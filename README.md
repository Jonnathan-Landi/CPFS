<p align="center">
  <b><i>
    <span style="font-size: 2.2em;">
      CPFS — Cuenca Precipitation Forecast System
    </span>
  </i></b>
</p>

<p align="center">
  <b>
    Probabilistic short-term precipitation forecasting system for the canton of Cuenca
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

The **Cuenca Precipitation Forecast System (CPFS)** is a modular and scalable framework designed to estimate the probability of rainfall occurrence over the canton of Cuenca at short-term horizons (1–6 hours). The system is motivated by the need for high-resolution, operationally relevant precipitation forecasts in complex mountainous environments, where global numerical models alone are insufficient to capture local-scale variability.

CPFS adopts a hybrid modeling paradigm that integrates:

- **Numerical Weather Prediction (NWP)** outputs, primarily from ECMWF, providing large-scale atmospheric conditions and forecasted variables.  
- **Satellite observations (GOES-19)**, enabling near real-time monitoring of cloud structure, evolution and convective development.  
- **In-situ hydrometeorological observations**, supplying ground truth data and local context for model calibration and validation.  

The central hypothesis of the system is that precipitation at short time scales can be better represented as a **probabilistic outcome conditioned on both forecasted atmospheric states and observed cloud dynamics**, rather than relying exclusively on deterministic model outputs.

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
