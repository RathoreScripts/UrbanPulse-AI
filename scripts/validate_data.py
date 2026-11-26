
from src.urbanpulse.data_validation import run_validation


def main():
    print("Starting UrbanPulse AI data validation...")

    results = run_validation()

    if results.get("overall_status") == "PASS":
        print("\nGreat! Your dataset passed all validation checks.")
    else:
        print("\nSome checks need attention. Review the report.")


if __name__ == "__main__":
    main()
