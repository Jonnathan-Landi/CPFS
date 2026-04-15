<p align="center">
  <b><i>
    <span style="font-size: 2.2em;">
      CPFS — Cuenca Precipitation Forecast System
    </span>
  </i></b>
</p>

<p align="center">
  <b>
    RainForest Phase 1: Probabilistic short-term precipitation nowcasting for Ecuador
  </b>
</p>

---

## Table of Contents

1. [Introduction](#introduction)  
2. [System Overview](#system-overview-coming-soon)  
3. [Data Sources](#data-sources-coming-soon)  
4. [Modeling Approach](#modeling-approach-coming-soon)  
5. [Pipelines](#pipelines-coming-soon)  
6. [Models](#models-coming-soon)  
7. [Usage](#usage-coming-soon)  
8. [License](#license-coming-soon)  

---

## Introduction

The **RainForest** module is the Phase 1 nowcasting core of this repository. In this stage, the system is configured to run with a **satellite-only data strategy** for **Ecuador**, producing operational outputs for short horizons (1 h, 3 h and 6 h).

Phase 1 focuses on three products for each zone of interest:

- Rain probability.
- Expected precipitation intensity.
- Event type (`Sin lluvia`, `Lluvia debil`, `Lluvia moderada`, `Convectivo intenso`).

The operational domain boundary is defined by `assets/Ec/ecuador.shp` (EPSG:32717), and zones are spatially validated against that boundary before inference.

At this stage, **in-situ station data is not required** by the RainForest inference pipeline.

The central hypothesis of this first stage is that short-term precipitation behavior can be represented as a **probabilistic outcome driven by satellite-derived cloud and moisture signals**.

From a methodological perspective, CPFS formulates rainfall prediction as a **supervised probabilistic classification problem**, where the objective is to estimate:

where:

- `Y(t+h)` represents accumulated precipitation within a future horizon (e.g., 3 or 6 hours)  
- `τ` is a predefined rainfall threshold  
- `X(t)` corresponds to the set of predictors available at time `t`  

This formulation allows the system to produce calibrated outputs such as:

- Probability of rainfall occurrence  
- Probability of moderate rainfall  
- Probability of intense precipitation  

The system is structured to support progressive evolution, starting from baseline tabular models and extending towards multimodal architectures that incorporate both structured data and spatial satellite information.

In operational terms, CPFS is intended to support:

- Hydrometeorological monitoring  
- Early warning systems  
- Decision-making processes related to flood risk and urban drainage response  

---

## System Overview *(coming soon)*

---

## Data Sources *(coming soon)*

---

## Modeling Approach *(coming soon)*

---

## Pipelines *(coming soon)*

---

## Models *(coming soon)*

---

## Usage *(coming soon)*

### RainForest visual outputs

Each RainForest run now produces visual forecast products in addition to tabular outputs.

- Map by horizon for rain probability (1 h, 3 h, 6 h).
- Map by horizon for expected intensity.
- Map by horizon for event type (`Sin lluvia`, `Lluvia debil`, `Lluvia moderada`, `Convectivo intenso`).
- Animated GIF per variable showing horizon progression.

Spatial presentation uses:

- Ecuador boundary as national base (`assets/Ec/ecuador.shp`).
- Cuenca canton overlay (`assets/Canton/Cuenca.shp`) for local reference.
- Forecast zones from `zones/zones.geojson`.

Generated files are stored in `outputs/visuals/<run_id>/`, and the generated map/animation paths are written in `visual_products` inside each run JSON.

### ECMWF SSL / corporate proxy notes

If ECMWF download fails with `CERTIFICATE_VERIFY_FAILED`, configure one of these environment variables before running the ingest script:

- `CPFS_USE_SYSTEM_TRUST_STORE`: `true`/`false` to trust OS certificate store via `truststore` (default: `true`). Recommended in Windows corporate environments.
- `CPFS_CA_BUNDLE`: absolute path to your corporate CA certificate bundle (`.pem`/`.crt`).
- `REQUESTS_CA_BUNDLE` or `SSL_CERT_FILE`: standard Python/Requests CA bundle variables (also supported).
- `CPFS_ECMWF_VERIFY_SSL`: `true`/`false` toggle for SSL verification (default: `true`).
- `CPFS_ECMWF_AVAILABILITY_LAG_HOURS`: hours to subtract from current UTC to pick the latest available ECMWF cycle (default: `4`).

Recommended order:

1. Keep `CPFS_ECMWF_VERIFY_SSL=true`.
2. Use system trust store (default).
3. If your company CA is still not trusted, set `CPFS_CA_BUNDLE` to your exported corporate root/intermediate certificate.

Example in PowerShell:

```powershell
$env:CPFS_CA_BUNDLE = "C:\path\to\corp-ca.pem"
c:/GitHub/CPFS/.venv/Scripts/python.exe scripts/run_ingest_ecmwf.py
```

Temporary workaround (not recommended for production):

```powershell
$env:CPFS_ECMWF_VERIFY_SSL = "false"
c:/GitHub/CPFS/.venv/Scripts/python.exe scripts/run_ingest_ecmwf.py
```

Cycle selection example:

```powershell
$env:CPFS_ECMWF_AVAILABILITY_LAG_HOURS = "8"
c:/GitHub/CPFS/.venv/Scripts/python.exe scripts/run_ingest_ecmwf.py
```

---

## License *(coming soon)*
