from __future__ import annotations

import sys
from pathlib import Path

# Ensure package imports work from the repository root.
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rainforest.run_nowcast import main


if __name__ == "__main__":
    main()
