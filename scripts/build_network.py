
from src.urbanpulse.network import (
    build_network,
    get_network_summary
)

from src.urbanpulse.network_validation import (
    validate_network,
    print_network_report
)

from src.urbanpulse.network_visualizations import (
    save_network_map
)


def main():

    print("\n" + "=" * 60)
    print("              URBANPULSE AI")
    print("       VIRTUAL WATER NETWORK BUILDER")
    print("=" * 60)

    # 1. Build network
    print("\nBuilding virtual campus network...")

    graph, config = build_network()

    # 2. Display network summary
    summary = get_network_summary(graph, config)

    print("\nNETWORK SUMMARY")

    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    # 3. Validate network
    print("\nValidating network...")

    results = validate_network()

    print_network_report(results)

    if results["status"] != "PASS":
        print("\nNetwork validation failed.")
        print("Please check the configuration.")
        return

    # 4. Generate map
    print("\nGenerating 2D engineering map...")

    map_path = save_network_map()

    print("\n" + "=" * 60)
    print("URBANPULSE NETWORK BUILD COMPLETED!")
    print("=" * 60)

    print(f"\nOpen this file in your browser:\n{map_path}")


if __name__ == "__main__":
    main()
