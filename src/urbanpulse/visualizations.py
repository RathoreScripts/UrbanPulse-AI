
import pandas as pd
import matplotlib.pyplot as plt

from src.urbanpulse.config import get_project_path


def create_visualizations(df):

    print("\nStarting UrbanPulse AI Visualization...")

    # Create output directory
    output_dir = get_project_path(
        "artifacts/reports/plots"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # Prepare dataset
    df = df.copy()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    df["demand_liters"] = pd.to_numeric(
        df["demand_liters"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["timestamp", "zone", "demand_liters"]
    )

    # ==========================================
    # GRAPH 1: AVERAGE WATER DEMAND BY ZONE
    # ==========================================

    print("\nGenerating Graph 1...")

    zone_average = df.groupby(
        "zone"
    )["demand_liters"].mean()

    fig, ax = plt.subplots(figsize=(10, 6))

    zone_average.plot(
        kind="bar",
        ax=ax
    )

    ax.set_title(
        "Average Water Demand by Campus Zone",
        fontsize=14
    )

    ax.set_xlabel("Campus Zone")
    ax.set_ylabel("Average Demand (Litres/Hour)")

    ax.tick_params(axis="x", rotation=30)

    fig.tight_layout()

    fig.savefig(
        output_dir / "01_zone_average_demand.png",
        dpi=300
    )

    plt.close(fig)

    # ==========================================
    # GRAPH 2: HOURLY WATER DEMAND PATTERN
    # ==========================================

    print("Generating Graph 2...")

    df["hour"] = df["timestamp"].dt.hour

    hourly_average = df.groupby(
        ["hour", "zone"]
    )["demand_liters"].mean().unstack()

    fig, ax = plt.subplots(figsize=(12, 6))

    hourly_average.plot(
        ax=ax,
        marker="o",
        markersize=3
    )

    ax.set_title(
        "Hourly Water Demand Pattern",
        fontsize=14
    )

    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Average Demand (Litres/Hour)")

    ax.set_xticks(range(24))
    ax.legend(title="Campus Zone")

    ax.grid(alpha=0.3)

    fig.tight_layout()

    fig.savefig(
        output_dir / "02_hourly_demand_pattern.png",
        dpi=300
    )

    plt.close(fig)

    # ==========================================
    # GRAPH 3: DAILY WATER CONSUMPTION
    # ==========================================

    print("Generating Graph 3...")

    df["date"] = df["timestamp"].dt.date

    daily_demand = df.groupby(
        ["date", "zone"]
    )["demand_liters"].sum().unstack()

    fig, ax = plt.subplots(figsize=(14, 6))

    daily_demand.plot(
        ax=ax
    )

    ax.set_title(
        "Daily Water Consumption by Campus Zone",
        fontsize=14
    )

    ax.set_xlabel("Date")
    ax.set_ylabel("Total Demand (Litres/Day)")

    ax.legend(title="Campus Zone")
    ax.grid(alpha=0.3)

    fig.tight_layout()

    fig.savefig(
        output_dir / "03_daily_water_consumption.png",
        dpi=300
    )

    plt.close(fig)

    # ==========================================
    # GRAPH 4: TOTAL WATER DEMAND DISTRIBUTION
    # ==========================================

    print("Generating Graph 4...")

    zone_total = df.groupby(
        "zone"
    )["demand_liters"].sum()

    fig, ax = plt.subplots(figsize=(9, 7))

    zone_total.plot(
        kind="pie",
        autopct="%1.1f%%",
        startangle=90,
        ax=ax
    )

    ax.set_title(
        "Total Water Demand Distribution by Zone",
        fontsize=14
    )

    ax.set_ylabel("")

    fig.tight_layout()

    fig.savefig(
        output_dir / "04_zone_demand_distribution.png",
        dpi=300
    )

    plt.close(fig)

    # ==========================================
    # FINAL SUMMARY
    # ==========================================

    print("\n" + "=" * 55)
    print("ALL FOUR GRAPHS GENERATED SUCCESSFULLY!")
    print("=" * 55)

    print("\nGenerated files:")

    print("1. 01_zone_average_demand.png")
    print("2. 02_hourly_demand_pattern.png")
    print("3. 03_daily_water_consumption.png")
    print("4. 04_zone_demand_distribution.png")

    print(f"\nSaved location: {output_dir}")

    return output_dir

