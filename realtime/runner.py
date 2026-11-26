
"""
UrbanPulse AI - Telemetry Runner

Continuously:
1. Generates simulated sensor readings.
2. Saves readings to SQLite.
3. Detects system-status changes.
4. Records status alerts.
5. Repeats every five seconds.

All generated readings are SIMULATED.
"""

import time
from datetime import datetime

from realtime.simulator import TelemetrySimulator

from realtime.storage import (
    initialize_database,
    save_telemetry,
    save_alert,
    get_latest_telemetry,
)


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

UPDATE_INTERVAL_SECONDS = 5


# ---------------------------------------------------------
# TELEMETRY RUNNER
# ---------------------------------------------------------

class TelemetryRunner:

    def __init__(self):

        self.simulator = TelemetrySimulator()

        self.total_saved = 0

        # Initialize database before retrieving saved status
        initialize_database()

        # Restore the last known status from SQLite
        latest = get_latest_telemetry()

        if latest is not None:
            self.previous_status = latest["system_status"]

            print(
                "Previous system status restored:",
                self.previous_status
            )

        else:
            self.previous_status = None

            print("No previous telemetry status found.")

    # -----------------------------------------------------
    # PROCESS ONE TELEMETRY UPDATE
    # -----------------------------------------------------

    def process_update(self):

        # Generate a new simulated snapshot
        snapshot = self.simulator.generate_readings()

        # Save snapshot and five zone readings
        telemetry_id = save_telemetry(snapshot)

        self.total_saved += 1

        current_status = snapshot["system_status"]

        # -------------------------------------------------
        # DETECT SYSTEM STATUS CHANGES
        # -------------------------------------------------

        if current_status != self.previous_status:

            if current_status != "NORMAL":

                save_alert(
                    severity="WARNING",
                    message=(
                        f"Campus system status changed to "
                        f"{current_status}"
                    ),
                    source="SIMULATED"
                )

                print(
                    f"\n[ALERT] {current_status}\n"
                )

            elif self.previous_status is not None:

                save_alert(
                    severity="INFO",
                    message="Campus system returned to NORMAL",
                    source="SIMULATED"
                )

                print(
                    "\n[INFO] Campus system returned to NORMAL\n"
                )

        # Update status for the next reading
        self.previous_status = current_status

        # -------------------------------------------------
        # DISPLAY UPDATE
        # -------------------------------------------------

        print("=" * 55)

        print(
            "Time:",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        print("Mode: SIMULATION")

        print("Database record ID:", telemetry_id)

        print("System status:", current_status)

        print(
            "Total consumption:",
            snapshot["total_consumption_lph"],
            "L/hour"
        )

        print(
            "Water supply:",
            snapshot["supply_lph"],
            "L/hour"
        )

        print(
            "Tank level:",
            snapshot["tank_level_percent"],
            "%"
        )

        print("\nZone readings:")

        for zone in snapshot["zones"]:

            print(
                f"{zone['zone_name']:<12}"
                f" Consumption: "
                f"{zone['consumption_lph']:>9.2f} L/hour"
                f" | Pressure: {zone['pressure_m']:.3f} m"
            )

        print("\nTotal saved records:", self.total_saved)

    # -----------------------------------------------------
    # CONTINUOUS EXECUTION
    # -----------------------------------------------------

    def start(self):

        print("\nUrbanPulse AI Telemetry Runner Started")

        print("Mode: SIMULATION")

        print(
            f"Update interval: "
            f"{UPDATE_INTERVAL_SECONDS} seconds"
        )

        print("Press CTRL+C to stop.\n")

        try:

            while True:

                start_time = time.time()

                self.process_update()

                elapsed = time.time() - start_time

                sleep_time = max(
                    0,
                    UPDATE_INTERVAL_SECONDS - elapsed
                )

                time.sleep(sleep_time)

        except KeyboardInterrupt:

            print("\nStopping telemetry runner...")

            print(
                "Total telemetry snapshots saved:",
                self.total_saved
            )

            print("Runner stopped successfully.")


# ---------------------------------------------------------
# APPLICATION ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":

    runner = TelemetryRunner()

    runner.start()
