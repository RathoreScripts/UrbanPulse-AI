
from pathlib import Path
import yaml

# Find the main project folder
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Configuration file location
CONFIG_PATH = PROJECT_ROOT / "config" / "project_config.yaml"


def load_config():
    """Read project settings from the YAML file."""

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {CONFIG_PATH}"
        )

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return config


def get_project_path(relative_path):
    """Convert a project-relative path into a full path."""

    return PROJECT_ROOT / relative_path
