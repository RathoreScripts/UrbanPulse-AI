
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

import sqlite3

from realtime.storage import (
    DATABASE_PATH,
    initialize_database
)


# --------------------------------------------------
# 1. CREATE FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="UrbanPulse AI API",
    description="API for campus water management and telemetry.",
    version="1.1.0"
)


# --------------------------------------------------
# 2. ENABLE CORS FOR DASH FRONTEND
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8050",
        "http://localhost:8050",
        "http://127.0.0.1:8000",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# 3. DATABASE CONNECTION
# --------------------------------------------------

def get_db_connection():

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    return connection


# --------------------------------------------------
# 4. INITIALIZE DATABASE WHEN API STARTS
# --------------------------------------------------

@app.on_event("startup")
def startup_event():

    initialize_database()

    print("UrbanPulse AI API started successfully.")


# --------------------------------------------------
# 5. ROOT ENDPOINT
# --------------------------------------------------

@app.get("/")
def home():

    return {
        "project": "UrbanPulse AI",
        "message": "Campus Water Management API is running",
        "mode": "SIMULATION",
        "status": "ONLINE"
    }


# --------------------------------------------------
# 6. HEALTH CHECK
# --------------------------------------------------

@app.get("/api/health")
def health_check():

    return {
        "status": "healthy",
        "database": "connected",
        "mode": "SIMULATION"
    }


# --------------------------------------------------
# 7. LATEST TELEMETRY
# --------------------------------------------------

@app.get("/api/telemetry/latest")
def latest_telemetry():

    connection = get_db_connection()

    try:

        telemetry = connection.execute(
            """
            SELECT *
            FROM telemetry
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        if telemetry is None:

            return {
                "message": "No telemetry data available yet",
                "data": None
            }

        telemetry_data = dict(telemetry)

        zone_readings = connection.execute(
            """
            SELECT *
            FROM zone_readings
            WHERE telemetry_id = ?
            ORDER BY zone
            """,
            (telemetry_data["id"],)
        ).fetchall()

        telemetry_data["zones"] = [
            dict(row) for row in zone_readings
        ]

        return telemetry_data

    finally:

        connection.close()


# --------------------------------------------------
# 8. TELEMETRY HISTORY
# --------------------------------------------------

@app.get("/api/telemetry/history")
def telemetry_history(
    limit: int = Query(default=50, ge=1, le=1000)
):

    connection = get_db_connection()

    try:

        rows = connection.execute(
            """
            SELECT *
            FROM telemetry
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

        return {
            "count": len(rows),
            "data": [
                dict(row) for row in reversed(rows)
            ]
        }

    finally:

        connection.close()


# --------------------------------------------------
# 9. LATEST ZONE READINGS
# --------------------------------------------------

@app.get("/api/zones")
def zone_readings():

    connection = get_db_connection()

    try:

        latest = connection.execute(
            """
            SELECT id
            FROM telemetry
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        if latest is None:

            return {
                "count": 0,
                "data": []
            }

        rows = connection.execute(
            """
            SELECT *
            FROM zone_readings
            WHERE telemetry_id = ?
            ORDER BY zone
            """,
            (latest["id"],)
        ).fetchall()

        return {
            "count": len(rows),
            "data": [
                dict(row) for row in rows
            ]
        }

    finally:

        connection.close()


# --------------------------------------------------
# 10. RECENT ALERTS
# --------------------------------------------------

@app.get("/api/alerts")
def recent_alerts(
    limit: int = Query(default=20, ge=1, le=500)
):

    connection = get_db_connection()

    try:

        rows = connection.execute(
            """
            SELECT *
            FROM alerts
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

        return {
            "count": len(rows),
            "data": [
                dict(row) for row in rows
            ]
        }

    finally:

        connection.close()


# --------------------------------------------------
# 11. ACKNOWLEDGE ALERT
# --------------------------------------------------

@app.patch("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int):

    connection = get_db_connection()

    try:

        # Check whether the alert exists
        alert = connection.execute(
            """
            SELECT id, acknowledged
            FROM alerts
            WHERE id = ?
            """,
            (alert_id,)
        ).fetchone()

        if alert is None:

            raise HTTPException(
                status_code=404,
                detail="Alert not found"
            )

        # Update only the requested alert
        if alert["acknowledged"] == 0:

            connection.execute(
                """
                UPDATE alerts
                SET acknowledged = 1
                WHERE id = ?
                """,
                (alert_id,)
            )

            connection.commit()

        return {
            "success": True,
            "message": "Alert acknowledged successfully",
            "alert_id": alert_id,
            "acknowledged": True
        }

    finally:

        connection.close()
