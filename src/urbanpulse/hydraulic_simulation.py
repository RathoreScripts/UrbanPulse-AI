
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import yaml
import wntr

from wntr.network.controls import (
    Control,
    ControlAction,
    ValueCondition
)

from wntr.network.base import LinkStatus


# ============================================================
# URBANPULSE AI - HYDRAULIC SIMULATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "campus_water_demand.csv"
)

NETWORK_CONFIG_FILE = (
    PROJECT_ROOT / "config" / "network_config.yaml"
)

HYDRAULIC_CONFIG_FILE = (
    PROJECT_ROOT / "config" / "hydraulic_config.yaml"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "artifacts"
    / "reports"
    / "hydraulic"
)

PLOT_DIR = OUTPUT_DIR / "plots"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PLOT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 1. LOAD CONFIGURATION
# ============================================================

def load_yaml(file_path):

    if not file_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


# ============================================================
# 2. LOAD SYNTHETIC DEMAND DATA
# ============================================================

def load_demand_data():

    print("\nLoading synthetic demand dataset...")

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    required_columns = [
        "timestamp",
        "zone",
        "demand_liters"
    ]

    for column in required_columns:

        if column not in df.columns:
            raise ValueError(
                f"Missing required column: {column}"
            )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df["zone"] = (
        df["zone"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df["demand_liters"] = pd.to_numeric(
        df["demand_liters"],
        errors="coerce"
    )

    if df["timestamp"].isna().any():
        raise ValueError("Invalid timestamps found.")

    if df["demand_liters"].isna().any():
        raise ValueError("Invalid demand values found.")

    if (df["demand_liters"] < 0).any():
        raise ValueError("Negative demand values found.")

    print(f"Demand records loaded: {len(df)}")

    print(
        "Zones in dataset:",
        sorted(df["zone"].unique().tolist())
    )

    return df


# ============================================================
# 3. PREPARE ZONE-WISE DEMAND
# ============================================================

def prepare_zone_demand(df, demand_mapping):

    print("\nPreparing zone-wise water demand...")

    zone_data = {}

    for zone, node_id in demand_mapping.items():

        zone = zone.lower()

        zone_df = df[df["zone"] == zone].copy()

        if zone_df.empty:
            raise ValueError(
                f"No records found for zone: {zone}"
            )

        hourly_demand = (
            zone_df.groupby(
                zone_df["timestamp"].dt.hour
            )["demand_liters"]
            .mean()
            .reindex(range(24), fill_value=0)
        )

        average_demand_lph = float(
            zone_df["demand_liters"].mean()
        )

        if average_demand_lph <= 0:
            raise ValueError(
                f"Invalid average demand for {zone}"
            )

        # Convert L/hour to m3/second.
        base_demand_m3s = (
            average_demand_lph / 1000.0 / 3600.0
        )

        # Generate 24-hour demand pattern.
        multipliers = (
            hourly_demand / average_demand_lph
        ).tolist()

        zone_data[zone] = {
            "node_id": node_id,
            "average_demand_lph": average_demand_lph,
            "base_demand_m3s": base_demand_m3s,
            "hourly_demand": hourly_demand,
            "multipliers": multipliers
        }

        print(
            f"{zone}: {average_demand_lph:.2f} L/hour"
        )

    print("\nZone demand preparation completed.")

    return zone_data


# ============================================================
# 4. BUILD HYDRAULIC NETWORK
# ============================================================

def build_hydraulic_network(
    network_config,
    hydraulic_config,
    zone_data
):

    print("\nBuilding hydraulic network...")

    wn = wntr.network.WaterNetworkModel()

    # --------------------------------------------------------
    # SIMULATION SETTINGS
    # --------------------------------------------------------

    simulation_config = hydraulic_config["simulation"]

    units_config = hydraulic_config["units"]

    hydraulics_config = hydraulic_config["hydraulics"]

    wn.options.time.duration = (
        int(simulation_config["duration_hours"]) * 3600
    )

    wn.options.time.hydraulic_timestep = int(
        simulation_config["hydraulic_timestep_seconds"]
    )

    wn.options.time.report_timestep = int(
        simulation_config["report_timestep_seconds"]
    )

    wn.options.time.pattern_timestep = 3600

    wn.options.hydraulic.headloss = (
        hydraulics_config["headloss"]
    )

    wn.options.hydraulic.inpfile_units = (
        units_config["flow"]
    )

    wn.options.hydraulic.accuracy = 0.001

    wn.options.hydraulic.trials = 200

    wn.options.hydraulic.unbalanced = "STOP"

    # --------------------------------------------------------
    # RESERVOIR AND TANK IDs
    # --------------------------------------------------------

    reservoir_config = hydraulic_config["reservoir"]

    tank_config = hydraulic_config["tank"]

    reservoir_id = reservoir_config["node_id"]

    tank_id = tank_config["node_id"]

    # --------------------------------------------------------
    # ADD RESERVOIR
    # --------------------------------------------------------

    wn.add_reservoir(
        name=reservoir_id,
        base_head=float(
            reservoir_config["base_head_m"]
        )
    )

    # --------------------------------------------------------
    # ADD OVERHEAD TANK
    # --------------------------------------------------------

    wn.add_tank(
        name=tank_id,
        elevation=float(
            tank_config["elevation_m"]
        ),
        init_level=float(
            tank_config["initial_level_m"]
        ),
        min_level=float(
            tank_config["minimum_level_m"]
        ),
        max_level=float(
            tank_config["maximum_level_m"]
        ),
        diameter=float(
            tank_config["diameter_m"]
        ),
        min_vol=0.0
    )

    # --------------------------------------------------------
    # ADD JUNCTIONS AND DEMAND ZONES
    # --------------------------------------------------------

    junction_elevations = hydraulic_config[
        "junction_elevations"
    ]

    zone_elevations = hydraulic_config[
        "zone_elevations"
    ]

    for node in network_config["nodes"]:

        node_id = node["id"]

        node_type = node["type"]

        if node_type in ["reservoir", "tank"]:
            continue

        # Main network junctions.
        if node_type == "junction":

            if node_id not in junction_elevations:
                raise ValueError(
                    f"Elevation missing for {node_id}"
                )

            wn.add_junction(
                name=node_id,
                base_demand=0.0,
                elevation=float(
                    junction_elevations[node_id]
                )
            )

        # Campus demand-zone junctions.
        elif node_type == "demand_zone":

            zone = node["zone"].lower()

            if zone not in zone_data:
                raise ValueError(
                    f"Demand data missing for {zone}"
                )

            if node_id not in zone_elevations:
                raise ValueError(
                    f"Elevation missing for {node_id}"
                )

            pattern_name = f"PAT_{node_id}"

            wn.add_pattern(
                pattern_name,
                zone_data[zone]["multipliers"]
            )

            wn.add_junction(
                name=node_id,
                base_demand=zone_data[zone][
                    "base_demand_m3s"
                ],
                demand_pattern=pattern_name,
                elevation=float(
                    zone_elevations[node_id]
                )
            )

    # --------------------------------------------------------
    # ADD NETWORK PIPES
    # --------------------------------------------------------

    pipe_count = 0

    for pipe in network_config["pipes"]:

        pipe_id = pipe["id"]

        start_node = pipe["from"]

        end_node = pipe["to"]

        # P01 and P02 are replaced by the pump.
        if pipe_id in ["P01", "P02"]:
            continue

        diameter_m = (
            float(pipe["diameter_mm"]) / 1000.0
        )

        wn.add_pipe(
            name=pipe_id,
            start_node_name=start_node,
            end_node_name=end_node,
            length=float(pipe["length_m"]),
            diameter=diameter_m,
            roughness=float(
                hydraulics_config[
                    "hazen_williams_roughness"
                ]
            ),
            minor_loss=0.0,
            initial_status="OPEN"
        )

        pipe_count += 1

    # --------------------------------------------------------
    # ADD PUMP CHARACTERISTIC CURVE
    # --------------------------------------------------------

    # Assumed engineering values for the conceptual network.
    # Flow: m3/s
    # Head: metres
    #
    # These are NOT actual campus pump specifications.

    pump_curve_points = [
        (0.0, 30.0),
        (0.002, 20.0),
        (0.004, 5.0)
    ]

    wn.add_curve(
        "PUMP_CURVE_1",
        "HEAD",
        pump_curve_points
    )

    # --------------------------------------------------------
    # ADD PUMP
    # --------------------------------------------------------

    pump_config = hydraulic_config["pump"]

    pump_id = pump_config["link_id"]

    wn.add_pump(
        name=pump_id,
        start_node_name=reservoir_id,
        end_node_name=tank_id,
        pump_type="HEAD",
        pump_parameter="PUMP_CURVE_1",
        initial_status="OPEN"
    )

    # --------------------------------------------------------
    # AUTOMATIC PUMP CONTROLS
    # --------------------------------------------------------

    tank_node = wn.get_node(tank_id)

    pump_node = wn.get_link(pump_id)

    turn_off_level = float(
        pump_config["turn_off_level_m"]
    )

    turn_on_level = float(
        pump_config["turn_on_level_m"]
    )

    # Stop pump when tank level reaches upper threshold.
    condition_off = ValueCondition(
        tank_node,
        "level",
        ">",
        turn_off_level
    )

    action_off = ControlAction(
        pump_node,
        "status",
        LinkStatus.Closed
    )

    wn.add_control(
        "pump_off_high_level",
        Control(condition_off, action_off)
    )

    # Restart pump when tank level reaches lower threshold.
    condition_on = ValueCondition(
        tank_node,
        "level",
        "<",
        turn_on_level
    )

    action_on = ControlAction(
        pump_node,
        "status",
        LinkStatus.Open
    )

    wn.add_control(
        "pump_on_low_level",
        Control(condition_on, action_on)
    )

    print("Automatic pump controls configured.")

    # --------------------------------------------------------
    # NETWORK SUMMARY
    # --------------------------------------------------------

    print("\nNETWORK SUMMARY")

    print("Hydraulic nodes:", len(wn.node_name_list))

    print("Hydraulic links:", len(wn.link_name_list))

    print("Hydraulic pipes:", pipe_count)

    print("Hydraulic pumps:", len(wn.pump_name_list))

    return wn


# ============================================================
# 5. EXPORT EPANET MODEL
# ============================================================

def export_epanet_model(wn):

    print("\nExporting EPANET input model...")

    inp_path = OUTPUT_DIR / "urbanpulse_network.inp"

    wntr.network.write_inpfile(
        wn,
        str(inp_path),
        units="LPS",
        version=2.2
    )

    print(f"EPANET model saved: {inp_path}")

    return inp_path


# ============================================================
# 6. RUN EPANET SIMULATION
# ============================================================

def run_epanet_simulation(wn):

    print("\nStarting EPANET hydraulic simulation...")

    print(
        "Hydraulic timestep:",
        wn.options.time.hydraulic_timestep // 60,
        "minutes"
    )

    print(
        "Simulation duration:",
        wn.options.time.duration // 3600,
        "hours"
    )

    print("Please wait...")

    simulator = wntr.sim.EpanetSimulator(wn)

    file_prefix = OUTPUT_DIR / "urbanpulse_run"

    results = simulator.run_sim(
        file_prefix=str(file_prefix),
        convergence_error=True
    )

    print("\nEPANET simulation completed successfully.")

    return results


# ============================================================
# 7. PROCESS HYDRAULIC RESULTS
# ============================================================

def process_results(results, hydraulic_config):

    print("\nProcessing hydraulic results...")

    tank_id = hydraulic_config["tank"]["node_id"]

    tank_elevation = float(
        hydraulic_config["tank"]["elevation_m"]
    )

    def convert_time(dataframe):

        output = dataframe.copy()

        output.index = (
            output.index.astype(float) / 3600.0
        )

        output.index.name = "time_hours"

        return output

    pressure = convert_time(
        results.node["pressure"]
    )

    demand = convert_time(
        results.node["demand"]
    )

    head = convert_time(
        results.node["head"]
    )

    flowrate = convert_time(
        results.link["flowrate"]
    )

    velocity = convert_time(
        results.link["velocity"]
    )

    link_status = convert_time(
        results.link["status"]
    )

    # Tank level = tank hydraulic head - tank elevation.
    tank_level = head[[tank_id]].copy()

    tank_level[tank_id] = (
        tank_level[tank_id] - tank_elevation
    )

    # Save result files.
    pressure.to_csv(
        OUTPUT_DIR / "node_pressure.csv"
    )

    demand.to_csv(
        OUTPUT_DIR / "node_demand.csv"
    )

    head.to_csv(
        OUTPUT_DIR / "node_head.csv"
    )

    tank_level.to_csv(
        OUTPUT_DIR / "tank_level.csv"
    )

    flowrate.to_csv(
        OUTPUT_DIR / "pipe_flowrate.csv"
    )

    velocity.to_csv(
        OUTPUT_DIR / "pipe_velocity.csv"
    )

    link_status.to_csv(
        OUTPUT_DIR / "link_status.csv"
    )

    print("Hydraulic CSV files saved successfully.")

    return {
        "pressure": pressure,
        "demand": demand,
        "head": head,
        "tank_level": tank_level,
        "flowrate": flowrate,
        "velocity": velocity,
        "link_status": link_status
    }


# ============================================================
# 8. GENERATE HYDRAULIC SUMMARY
# ============================================================

def generate_summary(result_data, hydraulic_config):

    print("\nGenerating hydraulic summary...")

    pressure = result_data["pressure"]

    tank_level = result_data["tank_level"]

    flowrate = result_data["flowrate"]

    velocity = result_data["velocity"]

    tank_id = hydraulic_config["tank"]["node_id"]

    lines = []

    lines.append("=" * 60)
    lines.append("                 URBANPULSE AI")
    lines.append("          HYDRAULIC SIMULATION REPORT")
    lines.append("=" * 60)

    lines.append("")
    lines.append("SIMULATION INFORMATION")
    lines.append("-" * 60)

    lines.append("Duration: 24 hours")
    lines.append("Solver: EPANET 2.2")
    lines.append("Dataset: Synthetic")
    lines.append("Network: Conceptual campus water network")

    lines.append("")
    lines.append("PRESSURE SUMMARY")
    lines.append("-" * 60)

    lines.append(
        f"Minimum pressure: {pressure.min().min():.3f} m"
    )

    lines.append(
        f"Maximum pressure: {pressure.max().max():.3f} m"
    )

    lines.append(
        f"Average pressure: {pressure.mean().mean():.3f} m"
    )

    lines.append("")
    lines.append("TANK LEVEL SUMMARY")
    lines.append("-" * 60)

    lines.append(
        f"Minimum level: {tank_level[tank_id].min():.3f} m"
    )

    lines.append(
        f"Maximum level: {tank_level[tank_id].max():.3f} m"
    )

    lines.append(
        f"Average level: {tank_level[tank_id].mean():.3f} m"
    )

    lines.append("")
    lines.append("PIPE FLOW SUMMARY")
    lines.append("-" * 60)

    lines.append(
        f"Maximum absolute flow: "
        f"{flowrate.abs().max().max():.6f} m3/s"
    )

    lines.append(
        f"Maximum absolute velocity: "
        f"{velocity.abs().max().max():.6f} m/s"
    )

    lines.append("")
    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)

    report_text = "\n".join(lines)

    report_path = OUTPUT_DIR / "hydraulic_summary.txt"

    report_path.write_text(
        report_text,
        encoding="utf-8"
    )

    print(report_text)

    print(f"\nSummary saved: {report_path}")


# ============================================================
# 9. CREATE HYDRAULIC PLOTS
# ============================================================

def create_hydraulic_plots(
    result_data,
    hydraulic_config
):

    print("\nCreating hydraulic visualizations...")

    pressure = result_data["pressure"]

    tank_level = result_data["tank_level"]

    flowrate = result_data["flowrate"]

    velocity = result_data["velocity"]

    tank_id = hydraulic_config["tank"]["node_id"]

    # --------------------------------------------------------
    # PLOT 1: ZONE PRESSURE
    # --------------------------------------------------------

    plt.figure(figsize=(12, 6))

    zone_columns = [
        column
        for column in pressure.columns
        if column.startswith("Z")
    ]

    for node in zone_columns:

        plt.plot(
            pressure.index,
            pressure[node],
            label=node
        )

    plt.title("Zone-wise Hydraulic Pressure")

    plt.xlabel("Time (Hours)")

    plt.ylabel("Pressure (m)")

    plt.legend()

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        PLOT_DIR / "01_zone_pressure.png",
        dpi=300
    )

    plt.close()

    # --------------------------------------------------------
    # PLOT 2: TANK WATER LEVEL
    # --------------------------------------------------------

    plt.figure(figsize=(12, 6))

    plt.plot(
        tank_level.index,
        tank_level[tank_id],
        marker="o",
        label="Overhead Tank"
    )

    plt.axhline(
        float(
            hydraulic_config["tank"]["minimum_level_m"]
        ),
        linestyle="--",
        label="Minimum Level"
    )

    plt.axhline(
        float(
            hydraulic_config["tank"]["maximum_level_m"]
        ),
        linestyle="--",
        label="Maximum Level"
    )

    plt.title("Overhead Tank Water Level")

    plt.xlabel("Time (Hours)")

    plt.ylabel("Water Level (m)")

    plt.legend()

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        PLOT_DIR / "02_tank_water_level.png",
        dpi=300
    )

    plt.close()

    # --------------------------------------------------------
    # PLOT 3: PIPE FLOW RATE
    # --------------------------------------------------------

    plt.figure(figsize=(12, 6))

    for pipe in flowrate.columns:

        plt.plot(
            flowrate.index,
            flowrate[pipe],
            label=pipe
        )

    plt.title("Pipe-wise Flow Rate")

    plt.xlabel("Time (Hours)")

    plt.ylabel("Flow Rate (m3/s)")

    plt.legend(
        loc="best",
        fontsize=7,
        ncol=3
    )

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        PLOT_DIR / "03_pipe_flowrate.png",
        dpi=300
    )

    plt.close()

    # --------------------------------------------------------
    # PLOT 4: PIPE VELOCITY
    # --------------------------------------------------------

    plt.figure(figsize=(12, 6))

    for pipe in velocity.columns:

        plt.plot(
            velocity.index,
            velocity[pipe],
            label=pipe
        )

    plt.title("Pipe-wise Water Velocity")

    plt.xlabel("Time (Hours)")

    plt.ylabel("Velocity (m/s)")

    plt.legend(
        loc="best",
        fontsize=7,
        ncol=3
    )

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        PLOT_DIR / "04_pipe_velocity.png",
        dpi=300
    )

    plt.close()

    print("All hydraulic plots saved successfully.")


# ============================================================
# 10. MAIN EXECUTION
# ============================================================

def run_hydraulic_simulation():

    print("\n")

    print("=" * 60)
    print("                  URBANPULSE AI")
    print("               HYDRAULIC SIMULATION")
    print("=" * 60)

    try:

        print("\nLoading configuration files...")

        network_config = load_yaml(
            NETWORK_CONFIG_FILE
        )

        hydraulic_config = load_yaml(
            HYDRAULIC_CONFIG_FILE
        )

        # Load dataset.
        df = load_demand_data()

        # Prepare zone demand.
        demand_mapping = hydraulic_config[
            "demand_mapping"
        ]

        zone_data = prepare_zone_demand(
            df,
            demand_mapping
        )

        # Build network.
        wn = build_hydraulic_network(
            network_config,
            hydraulic_config,
            zone_data
        )

        # Export EPANET input.
        export_epanet_model(wn)

        # Run EPANET.
        results = run_epanet_simulation(wn)

        # Process results.
        result_data = process_results(
            results,
            hydraulic_config
        )

        # Generate report.
        generate_summary(
            result_data,
            hydraulic_config
        )

        # Generate plots.
        create_hydraulic_plots(
            result_data,
            hydraulic_config
        )

        print("\n")

        print("=" * 60)
        print("       HYDRAULIC SIMULATION COMPLETED")
        print("=" * 60)

        print("\nOutput directory:")
        print(OUTPUT_DIR)

        print("\nPlot directory:")
        print(PLOT_DIR)

    except Exception as error:

        print("\n")

        print("=" * 60)
        print("       HYDRAULIC SIMULATION FAILED")
        print("=" * 60)

        print(f"\nError: {error}")

        raise


if __name__ == "__main__":

    run_hydraulic_simulation()
