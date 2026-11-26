
"""
UrbanPulse AI - SQLite Telemetry Storage

Stores simulated or future real sensor readings.
Does not modify the original project datasets.
"""

import sqlite3
import json

from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_DIR = PROJECT_ROOT / "data" / "realtime"

DATABASE_PATH = DATABASE_DIR / "urbanpulse_telemetry.db"


def get_connection():

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                mode TEXT NOT NULL,
                system_status TEXT,
                total_consumption_lph REAL,
                supply_lph REAL,
                tank_level_percent REAL,
                tank_capacity_liters REAL,
                reading_count INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zone_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telemetry_id INTEGER NOT NULL,
                zone TEXT NOT NULL,
                zone_name TEXT NOT NULL,
                consumption_lph REAL,
                pressure_m REAL,
                source TEXT NOT NULL,
                status TEXT,
                FOREIGN KEY (telemetry_id)
                    REFERENCES telemetry(id)
                    ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                severity TEXT NOT NULL,
                zone TEXT,
                message TEXT NOT NULL,
                source TEXT NOT NULL,
                acknowledged INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp
            ON telemetry(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_zone_telemetry
            ON zone_readings(telemetry_id)
        """)

        connection.commit()

        print("UrbanPulse database initialized.")
        print(f"Database location: {DATABASE_PATH}")

    finally:

        connection.close()


def save_telemetry(snapshot):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO telemetry (
                timestamp,
                source,
                mode,
                system_status,
                total_consumption_lph,
                supply_lph,
                tank_level_percent,
                tank_capacity_liters,
                reading_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot["timestamp"],
            snapshot["source"],
            snapshot["mode"],
            snapshot["system_status"],
            snapshot["total_consumption_lph"],
            snapshot["supply_lph"],
            snapshot["tank_level_percent"],
            snapshot["tank_capacity_liters"],
            snapshot["reading_count"]
        ))

        telemetry_id = cursor.lastrowid

        for zone in snapshot["zones"]:

            cursor.execute("""
                INSERT INTO zone_readings (
                    telemetry_id,
                    zone,
                    zone_name,
                    consumption_lph,
                    pressure_m,
                    source,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                telemetry_id,
                zone["zone"],
                zone["zone_name"],
                zone["consumption_lph"],
                zone["pressure_m"],
                zone["source"],
                zone["status"]
            ))

        connection.commit()

        return telemetry_id

    finally:

        connection.close()


def get_latest_telemetry():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM telemetry
            ORDER BY id DESC
            LIMIT 1
        """)

        row = cursor.fetchone()

        if row is None:
            return None

        result = dict(row)

        cursor.execute("""
            SELECT zone, zone_name,
                   consumption_lph, pressure_m,
                   source, status
            FROM zone_readings
            WHERE telemetry_id = ?
            ORDER BY id
        """, (result["id"],))

        result["zones"] = [
            dict(item)
            for item in cursor.fetchall()
        ]

        return result

    finally:

        connection.close()


def get_recent_telemetry(limit=100):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM telemetry
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:

        connection.close()


def get_zone_history(zone, limit=100):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                t.timestamp,
                z.zone,
                z.consumption_lph,
                z.pressure_m,
                z.source
            FROM zone_readings z
            JOIN telemetry t
                ON t.id = z.telemetry_id
            WHERE z.zone = ?
            ORDER BY t.id DESC
            LIMIT ?
        """, (zone.lower(), limit))

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:

        connection.close()


def save_alert(severity, message, zone=None, source="SIMULATED"):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO alerts (
                timestamp,
                severity,
                zone,
                message,
                source
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            severity,
            zone,
            message,
            source
        ))

        connection.commit()

        return cursor.lastrowid

    finally:

        connection.close()


def get_recent_alerts(limit=50):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM alerts
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:

        connection.close()


if __name__ == "__main__":

    initialize_database()
