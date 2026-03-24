from cpfs.orchestration.prepare_ecmwf_pipeline import run_prepare_ecmwf


if __name__ == "__main__":
    out = run_prepare_ecmwf(
        steps=list(range(0, 25, 3)),
        variables=["tp", "t2m", "u10", "v10", "cape"],
        roi_path="assets/roi/cuenca_forecast_roi/cuenca_forecast_roi.shp",
        roi_layer="cuenca_forecast_roi",
    )

    print(f"Producto listo para uso en: {out}")