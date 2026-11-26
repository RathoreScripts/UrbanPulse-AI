
from src.urbanpulse.data_generation import generate_and_save_data


def main():

    print("=" * 50)
    print("       URBANPULSE AI")
    print("   SYNTHETIC DATA GENERATOR")
    print("=" * 50)

    print("\nGenerating campus water demand data...")

    df, output_path = generate_and_save_data()

    print("\nDataset information:")
    print("-" * 35)

    print(f"Total records: {len(df)}")
    print(f"Total zones: {df['zone'].nunique()}")

    print("\nZone-wise records:")
    print(df.groupby("zone").size())

    print("\nFirst five records:")
    print(df.head())

    print("\nData generation completed!")


if __name__ == "__main__":
    main()
