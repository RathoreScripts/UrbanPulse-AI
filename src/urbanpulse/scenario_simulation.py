from pathlib import Path
import pandas as pd
import wntr

from wntr.network.base import LinkStatus


# ============================================================
# URBANPULSE AI - SCENARIO SIMULATION ENGINE
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

HYDRAULIC_FOLDER = ROOT / "artifacts" / "reports" / "hydraulic"
OUTPUT_FOLDER = ROOT / "artifacts" / "reports" / "scenarios"

ZONE_NODES = ["Z1", "Z2", "Z3", "Z4", "Z5"]

RESERVOIR_NODE = "RES1"
TANK_NODE = "TANK1"
SCENARIO_JUNCTION = "J3"


def find_epanet_file():
    """Find the EPANET input file created by hydraulic simulation."""

    files = list(HYDRAULIC_FOLDER.rglob("*.inp"))

    if not files:
        raise FileNotFoundError(
            "\nEPANET .inp file was not found.\n"
            f"Expected it somewhere inside: {HYDRAULIC_FOLDER}\n"
            "Run the hydraulic simulation first."
        )

    # Select the most recently modified EPANET input file.
    return max(files, key=lambda file: file.stat().st_mtime)


def load_network(inp_file):
    """Load a fresh network for an individual scenario."""

    return wntr.network.WaterNetworkModel(str(inp_file))


def scale_all_demands(network, factor):
    """Increase or decrease all junction demands."""

    for node_name in network.junction_name_list:
        node = network.get_node(node_name)

        for demand in node.demand_timeseries_list:
            demand.base_value = float(demand.base_value) * factor


def apply_scenario(network, scenario_name):
    """Apply scenario-specific changes to the network."""

    if scenario_name == "normal":
        pass

    elif scenario_name == "peak_demand":
        # Simulate a 50% increase in campus water demand.
        scale_all_demands(network, 1.50)

    elif scenario_name == "drought":
        # Reduce available reservoir head by 5 metres.
        reservoir = network.get_node(RESERVOIR_NODE)
        reservoir.base_head = float(reservoir.base_head) - 5.0

    elif scenario_name == "leakage":
        # Add a small continuous discharge at junction J3.
        junction = network.get_node(SCENARIO_JUNCTION)
        junction.add_demand(
            0.0005,
            None,
            "simulated_leakage"
        )

    elif scenario_name == "pipe_burst":
        # Represent a larger uncontrolled discharge at junction J3.
        junction = network.get_node(SCENARIO_JUNCTION)
        junction.add_demand(
            0.0020,
            None,
            "simulated_burst"
        )

    elif scenario_name == "water_conservation":
        # Simulate a 25% reduction in demand.
        scale_all_demands(network, 0.75)

    elif scenario_name == "pump_outage":
        # Close all pumps for this scenario.
        if not network.pump_name_list:
            raise ValueError("No pump was found in the hydraulic network.")

        for pump_name in network.pump_name_list:
            pump = network.get_link(pump_name)
            pump.initial_status = LinkStatus.Closed

    else:
        raise ValueError(f"Unknown scenario: {scenario_name}")

    return network


def run_one_scenario(inp_file, scenario_name):
    """Run EPANET and export the results for one scenario."""

    print("\n" + "=" * 60)
    print(f"RUNNING SCENARIO: {scenario_name.upper()}")
    print("=" * 60)

    scenario_folder = OUTPUT_FOLDER / scenario_name
    scenario_folder.mkdir(parents=True, exist_ok=True)

    # Always load a fresh network.
    network = load_network(inp_file)

    # Apply the scenario.
    network = apply_scenario(network, scenario_name)

    # Run EPANET.
    simulator = wntr.sim.EpanetSimulator(network)

    results = simulator.run_sim(
        file_prefix=str(scenario_folder / scenario_name),
        convergence_error=True
    )

    # --------------------------------------------------------
    # ZONE PRESSURE
    # --------------------------------------------------------

    pressure = results.node["pressure"]

    missing_zones = [
        zone for zone in ZONE_NODES
        if zone not in pressure.columns
    ]

    if missing_zones:
        raise ValueError(
            f"Missing zone pressure columns: {missing_zones}"
        )

    zone_pressure = pressure[ZONE_NODES]

    zone_pressure.to_csv(
        scenario_folder / "zone_pressure.csv"
    )

    minimum_pressure = float(zone_pressure.min().min())
    maximum_pressure = float(zone_pressure.max().max())
    average_pressure = float(zone_pressure.mean().mean())

    minimum_location = zone_pressure.stack().idxmin()

    # --------------------------------------------------------
    # TANK WATER LEVEL
    # --------------------------------------------------------

    tank = network.get_node(TANK_NODE)
    tank_head = results.node["head"][TANK_NODE]

    tank_level = tank_head - float(tank.elevation)

    tank_level_df = tank_level.to_frame(name="tank_level_m")

    tank_level_df.to_csv(
        scenario_folder / "tank_level.csv"
    )

    minimum_tank_level = float(tank_level.min())
    maximum_tank_level = float(tank_level.max())

    # --------------------------------------------------------
    # PIPE FLOW
    # --------------------------------------------------------

    flowrate = results.link["flowrate"]

    flowrate.to_csv(
        scenario_folder / "link_flowrate.csv"
    )

    maximum_flow = float(flowrate.abs().max().max())

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    summary = {
        "scenario": scenario_name,
        "status": "SUCCESS",
        "minimum_zone_pressure_m": round(minimum_pressure, 3),
        "maximum_zone_pressure_m": round(maximum_pressure, 3),
        "average_zone_pressure_m": round(average_pressure, 3),
        "lowest_pressure_node": minimum_location[1],
        "lowest_pressure_time_hours": round(
            float(minimum_location[0]) / 3600, 2
        ),
        "minimum_tank_level_m": round(minimum_tank_level, 3),
        "maximum_tank_level_m": round(maximum_tank_level, 3),
        "maximum_absolute_flow_m3s": round(maximum_flow, 6),
    }

    summary_df = pd.DataFrame([summary])

    summary_df.to_csv(
        scenario_folder / "scenario_summary.csv",
        index=False
    )

    print("\nSCENARIO RESULTS")
    print("-" * 45)
    print(f"Minimum zone pressure : {minimum_pressure:.3f} m")
    print(f"Average zone pressure : {average_pressure:.3f} m")
    print(f"Maximum zone pressure : {maximum_pressure:.3f} m")
    print(f"Lowest pressure node  : {minimum_location[1]}")
    print(f"Minimum tank level    : {minimum_tank_level:.3f} m")
    print(f"Maximum tank level    : {maximum_tank_level:.3f} m")
    print(f"Maximum flow          : {maximum_flow:.6f} m3/s")

    print(f"\nSaved results: {scenario_folder}")

    return summary


def run_all_scenarios():
    """Run all seven campus water scenarios."""

    print("\n" + "=" * 60)
    print("              URBANPULSE AI")
    print("          SCENARIO SIMULATION")
    print("=" * 60)

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    inp_file = find_epanet_file()

    print(f"\nEPANET model found: {inp_file.name}")

    scenarios = [
        "normal",
        "peak_demand",
        "drought",
        "leakage",
        "pipe_burst",
        "water_conservation",
        "pump_outage",
    ]

    all_summaries = []

    for scenario in scenarios:

        try:
            result = run_one_scenario(
                inp_file,
                scenario
            )

            all_summaries.append(result)

        except Exception as error:
            print("\nSCENARIO FAILED")
            print(f"Scenario: {scenario}")
            print(f"Reason: {error}")

            all_summaries.append({
                "scenario": scenario,
                "status": "FAILED",
                "error": str(error),
            })

    # --------------------------------------------------------
    # COMBINED REPORT
    # --------------------------------------------------------

    combined = pd.DataFrame(all_summaries)

    combined.to_csv(
        OUTPUT_FOLDER / "all_scenarios_summary.csv",
        index=False
    )

    report_path = OUTPUT_FOLDER / "scenario_report.txt"

    with open(report_path, "w", encoding="utf-8") as file:
        file.write("URBANPULSE AI - SCENARIO SIMULATION REPORT\n")
        file.write("=" * 55 + "\n\n")
        file.write("Dataset: Synthetic campus water demand\n")
        file.write("Network: Conceptual campus water network\n")
        file.write("Simulation engine: EPANET through WNTR\n\n")
        file.write(combined.to_string(index=False))
        file.write("\n\nIMPORTANT:\n")
        file.write(
            "Leakage and pipe burst are represented as additional "
            "junction discharge.\n"
        )
        file.write(
            "All results are simulation outputs based on assumed "
            "network parameters.\n"
        )
        file.write(
            "They are not measurements or verified predictions "
            "for a real campus.\n"
        )

    print("\n" + "=" * 60)
    print("ALL SCENARIOS PROCESSED")
    print("=" * 60)

    print(combined.to_string(index=False))

    print(f"\nCombined CSV: {OUTPUT_FOLDER / 'all_scenarios_summary.csv'}")
    print(f"Text report : {report_path}")


if __name__ == "__main__":
    run_all_scenarios()