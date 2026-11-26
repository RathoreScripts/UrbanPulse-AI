
from pathlib import Path

import yaml
import pandas as pd
import numpy as np
from scipy.optimize import linprog


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATH = PROJECT_ROOT / "config" / "optimization_config.yaml"

FORECAST_PATH = (
    PROJECT_ROOT / "artifacts" / "reports" /
    "forecasting" / "next_24_hour_forecast.csv"
)


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_forecast():
    if not FORECAST_PATH.exists():
        raise FileNotFoundError(f"Forecast file not found: {FORECAST_PATH}")

    df = pd.read_csv(FORECAST_PATH)

    required = ["timestamp", "zone", "predicted_demand_liters"]

    for column in required:
        if column not in df.columns:
            raise ValueError(f"Missing column: {column}")

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["zone"] = df["zone"].str.lower().str.strip()
    df["predicted_demand_liters"] = pd.to_numeric(
        df["predicted_demand_liters"], errors="raise"
    )

    if df[required].isnull().any().any():
        raise ValueError("Forecast contains missing values.")

    if (df["predicted_demand_liters"] < 0).any():
        raise ValueError("Negative demand found.")

    if df.duplicated(["timestamp", "zone"]).any():
        raise ValueError("Duplicate timestamp-zone records found.")

    return df


def optimize_single_hour(hourly_data, config):
    zones_config = config["optimization"]["zones"]
    zones = list(zones_config.keys())

    demand_map = dict(zip(
        hourly_data["zone"],
        hourly_data["predicted_demand_liters"]
    ))

    if set(demand_map) != set(zones):
        raise ValueError("Missing or unexpected zone in hourly forecast.")

    demand = np.array([float(demand_map[z]) for z in zones])

    supply = float(config["optimization"]["available_supply_liters"])

    priorities = np.array([
        float(zones_config[z]["priority"]) for z in zones
    ])

    minimum_percentages = np.array([
        float(zones_config[z]["minimum_allocation_percentage"])
        for z in zones
    ])

    if supply < 0:
        raise ValueError("Supply cannot be negative.")

    if (priorities <= 0).any():
        raise ValueError("Priority weights must be positive.")

    if ((minimum_percentages < 0) | (minimum_percentages > 1)).any():
        raise ValueError("Minimum percentages must be between 0 and 1.")

    minimum_allocation = demand * minimum_percentages

    if minimum_allocation.sum() > supply:
        raise ValueError(
            "Supply is insufficient for the configured minimum targets."
        )

    n = len(zones)

    # Variables: allocations followed by unmet demand.
    objective = np.concatenate([np.zeros(n), priorities])

    equality_matrix = np.hstack([np.eye(n), np.eye(n)])
    equality_rhs = demand

    supply_constraint = np.concatenate([
        np.ones(n), np.zeros(n)
    ]).reshape(1, -1)

    bounds = (
        [(minimum_allocation[i], demand[i]) for i in range(n)]
        + [(0, None) for _ in range(n)]
    )

    result = linprog(
        c=objective,
        A_ub=supply_constraint,
        b_ub=[supply],
        A_eq=equality_matrix,
        b_eq=equality_rhs,
        bounds=bounds,
        method="highs"
    )

    if not result.success:
        raise RuntimeError(f"Optimization failed: {result.message}")

    allocations = result.x[:n]
    shortages = result.x[n:]

    output = []

    for i, zone in enumerate(zones):
        output.append({
            "zone": zone,
            "predicted_demand_liters": round(demand[i], 2),
            "allocated_water_liters": round(allocations[i], 2),
            "unmet_demand_liters": round(shortages[i], 2),
            "priority_weight": priorities[i],
            "minimum_target_liters": round(minimum_allocation[i], 2),
            "allocation_percentage": round(
                allocations[i] / demand[i] * 100, 2
            ) if demand[i] > 0 else 100.0
        })

    return output


def run_optimization():
    print("\n" + "=" * 60)
    print("          URBANPULSE AI")
    print("       WATER ALLOCATION OPTIMIZATION")
    print("=" * 60)

    config = load_config()
    forecast_df = load_forecast()

    zones_config = config["optimization"]["zones"]
    expected_zones = set(zones_config.keys())
    actual_zones = set(forecast_df["zone"].unique())

    if expected_zones != actual_zones:
        raise ValueError(
            f"Zone mismatch. Expected {expected_zones}, found {actual_zones}"
        )

    output_dir = (
        PROJECT_ROOT / config["optimization"]["output"]["directory"]
    )

    # Prevent a file from blocking directory creation.
    if output_dir.exists() and not output_dir.is_dir():
        raise NotADirectoryError(
            f"Output path exists as a file: {output_dir}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    all_results = []
    timestamps = sorted(forecast_df["timestamp"].unique())

    print(f"\nForecast records: {len(forecast_df)}")
    print(f"Zones: {len(expected_zones)}")
    print(f"Hours to optimize: {len(timestamps)}")

    for timestamp in timestamps:
        hourly_data = forecast_df[
            forecast_df["timestamp"] == timestamp
        ]

        hourly_results = optimize_single_hour(hourly_data, config)

        for row in hourly_results:
            row["timestamp"] = timestamp
            all_results.append(row)

    results_df = pd.DataFrame(all_results)

    results_df = results_df[
        [
            "timestamp",
            "zone",
            "predicted_demand_liters",
            "allocated_water_liters",
            "unmet_demand_liters",
            "priority_weight",
            "minimum_target_liters",
            "allocation_percentage"
        ]
    ]

    results_df.to_csv(
        output_dir / "hourly_water_allocation.csv",
        index=False
    )

    zone_summary = (
        results_df.groupby("zone", as_index=False)
        .agg({
            "predicted_demand_liters": "sum",
            "allocated_water_liters": "sum",
            "unmet_demand_liters": "sum",
            "minimum_target_liters": "sum"
        })
    )

    zone_summary["allocation_percentage"] = (
        zone_summary["allocated_water_liters"]
        / zone_summary["predicted_demand_liters"].replace(0, np.nan)
        * 100
    ).fillna(100).round(2)

    zone_summary.to_csv(
        output_dir / "zone_allocation_summary.csv",
        index=False
    )

    hourly_totals = (
        results_df.groupby("timestamp", as_index=False)
        .agg({
            "predicted_demand_liters": "sum",
            "allocated_water_liters": "sum",
            "unmet_demand_liters": "sum"
        })
    )

    hourly_totals.to_csv(
        output_dir / "hourly_allocation_totals.csv",
        index=False
    )

    total_demand = results_df["predicted_demand_liters"].sum()
    total_allocated = results_df["allocated_water_liters"].sum()
    total_shortage = results_df["unmet_demand_liters"].sum()

    total_supply = (
        float(config["optimization"]["available_supply_liters"])
        * len(timestamps)
    )

    shortage_percentage = (
        total_shortage / total_demand * 100
        if total_demand > 0 else 0
    )

    report = [
        "URBANPULSE AI - WATER OPTIMIZATION REPORT",
        "=" * 55,
        "",
        "Dataset: Synthetic AI demand forecast",
        "Method: Linear Programming using SciPy HiGHS",
        f"Hours optimized: {len(timestamps)}",
        f"Zones: {len(expected_zones)}",
        f"Total predicted demand: {total_demand:.2f} litres",
        f"Total available supply: {total_supply:.2f} litres",
        f"Total allocated water: {total_allocated:.2f} litres",
        f"Total unmet demand: {total_shortage:.2f} litres",
        f"Overall shortage: {shortage_percentage:.2f}%",
        "",
        "ZONE-WISE SUMMARY",
        zone_summary.to_string(index=False),
        "",
        "Supply and minimum allocation targets are project assumptions.",
        "Results are recommendations based on synthetic forecast data."
    ]

    (output_dir / "optimization_report.txt").write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print("\nZONE-WISE WATER ALLOCATION")
    print(zone_summary.round(2).to_string(index=False))

    print("\nOVERALL SUMMARY")
    print(f"Total predicted demand: {total_demand:.2f} L")
    print(f"Total allocated water: {total_allocated:.2f} L")
    print(f"Total unmet demand: {total_shortage:.2f} L")
    print(f"Overall shortage: {shortage_percentage:.2f}%")

    print("\nOPTIMIZATION COMPLETED SUCCESSFULLY")
    print(f"\nOutput folder: {output_dir}")


if __name__ == "__main__":
    run_optimization()
