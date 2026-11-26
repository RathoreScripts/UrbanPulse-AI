
import pandas as pd

from src.urbanpulse.config import load_config, get_project_path


REQUIRED_COLUMNS = [
    "timestamp",
    "zone",
    "demand_liters"
]


def validate_dataset(df):
    """
    Validate the synthetic campus water demand dataset.
    Returns a dictionary containing validation results.
    """

    config = load_config()
    expected_zones = set(config["zones"].keys())
    expected_days = config["simulation"]["days"]

    results = {}

    # 1. Check required columns
    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    results["missing_columns"] = missing_columns

    if missing_columns:
        return results

    # 2. Check missing values
    results["missing_values"] = (
        df[REQUIRED_COLUMNS].isnull().sum().to_dict()
    )

    # 3. Check duplicate records
    results["duplicate_rows"] = int(
        df.duplicated().sum()
    )

    results["duplicate_timestamp_zone"] = int(
        df.duplicated(
            subset=["timestamp", "zone"]
        ).sum()
    )

    # 4. Check negative water demand
    results["negative_demand"] = int(
        (df["demand_liters"] < 0).sum()
    )

    # 5. Check unknown zones
    actual_zones = set(df["zone"].dropna().unique())

    results["unknown_zones"] = sorted(
        actual_zones - expected_zones
    )

    results["missing_zones"] = sorted(
        expected_zones - actual_zones
    )

    # 6. Check timestamp validity
    timestamps = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    results["invalid_timestamps"] = int(
        timestamps.isna().sum()
    )

    valid_timestamps = timestamps.dropna()

    if not valid_timestamps.empty:

        results["start_date"] = str(
            valid_timestamps.min()
        )

        results["end_date"] = str(
            valid_timestamps.max()
        )

        results["total_unique_timestamps"] = int(
            valid_timestamps.nunique()
        )

    else:
        results["start_date"] = None
        results["end_date"] = None
        results["total_unique_timestamps"] = 0

    # 7. Check expected number of records
    expected_records = expected_days * 24 * len(expected_zones)

    results["expected_records"] = expected_records
    results["actual_records"] = len(df)

    results["record_count_correct"] = (
        len(df) == expected_records
    )

    # 8. Check demand values are numeric
    numeric_demand = pd.to_numeric(
        df["demand_liters"],
        errors="coerce"
    )

    results["non_numeric_demand"] = int(
        numeric_demand.isna().sum()
    )

    # 9. Check hourly continuity
    if not valid_timestamps.empty:

        unique_times = pd.Series(
            valid_timestamps.unique()
        ).sort_values()

        differences = unique_times.diff().dropna()

        results["non_hourly_intervals"] = int(
            (differences != pd.Timedelta(hours=1)).sum()
        )

    else:
        results["non_hourly_intervals"] = None

    # 10. Check one record per zone per timestamp
    results["records_per_zone"] = (
        df.groupby("zone").size().to_dict()
    )

    # Determine overall validation status
    missing_value_count = sum(
        results["missing_values"].values()
    )

    passed = (
        not missing_columns
        and missing_value_count == 0
        and results["duplicate_rows"] == 0
        and results["duplicate_timestamp_zone"] == 0
        and results["negative_demand"] == 0
        and not results["unknown_zones"]
        and not results["missing_zones"]
        and results["invalid_timestamps"] == 0
        and results["non_numeric_demand"] == 0
        and results["record_count_correct"]
        and results["non_hourly_intervals"] == 0
        and all(
            count == expected_days * 24
            for count in results["records_per_zone"].values()
        )
        and len(results["records_per_zone"]) == len(expected_zones)
    )

    results["overall_status"] = (
        "PASS" if passed else "CHECK REQUIRED"
    )

    return results


def print_validation_report(results):
    """Print a readable validation report."""

    print("\n" + "=" * 55)
    print("       URBANPULSE AI - DATA VALIDATION")
    print("=" * 55)

    for key, value in results.items():

        if isinstance(value, dict):
            print(f"\n{key.replace('_', ' ').title()}:")

            for name, count in value.items():
                print(f"  {name}: {count}")

        else:
            print(
                f"{key.replace('_', ' ').title()}: {value}"
            )

    print("\n" + "=" * 55)
    print("OVERALL STATUS:", results.get("overall_status", "ERROR"))
    print("=" * 55)


def run_validation():
    """Load the CSV and run all validation checks."""

    input_path = get_project_path(
        "data/synthetic/campus_water_demand.csv"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {input_path}"
        )

    df = pd.read_csv(input_path)

    results = validate_dataset(df)

    print_validation_report(results)

    # Save validation report
    report_path = get_project_path(
        "artifacts/reports/data_validation_report.txt"
    )

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(report_path, "w", encoding="utf-8") as file:
        for key, value in results.items():
            file.write(f"{key}: {value}\n")

    print(f"\nReport saved at: {report_path}")

    return results


if __name__ == "__main__":
    run_validation()
