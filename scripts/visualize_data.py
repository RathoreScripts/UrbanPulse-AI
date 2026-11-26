
import pandas as pd

from src.urbanpulse.config import get_project_path
from src.urbanpulse.visualizations import create_visualizations


def main():

    print("\n" + "=" * 55)
    print("             URBANPULSE AI")
    print("          DATA VISUALIZATION")
    print("=" * 55)

    # Load synthetic dataset
    file_path = get_project_path(
        "data/synthetic/campus_water_demand.csv"
    )

    print("\nLoading dataset...")

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    print("\nDataset loaded successfully!")

    print(f"Total records: {len(df)}")
    print(f"Total zones: {df['zone'].nunique()}")

    print("\nDataset preview:")

    print(df.head())

    # Generate visualizations
    create_visualizations(df)

    print("\nUrbanPulse AI visualization completed!")


if __name__ == "__main__":
    main()


