
"""
UrbanPulse AI - Dashboard Data Loader

Loads existing datasets, forecasting outputs, hydraulic
simulation results, scenario comparisons and optimization reports.

This module does not generate synthetic data or retrain models.
It reads the existing project files only.
"""

from pathlib import Path

import pandas as pd


# ============================================================
# 1. PROJECT PATH CONFIGURATION
# ============================================================

# dashboard/data_loader.py
#       |
#       └── Project root = Urbanplus/

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
MODEL_DIR = PROJECT_ROOT / "models"
REPORT_DIR = PROJECT_ROOT / "artifacts" / "reports"

DEMAND_FILE = (
    DATA_DIR / "synthetic" / "campus_water_demand.csv"
)

FORECAST_DIR = REPORT_DIR / "forecasting"
HYDRAULIC_DIR = REPORT_DIR / "hydraulic"
SCENARIO_DIR = REPORT_DIR / "scenario_analysis"
OPTIMIZATION_DIR = REPORT_DIR / "optimization"


# ============================================================
# 2. COMMON CSV LOADING FUNCTION
# ============================================================

def load_csv(file_path):
    """
    Read a CSV file and return a pandas DataFrame.

    Parameters
    ----------
    file_path : pathlib.Path
        Location of the CSV file.

    Returns
    -------
    pandas.DataFrame
        Loaded CSV data.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required project file not found: {file_path}"
        )

    try:
        return pd.read_csv(file_path)

    except Exception as error:
        raise RuntimeError(
            f"Could not read file: {file_path}\n"
            f"Reason: {error}"
        ) from error


# ============================================================
# 3. HISTORICAL WATER DEMAND
# ============================================================

def load_demand_data():
    """
    Load historical campus water demand.

    Expected columns:
    timestamp, zone, demand_liters
    """

    df = load_csv(DEMAND_FILE)

    required_columns = [
        "timestamp",
        "zone",
        "demand_liters"
    ]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(
                f"Missing column '{column}' in historical demand data."
            )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df["demand_liters"] = pd.to_numeric(
        df["demand_liters"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["timestamp", "zone", "demand_liters"]
    )

    return df.sort_values("timestamp").reset_index(drop=True)


# ============================================================
# 4. AI FORECASTING RESULTS
# ============================================================

def load_forecast_data():
    """
    Load the next 24-hour zone-wise demand forecast.

    Expected columns:
    timestamp, zone, predicted_demand_liters, selected_model
    """

    file_path = FORECAST_DIR / "next_24_hour_forecast.csv"

    df = load_csv(file_path)

    required_columns = [
        "timestamp",
        "zone",
        "predicted_demand_liters"
    ]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(
                f"Missing column '{column}' in forecast data."
            )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df["predicted_demand_liters"] = pd.to_numeric(
        df["predicted_demand_liters"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["timestamp", "zone", "predicted_demand_liters"]
    )

    return df.sort_values(
        ["timestamp", "zone"]
    ).reset_index(drop=True)


def load_campus_forecast():
    """
    Load the total campus demand forecast.

    Expected columns:
    timestamp, predicted_demand_liters
    """

    file_path = FORECAST_DIR / "campus_total_forecast.csv"

    df = load_csv(file_path)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df["predicted_demand_liters"] = pd.to_numeric(
        df["predicted_demand_liters"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["timestamp", "predicted_demand_liters"]
    )

    return df.sort_values("timestamp").reset_index(drop=True)


def load_model_comparison():
    """
    Load the saved model comparison metrics.
    """

    file_path = FORECAST_DIR / "model_comparison_metrics.csv"

    return load_csv(file_path)


def load_best_models():
    """
    Load the selected model information from JSON.
    """

    import json

    file_path = FORECAST_DIR / "best_models.json"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Best-model report not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# 5. HYDRAULIC SIMULATION RESULTS
# ============================================================

def load_node_pressure():
    """
    Load hydraulic node pressure results.

    The simulation uses time_hours as its time axis.
    Pressure columns represent network nodes.
    """

    file_path = HYDRAULIC_DIR / "node_pressure.csv"

    df = load_csv(file_path)

    if "time_hours" not in df.columns:
        raise ValueError(
            "time_hours column missing from node_pressure.csv"
        )

    df["time_hours"] = pd.to_numeric(
        df["time_hours"],
        errors="coerce"
    )

    return df.sort_values("time_hours").reset_index(drop=True)


def load_node_head():
    """Load hydraulic node head results."""

    file_path = HYDRAULIC_DIR / "node_head.csv"

    return load_csv(file_path)


def load_node_demand():
    """Load hydraulic node demand results."""

    file_path = HYDRAULIC_DIR / "node_demand.csv"

    return load_csv(file_path)


def load_tank_level():
    """
    Load overhead tank water-level simulation results.
    """

    file_path = HYDRAULIC_DIR / "tank_level.csv"

    df = load_csv(file_path)

    if "time_hours" not in df.columns:
        raise ValueError(
            "time_hours column missing from tank_level.csv"
        )

    df["time_hours"] = pd.to_numeric(
        df["time_hours"],
        errors="coerce"
    )

    return df.sort_values("time_hours").reset_index(drop=True)


def load_pipe_flowrate():
    """Load simulated pipe flow rates."""

    file_path = HYDRAULIC_DIR / "pipe_flowrate.csv"

    return load_csv(file_path)


def load_pipe_velocity():
    """Load simulated pipe velocities."""

    file_path = HYDRAULIC_DIR / "pipe_velocity.csv"

    return load_csv(file_path)


def load_link_status():
    """Load simulated hydraulic link status."""

    file_path = HYDRAULIC_DIR / "link_status.csv"

    return load_csv(file_path)


# ============================================================
# 6. SCENARIO ANALYSIS
# ============================================================

def load_scenario_comparison():
    """
    Load the comparison results for all hydraulic scenarios.

    Includes:
    - Minimum and maximum zone pressure
    - Average zone pressure
    - Minimum and maximum tank level
    - Maximum absolute flow
    - Pressure condition
    """

    file_path = (
        SCENARIO_DIR / "scenario_comparison.csv"
    )

    return load_csv(file_path)


def load_all_scenarios_summary():
    """
    Load the scenario summary generated by the project.
    """

    file_path = (
        REPORT_DIR / "scenarios" / "all_scenarios_summary.csv"
    )

    return load_csv(file_path)


# ============================================================
# 7. WATER ALLOCATION OPTIMIZATION
# ============================================================

def load_zone_allocation():
    """
    Load zone-wise optimized water allocation.

    Expected columns:
    zone,
    predicted_demand_liters,
    allocated_water_liters,
    unmet_demand_liters,
    minimum_target_liters,
    allocation_percentage
    """

    file_path = (
        OPTIMIZATION_DIR / "zone_allocation_summary.csv"
    )

    df = load_csv(file_path)

    numeric_columns = [
        "predicted_demand_liters",
        "allocated_water_liters",
        "unmet_demand_liters",
        "minimum_target_liters",
        "allocation_percentage"
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


def load_hourly_allocation():
    """
    Load hourly optimized water allocation.
    """

    file_path = (
        OPTIMIZATION_DIR / "hourly_water_allocation.csv"
    )

    return load_csv(file_path)


def load_hourly_allocation_totals():
    """
    Load hourly total water allocation.
    """

    file_path = (
        OPTIMIZATION_DIR / "hourly_allocation_totals.csv"
    )

    return load_csv(file_path)


# ============================================================
# 8. PROJECT INFORMATION
# ============================================================

ZONES = [
    "hostel",
    "academic",
    "canteen",
    "medical",
    "sports"
]


def get_project_summary():
    """
    Return basic information calculated from the actual
    historical dataset.
    """

    df = load_demand_data()

    return {
        "total_records": len(df),

        "total_zones": df["zone"].nunique(),

        "zones": sorted(df["zone"].unique().tolist()),

        "start_date": df["timestamp"].min(),

        "end_date": df["timestamp"].max(),

        "total_demand_liters": df["demand_liters"].sum(),

        "average_hourly_demand_liters": (
            df.groupby("timestamp")["demand_liters"]
            .sum()
            .mean()
        )
    }
