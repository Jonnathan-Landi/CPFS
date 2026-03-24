# src/cpfs/ingest/ecmwf/download.py

from datetime import datetime, timedelta
from pathlib import Path
from requests import HTTPError
from requests.exceptions import SSLError as RequestsSSLError

from .client import get_ecmwf_client


ECMWF_PARAM_ALIASES = {
    "t2m": "2t",
    "u10": "10u",
    "v10": "10v",
    "cape": "mucape",
}


def normalize_ecmwf_variables(variables: list[str]) -> list[str]:
    normalized = []
    for variable in variables:
        key = variable.strip().lower()
        normalized.append(ECMWF_PARAM_ALIASES.get(key, key))

    seen = set()
    deduplicated = []
    for variable in normalized:
        if variable not in seen:
            deduplicated.append(variable)
            seen.add(variable)

    return deduplicated


def build_target_path(base_dir, date, time):
    folder = Path(base_dir) / date
    folder.mkdir(parents=True, exist_ok=True)

    filename = f"ecmwf_{date}_{time}.grib2"
    return folder / filename


def previous_ecmwf_cycle(date: str, time: str) -> tuple[str, str]:
    run_dt = datetime.strptime(f"{date}{time}", "%Y%m%d%H")
    prev_dt = run_dt.replace(minute=0, second=0, microsecond=0) - timedelta(hours=6)
    return prev_dt.strftime("%Y%m%d"), prev_dt.strftime("%H")


def download_ecmwf_forecast(
    date=None,
    time="00",
    steps=None,
    variables=None,
    base_dir="data/raw/ecmwf",
    max_cycle_fallbacks: int = 3,
):
    """
    Descarga pronóstico ECMWF (Open Data)

    Parámetros:
    ----------
    date : str (YYYYMMDD)
    time : str ("00", "06", "12", "18")
    steps : list[int]
    variables : list[str]
    """

    if date is None:
        date = datetime.utcnow().strftime("%Y%m%d")

    if steps is None:
        steps = [0, 3, 6, 9, 12]

    if variables is None:
        variables = ["tp", "t2m", "u10", "v10", "cape"]

    requested_variables = list(variables)
    variables = normalize_ecmwf_variables(variables)

    client = get_ecmwf_client()
    if requested_variables != variables:
        print(f"[INFO] Variables traducidas ECMWF: {requested_variables} -> {variables}")

    candidate_date = date
    candidate_time = time

    for attempt in range(max_cycle_fallbacks + 1):
        target_path = build_target_path(base_dir, candidate_date, candidate_time)
        if target_path.exists():
            print(f"[INFO] Archivo ya existe: {target_path}")
            return target_path

        print(f"[INFO] Descargando ECMWF: date={candidate_date}, time={candidate_time}")

        try:
            client.retrieve(
                date=candidate_date,
                time=candidate_time,
                step=steps,
                stream="oper",
                type="fc",
                param=variables,
                target=str(target_path),
            )
            print(f"[OK] Guardado en: {target_path}")
            return target_path
        except RequestsSSLError as exc:
            raise RuntimeError(
                "Fallo SSL al conectar con ECMWF Open Data. "
                "Configura un certificado CA confiable con CPFS_CA_BUNDLE "
                "(o REQUESTS_CA_BUNDLE/SSL_CERT_FILE) y vuelve a ejecutar. "
                "Como workaround temporal no recomendado, usa "
                "CPFS_ECMWF_VERIFY_SSL=false."
            ) from exc
        except HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code != 404 or attempt == max_cycle_fallbacks:
                raise

            prev_date, prev_time = previous_ecmwf_cycle(candidate_date, candidate_time)
            print(
                "[WARN] Corrida no disponible aún "
                f"({candidate_date} {candidate_time} UTC). "
                f"Fallback a {prev_date} {prev_time} UTC"
            )
            candidate_date, candidate_time = prev_date, prev_time

    raise RuntimeError("No se pudo descargar ECMWF tras aplicar fallbacks")