
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    ROOT / "artifacts" / "reports" / "scenarios"
    / "all_scenarios_summary.csv"
)

OUTPUT_FOLDER = (
    ROOT / "artifacts" / "reports" / "scenario_analysis"
)

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


def load_scenario_data():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Scenario summary not found: {INPUT_FILE}\n"
            "Run python -m scripts.run_scenarios first."
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "scenario",
        "status",
        "minimum_zone_pressure_m",
        "maximum_zone_pressure_m",
        "average_zone_pressure_m",
        "minimum_tank_level_m",
        "maximum_tank_level_m",
        "maximum_absolute_flow_m3s",
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing columns in scenario CSV: {missing}")

    df = df[df["status"] == "SUCCESS"].copy()

    if df.empty:
        raise ValueError("No successful scenario results were found.")

    numeric_columns = [
        "minimum_zone_pressure_m",
        "maximum_zone_pressure_m",
        "average_zone_pressure_m",
        "minimum_tank_level_m",
        "maximum_tank_level_m",
        "maximum_absolute_flow_m3s",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


def create_pressure_chart(df):
    plt.figure(figsize=(11, 6))

    plt.bar(
        df["scenario"],
        df["minimum_zone_pressure_m"]
    )

    plt.axhline(
        0,
        linestyle="--",
        label="Zero pressure reference"
    )

    plt.title("Minimum Zone Pressure Across Scenarios")
    plt.xlabel("Scenario")
    plt.ylabel("Minimum Pressure (m)")
    plt.xticks(rotation=30, ha="right")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        OUTPUT_FOLDER / "01_minimum_zone_pressure.png",
        dpi=300
    )

    plt.close()


def create_average_pressure_chart(df):
    plt.figure(figsize=(11, 6))

    plt.bar(
        df["scenario"],
        df["average_zone_pressure_m"]
    )

    plt.title("Average Zone Pressure Across Scenarios")
    plt.xlabel("Scenario")
    plt.ylabel("Average Pressure (m)")
    plt.xticks(rotation=30, ha="right")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        OUTPUT_FOLDER / "02_average_zone_pressure.png",
        dpi=300
    )

    plt.close()


def create_tank_level_chart(df):
    plt.figure(figsize=(11, 6))

    plt.plot(
        df["scenario"],
        df["minimum_tank_level_m"],
        marker="o",
        label="Minimum tank level"
    )

    plt.plot(
        df["scenario"],
        df["maximum_tank_level_m"],
        marker="s",
        label="Maximum tank level"
    )

    plt.title("Tank Water Level Across Scenarios")
    plt.xlabel("Scenario")
    plt.ylabel("Tank Water Level (m)")
    plt.xticks(rotation=30, ha="right")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        OUTPUT_FOLDER / "03_tank_level_comparison.png",
        dpi=300
    )

    plt.close()


def create_flow_chart(df):
    plt.figure(figsize=(11, 6))

    plt.bar(
        df["scenario"],
        df["maximum_absolute_flow_m3s"]
    )

    plt.title("Maximum Absolute Link Flow Across Scenarios")
    plt.xlabel("Scenario")
    plt.ylabel("Maximum Absolute Flow (m3/s)")
    plt.xticks(rotation=30, ha="right")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        OUTPUT_FOLDER / "04_maximum_flow_comparison.png",
        dpi=300
    )

    plt.close()


def create_comparison_report(df):
    normal_rows = df[df["scenario"] == "normal"]

    if normal_rows.empty:
        raise ValueError("Normal scenario is required for comparison.")

    normal_pressure = float(
        normal_rows.iloc[0]["average_zone_pressure_m"]
    )

    comparison = df.copy()

    comparison["average_pressure_change_m"] = (
        comparison["average_zone_pressure_m"] - normal_pressure
    ).round(3)

    comparison["pressure_condition"] = comparison[
        "minimum_zone_pressure_m"
    ].apply(
        lambda value:
            "Negative pressure observed"
            if value < 0
            else "Positive pressure in simulation"
    )

    comparison.to_csv(
        OUTPUT_FOLDER / "scenario_comparison.csv",
        index=False
    )

    # Identify the scenarios with the lowest pressure and tank level.
    lowest_pressure_row = comparison.loc[
        comparison["minimum_zone_pressure_m"].idxmin()
    ]

    lowest_tank_row = comparison.loc[
        comparison["minimum_tank_level_m"].idxmin()
    ]

    report = []

    report.append("URBANPULSE AI - SCENARIO ANALYSIS")
    report.append("=" * 55)
    report.append("")
    report.append("Dataset: Synthetic campus water demand")
    report.append("Network: Conceptual campus water network")
    report.append("Simulation: EPANET through WNTR")
    report.append("")
    report.append("KEY FINDINGS")
    report.append("-" * 40)

    report.append(
        f"Lowest minimum zone pressure: "
        f"{lowest_pressure_row['scenario']} "
        f"({lowest_pressure_row['minimum_zone_pressure_m']:.3f} m)"
    )

    report.append(
        f"Lowest tank level: "
        f"{lowest_tank_row['scenario']} "
        f"({lowest_tank_row['minimum_tank_level_m']:.3f} m)"
    )

    negative_scenarios = comparison[
        comparison["minimum_zone_pressure_m"] < 0
    ]["scenario"].tolist()

    if negative_scenarios:
        report.append(
            "Scenarios with negative simulated zone pressure: "
            + ", ".join(negative_scenarios)
        )
    else:
        report.append(
            "No scenario produced negative simulated zone pressure."
        )

    report.append("")
    report.append("SCENARIO COMPARISON")
    report.append("-" * 40)
    report.append(
        comparison[
            [
                "scenario",
                "minimum_zone_pressure_m",
                "average_zone_pressure_m",
                "minimum_tank_level_m",
                "average_pressure_change_m",
                "pressure_condition",
            ]
        ].to_string(index=False)
    )

    report.append("")
    report.append("MODELLING LIMITATIONS")
    report.append("-" * 40)
    report.append(
        "All results depend on assumed network parameters and synthetic data."
    )
    report.append(
        "Leakage and burst are represented as additional junction discharge."
    )
    report.append(
        "Pressure adequacy must be assessed against verified design criteria."
    )
    report.append(
        "This is a decision-support simulation, not a real pump-control system."
    )

    report_path = OUTPUT_FOLDER / "scenario_analysis_report.txt"

    report_path.write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print("\n".join(report))

    return comparison


def run_analysis():
    print("\n" + "=" * 55)
    print("       URBANPULSE AI - SCENARIO ANALYTICS")
    print("=" * 55)

    df = load_scenario_data()

    print(f"\nSuccessful scenarios loaded: {len(df)}")

    create_pressure_chart(df)
    print("1. Minimum pressure chart created.")

    create_average_pressure_chart(df)
    print("2. Average pressure chart created.")

    create_tank_level_chart(df)
    print("3. Tank level chart created.")

    create_flow_chart(df)
    print("4. Flow comparison chart created.")

    create_comparison_report(df)

    print("\nSCENARIO ANALYSIS COMPLETED!")
    print(f"Output folder: {OUTPUT_FOLDER}")


if __name__ == "__main__":
    run_analysis()
