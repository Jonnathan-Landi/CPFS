from __future__ import annotations

import argparse

from .config import load_config
from .pipeline import execute_nowcast
from .products import summarize_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RainForest nowcasting pipeline")
    parser.add_argument("--config", default="rainforest_config.json", help="Path to config file")
    parser.add_argument("--force", action="store_true", help="Force run even if source timestamp is unchanged")
    args = parser.parse_args()

    config = load_config(args.config)
    result = execute_nowcast(config=config, force=args.force)

    print(f"run_id={result.run_id}")
    print(f"status={result.status}")
    if result.warnings:
        print("warnings:")
        for item in result.warnings:
            print(f"- {item}")
    print(summarize_rows(result.rows))


if __name__ == "__main__":
    main()
