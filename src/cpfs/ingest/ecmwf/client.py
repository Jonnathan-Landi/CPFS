import os

from ecmwf.opendata import Client


def _parse_bool_env(value: str | None, default: bool) -> bool:
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    return default


def _enable_system_trust_store() -> None:
    use_system_store = _parse_bool_env(
        os.getenv("CPFS_USE_SYSTEM_TRUST_STORE"),
        default=True,
    )
    if not use_system_store:
        return

    try:
        import truststore

        truststore.inject_into_ssl()
    except Exception:
        return


def _parse_verify_env():
    verify_value = os.getenv("CPFS_ECMWF_VERIFY_SSL")
    ca_bundle = (
        os.getenv("CPFS_CA_BUNDLE")
        or os.getenv("REQUESTS_CA_BUNDLE")
        or os.getenv("SSL_CERT_FILE")
    )

    if ca_bundle:
        return ca_bundle

    if verify_value is None:
        return True

    return _parse_bool_env(verify_value, default=True)


def get_ecmwf_client():
    _enable_system_trust_store()
    verify = _parse_verify_env()
    return Client(source="ecmwf", verify=verify)