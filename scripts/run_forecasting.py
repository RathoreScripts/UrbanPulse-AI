
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from urbanpulse.forecasting import run_forecasting


if __name__ == "__main__":
    run_forecasting()
