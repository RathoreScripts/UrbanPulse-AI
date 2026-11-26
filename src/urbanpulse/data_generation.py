
import numpy as np
import pandas as pd

from src.urbanpulse.config import load_config, get_project_path


def generate_hourly_demand(days=None):
    """
    Generate synthetic hourly water demand
    for five conceptual campus zones.

    Demand is measured in litres per hour.
    This is synthetic data, not real campus data.
    """

    config = load_config()

    if days is None:
        days = config["simulation"]["days"]

    seed = config["simulation"]["random_seed"]
    rng = np.random.default_rng(seed)

    # Create hourly timestamps
    timestamps = pd.date_range(
        start="2026-01-01 00:00:00",
        periods=days * 24,
        freq="h"
    )

    # Average demand assumptions in litres per second
    zones = config["zones"]

    zone_demands_lps = {
        zone: details["average_demand_lps"]
        for zone, details in zones.items()
    }

    # Convert litres/second to litres/hour
    zone_demands_lph = {
        zone: demand * 3600
        for zone, demand in zone_demands_lps.items()
    }

    # Hourly demand pattern
    hourly_pattern = np.array([
        0.35, 0.30, 0.28, 0.27, 0.30, 0.45,
        0.75, 1.20, 1.35, 1.20, 1.05, 1.00,
        1.05, 1.00, 0.95, 0.90, 0.95, 1.10,
        1.30, 1.40, 1.25, 1.00, 0.70, 0.50
    ])

    records = []

    for timestamp in timestamps:

        hour = timestamp.hour
        weekday = timestamp.weekday()

        for zone, average_lph in zone_demands_lph.items():

            demand_factor = hourly_pattern[hour]

            # Academic activity is lower on weekends
            if zone == "academic" and weekday >= 5:
                demand_factor *= 0.35

            # Canteen demand changes with meal hours
            if zone == "canteen":
                if hour in [7, 8, 13, 14, 19, 20]:
                    demand_factor *= 1.35

            # Small random variation
            noise = rng.normal(loc=1.0, scale=0.08)

            # Final hourly demand
            demand_liters = average_lph * demand_factor * noise

            # Avoid negative values
            demand_liters = max(0, demand_liters)

            records.append({
                "timestamp": timestamp,
                "zone": zone,
                "demand_liters": round(demand_liters, 2)
            })

    # Convert records into a DataFrame
    df = pd.DataFrame(records)

    return df


def save_synthetic_data(df):
    """Save synthetic water demand data as a CSV file."""

    config = load_config()

    output_path = get_project_path(
        config["output"]["synthetic_data"]
    )

    # Create output folder if it does not exist
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(output_path, index=False)

    print("\nSynthetic dataset saved successfully!")
    print(f"File location: {output_path}")

    return output_path


def generate_and_save_data():
    """Generate and save the complete synthetic dataset."""

    df = generate_hourly_demand()

    output_path = save_synthetic_data(df)

    return df, output_path
