
"""
UrbanPulse AI - Real-Time Telemetry Simulator

IMPORTANT:
This module generates SIMULATED sensor readings.
It does not connect to real campus sensors.

It uses the existing historical water-demand dataset
to create more realistic, time-dependent readings.
"""

from pathlib import Path
from datetime import datetime
import random

import pandas as pd


# ---------------------------------------------------------
# PROJECT PATHS AND CONFIGURATION
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "campus_water_demand.csv"
)

HYDRAULIC_PATH = (
    PROJECT_ROOT
    / "artifacts"
    / "reports"
    / "hydraulic"
    / "node_pressure.csv"
)

ZONES = [
    "hostel",
    "academic",
    "canteen",
    "medical",
    "sports",
]

ZONE_DISPLAY_NAMES = {
    "hostel": "Hostel",
    "academic": "Academic",
    "canteen": "Canteen",
    "medical": "Medical",
    "sports": "Sports",
}


# ---------------------------------------------------------
# TELEMETRY SIMULATOR CLASS
# ---------------------------------------------------------

class TelemetrySimulator:

    def __init__(self):

        self.random = random.Random()

        self.history = self._load_historical_data()

        self.pressure_baselines = self._load_pressure_baselines()

        # Initial simulated tank level
        self.tank_level_percent = 75.0

        # Assumed supply capacity for the prototype
        self.supply_capacity_lph = 6800.0

        # Hysteresis: remember whether high demand is active
        self.high_demand_active = False

        self.last_update = None

        # Count generated telemetry readings
        self.reading_count = 0

        print("UrbanPulse telemetry simulator initialized.")
        print("Mode: SIMULATION")
        print(f"Historical records loaded: {len(self.history)}")

    # -----------------------------------------------------
    # LOAD HISTORICAL DEMAND DATA
    # -----------------------------------------------------

    def _load_historical_data(self):

        if not DATASET_PATH.exists():

            raise FileNotFoundError(
                f"Historical dataset not found: {DATASET_PATH}"
            )

        df = pd.read_csv(DATASET_PATH)

        required_columns = [
            "timestamp",
            "zone",
            "demand_liters",
        ]

        missing = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing:

            raise ValueError(
                f"Missing dataset columns: {missing}"
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

        df = df.dropna(
            subset=[
                "timestamp",
                "zone",
                "demand_liters",
            ]
        )

        df = df[
            df["zone"].isin(ZONES)
            & (df["demand_liters"] >= 0)
        ].copy()

        if df.empty:

            raise ValueError(
                "No valid historical demand records found."
            )

        df["hour"] = df["timestamp"].dt.hour

        return df

    # -----------------------------------------------------
    # LOAD HYDRAULIC PRESSURE BASELINES
    # -----------------------------------------------------

    def _load_pressure_baselines(self):

        default_values = {
            "hostel": 2.2,
            "academic": 2.1,
            "canteen": 2.0,
            "medical": 2.3,
            "sports": 2.0,
        }

        if not HYDRAULIC_PATH.exists():

            return default_values

        try:

            pressure_df = pd.read_csv(HYDRAULIC_PATH)

            pressure_columns = {
                "hostel": "Z1",
                "academic": "Z2",
                "canteen": "Z3",
                "medical": "Z4",
                "sports": "Z5",
            }

            for zone, column in pressure_columns.items():

                if column in pressure_df.columns:

                    values = pd.to_numeric(
                        pressure_df[column],
                        errors="coerce"
                    ).dropna()

                    if not values.empty:

                        default_values[zone] = float(
                            values.mean()
                        )

        except Exception as error:

            print(
                "Could not load hydraulic pressure baselines:",
                error
            )

        return default_values

    # -----------------------------------------------------
    # GET HISTORICAL DEMAND PROFILE
    # -----------------------------------------------------

    def _get_base_demand(self, zone, hour):

        zone_data = self.history[
            self.history["zone"] == zone
        ]

        hour_data = zone_data[
            zone_data["hour"] == hour
        ]

        if not hour_data.empty:

            return float(
                hour_data["demand_liters"].median()
            )

        if not zone_data.empty:

            return float(
                zone_data["demand_liters"].median()
            )

        return 0.0

    # -----------------------------------------------------
    # GENERATE ONE TELEMETRY UPDATE
    # -----------------------------------------------------

    def generate_readings(self):

        now = datetime.now()

        hour = now.hour

        readings = []

        total_consumption = 0.0

        # Generate a simulated reading for each zone
        for zone in ZONES:

            base_demand = self._get_base_demand(
                zone,
                hour
            )

            # Small variation around historical demand
            variation = self.random.uniform(
                0.94,
                1.06
            )

            consumption_lph = max(
                0.0,
                base_demand * variation
            )

            # Simulated network pressure
            base_pressure = self.pressure_baselines[zone]

            pressure = base_pressure + self.random.uniform(
                -0.08,
                0.08
            )

            pressure = max(0.0, pressure)

            total_consumption += consumption_lph

            readings.append({

                "timestamp": now.isoformat(),

                "zone": zone,

                "zone_name": ZONE_DISPLAY_NAMES[zone],

                "consumption_lph": round(
                    consumption_lph,
                    2
                ),

                "pressure_m": round(
                    pressure,
                    3
                ),

                "source": "SIMULATED",

                "status": "NORMAL",

            })

        # -------------------------------------------------
        # SIMULATED WATER SUPPLY
        # -------------------------------------------------

        supply_lph = self.supply_capacity_lph

        # Difference between supply and consumption
        net_flow_lph = (
            supply_lph - total_consumption
        )

        # Assume this update represents five seconds.
        # Convert hourly flow into a five-second volume.
        tank_change_liters = (
            net_flow_lph * 5 / 3600
        )

        # Illustrative tank capacity
        tank_capacity_liters = 50000.0

        tank_change_percent = (
            tank_change_liters
            / tank_capacity_liters
            * 100
        )

        self.tank_level_percent += tank_change_percent

        self.tank_level_percent = max(
            0.0,
            min(
                100.0,
                self.tank_level_percent
            )
        )

        # -------------------------------------------------
        # SYSTEM STATUS WITH HYSTERESIS
        # -------------------------------------------------

        # Enter HIGH DEMAND when consumption exceeds supply.
        # Once active, remain HIGH DEMAND until consumption
        # falls at least 5% below the assumed supply capacity.

        recovery_threshold = supply_lph * 0.95

        if self.high_demand_active:

            if total_consumption < recovery_threshold:
                self.high_demand_active = False

        else:

            if total_consumption > supply_lph:
                self.high_demand_active = True


        # Low tank level has the highest priority.
        if self.tank_level_percent < 20:

            system_status = "LOW TANK LEVEL"

        elif self.high_demand_active:

            system_status = "HIGH DEMAND"

        else:

            system_status = "NORMAL"

        # -------------------------------------------------
        # RETURN TELEMETRY SNAPSHOT
        # -------------------------------------------------

        self.reading_count += 1

        self.last_update = now

        snapshot = {

            "timestamp": now.isoformat(),

            "source": "SIMULATED",

            "mode": "SIMULATION",

            "system_status": system_status,

            "total_consumption_lph": round(
                total_consumption,
                2
            ),

            "supply_lph": round(
                supply_lph,
                2
            ),

            "tank_level_percent": round(
                self.tank_level_percent,
                2
            ),

            "tank_capacity_liters": tank_capacity_liters,

            "zones": readings,

            "reading_count": self.reading_count,

        }

        return snapshot


# ---------------------------------------------------------
# STANDALONE TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    simulator = TelemetrySimulator()

    print("\nGenerating simulated telemetry...\n")

    for _ in range(3):

        data = simulator.generate_readings()

        print("-------------------------------------")

        print(
            "Timestamp:",
            data["timestamp"]
        )

        print(
            "System status:",
            data["system_status"]
        )

        print(
            "Total consumption:",
            data["total_consumption_lph"],
            "L/hour"
        )

        print(
            "Tank level:",
            data["tank_level_percent"],
            "%"
        )

        print("\nZone readings:")

        for zone in data["zones"]:

            print(
                zone["zone_name"],
                "|",
                zone["consumption_lph"],
                "L/hour",
                "| Pressure:",
                zone["pressure_m"],
                "m"
            )
