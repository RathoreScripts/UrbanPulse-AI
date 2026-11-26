import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from urbanpulse.scenario_analysis import run_analysis


if __name__ == "__main__":
    run_analysis()