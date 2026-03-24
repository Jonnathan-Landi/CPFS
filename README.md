# CPFS — Cuenca Precipitation Forecast System

---

<p align="center">
  <strong>Probabilistic Short-Term Rainfall Forecasting System for Cuenca</strong><br>
  Integrating Numerical Weather Prediction, Satellite Observations and In-situ Data
</p>

---

## Table of Contents

1. Introduction
2. System Overview *(coming soon)*
3. Data Sources *(coming soon)*
4. Modeling Approach *(coming soon)*
5. Pipelines *(coming soon)*
6. Models *(coming soon)*
7. Usage *(coming soon)*
8. License *(coming soon)*

---

## 1. Introduction

The **Cuenca Precipitation Forecast System (CPFS)** is a modular and scalable framework designed to estimate the probability of rainfall occurrence over the canton of Cuenca at short-term horizons (1–6 hours). The system is motivated by the need for high-resolution, operationally relevant precipitation forecasts in complex mountainous environments, where global numerical models alone are insufficient to capture local-scale variability.

CPFS adopts a hybrid modeling paradigm that integrates:

* **Numerical Weather Prediction (NWP)** outputs, primarily from ECMWF, providing large-scale atmospheric conditions and forecasted variables.
* **Satellite observations (GOES-19)**, enabling near real-time monitoring of cloud structure, evolution and convective development.
* **In-situ hydrometeorological observations**, supplying ground truth data and local context for model calibration and validation.

The central hypothesis of the system is that precipitation at short time scales can be better represented as a **probabilistic outcome conditioned on both forecasted atmospheric states and observed cloud dynamics**, rather than relying exclusively on deterministic model outputs.

From a methodological perspective, CPFS formulates rainfall prediction as a **supervised probabilistic classification problem**, where the objective is to estimate:

[
P(Y_{t+h} \geq \tau \mid X_t)
]

where:

* ( Y_{t+h} ) represents accumulated precipitation within a future horizon ( h ) (e.g., 3 or 6 hours),
* ( \tau ) is a predefined rainfall threshold,
* ( X_t ) corresponds to the set of predictors available at time ( t ).

This formulation allows the system to produce calibrated outputs such as:

* Probability of rainfall occurrence
* Probability of moderate rainfall
* Probability of intense precipitation

The system is structured to support progressive evolution, starting from baseline tabular models and extending towards multimodal architectures that incorporate both structured data and spatial satellite information.

In operational terms, CPFS is intended to support:

* Hydrometeorological monitoring
* Early warning systems
* Decision-making processes related to flood risk and urban drainage response

The project emphasizes reproducibility, modularity and extensibility, ensuring that new data sources, modeling strategies and prediction targets can be incorporated without restructuring the core system.

---
