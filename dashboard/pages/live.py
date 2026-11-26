
"""
UrbanPulse AI - Live Operations Dashboard

Displays simulated telemetry from the FastAPI backend.
Refreshes automatically every 5 seconds.

IMPORTANT:
All readings are simulated prototype data,
not physical sensor data.
"""

from datetime import datetime

import requests
import pandas as pd
import plotly.graph_objects as go

import dash_bootstrap_components as dbc
from dash import (
    html,
    dcc,
    Input,
    Output,
    ALL,
    ctx,
    callback,
)
from dash.exceptions import PreventUpdate


# ============================================================
# 1. API CONFIGURATION
# ============================================================

API_BASE_URL = "http://127.0.0.1:8000"
REFRESH_INTERVAL = 5000


def fetch_api(endpoint):
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            timeout=4
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException:
        return None


def get_rows(payload):
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        rows = payload.get("data", [])
        return rows if isinstance(rows, list) else []

    return []


def format_number(value, decimals=1):
    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def format_timestamp(value):
    if not value:
        return "Waiting for first reading"

    try:
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
        return dt.strftime("%d %b %Y · %I:%M:%S %p")

    except (ValueError, TypeError):
        return str(value)


# ============================================================
# 2. REUSABLE COMPONENTS
# ============================================================

def metric_card(title, value_id, unit, description, accent):

    return dbc.Card(
        dbc.CardBody([

            html.Div(
                title,
                className="live-kpi-label"
            ),

            html.Div([

                html.Span(
                    "—",
                    id=value_id,
                    className="live-kpi-value"
                ),

                html.Span(
                    unit,
                    className="live-kpi-unit"
                )

            ], className="live-kpi-reading"),

            html.Div(
                description,
                className="live-kpi-description"
            )

        ]),
        className=f"live-kpi-card {accent} h-100"
    )


def make_empty_chart():

    fig = go.Figure()

    fig.update_layout(
        template="plotly_dark",
        height=330,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=15, r=15, t=20, b=20),

        annotations=[dict(
            text="Waiting for telemetry readings",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(color="#94a3b8", size=13)
        )],

        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    return fig


def make_zone_card(zone):

    name = zone.get(
        "zone_name",
        zone.get("zone", "Unknown")
    )

    consumption = format_number(
        zone.get("consumption_lph")
    )

    pressure = format_number(
        zone.get("pressure_m"), 2
    )

    status = str(
        zone.get("status", "UNKNOWN")
    ).upper()

    status_class = (
        "zone-status-normal"
        if status == "NORMAL"
        else "zone-status-warning"
    )

    return dbc.Col(

        dbc.Card(
            dbc.CardBody([

                html.Div([

                    html.Div(
                        name,
                        className="live-zone-title"
                    ),

                    html.Span(
                        status,
                        className=(
                            f"live-zone-status {status_class}"
                        )
                    )

                ], className="live-zone-top"),

                html.Div(
                    consumption,
                    className="live-zone-value"
                ),

                html.Div(
                    "Litres per hour",
                    className="live-zone-unit"
                ),

                html.Div(
                    className="live-zone-divider"
                ),

                html.Div([

                    html.Span("Hydraulic pressure"),

                    html.Strong(f"{pressure} m")

                ], className="live-zone-pressure-row")

            ]),

            className="live-zone-card h-100"
        ),

        xs=12,
        sm=6,
        lg=4,
        xl=2,
        className="mb-3"
    )


# ============================================================
# 3. ALERT COMPONENT WITH ACKNOWLEDGEMENT BUTTON
# ============================================================

def make_alert_item(alert):

    severity = str(
        alert.get("severity", "INFO")
    ).upper()

    alert_id = alert.get("id")

    acknowledged = bool(
        alert.get("acknowledged", 0)
    )

    if severity == "CRITICAL":
        severity_class = "alert-critical"

    elif severity in ["WARNING", "ERROR"]:
        severity_class = "alert-warning"

    else:
        severity_class = "alert-info"

    acknowledgement_text = (
        "ACKNOWLEDGED"
        if acknowledged
        else "UNACKNOWLEDGED"
    )

    acknowledgement_class = (
        "alert-acknowledged"
        if acknowledged
        else "alert-unacknowledged"
    )

    # Show the button only for unacknowledged alerts.
    if not acknowledged and alert_id is not None:

        acknowledgement_action = html.Button(
            "Acknowledge",
            id={
                "type": "acknowledge-alert",
                "index": int(alert_id)
            },
            n_clicks=0,
            className="live-alert-ack-button",
            type="button"
        )

    else:

        acknowledgement_action = html.Span(
            "Completed",
            className="live-alert-completed"
        )

    return html.Div([

        # ALERT HEADER
        html.Div([

            html.Div([

                html.Span(
                    severity,
                    className=(
                        f"live-alert-severity {severity_class}"
                    )
                ),

                html.Span(
                    alert.get("zone") or "Campus-wide",
                    className="live-alert-zone"
                )

            ], className="live-alert-left"),

            html.Span(
                acknowledgement_text,
                className=(
                    f"live-alert-state {acknowledgement_class}"
                )
            )

        ], className="live-alert-top"),

        # MESSAGE
        html.Div(
            alert.get(
                "message",
                "System notification"
            ),
            className="live-alert-message"
        ),

        # TIMESTAMP AND SOURCE
        html.Div([

            html.Span(
                format_timestamp(alert.get("timestamp")),
                className="live-alert-time"
            ),

            html.Span(
                alert.get("source", "UNKNOWN"),
                className="live-alert-source"
            )

        ], className="live-alert-bottom"),

        # ACKNOWLEDGEMENT ACTION
        html.Div(
            acknowledgement_action,
            className="live-alert-action-row"
        )

    ], className="live-alert-item")


# ============================================================
# 4. PAGE LAYOUT
# ============================================================

layout = dbc.Container([

    # PAGE HEADING
    html.Div([

        html.Div([

            html.Div(
                "CAMPUS WATER MANAGEMENT",
                className="live-eyebrow"
            ),

            html.H2(
                "Live Operations",
                className="live-page-title"
            ),

            html.P(
                "Simulation monitoring of water consumption, "
                "storage and hydraulic conditions across "
                "five campus zones.",
                className="live-page-description"
            )

        ]),

        dbc.Badge(
            "SIMULATION MODE",
            className="live-simulation-badge"
        )

    ], className="live-page-header"),

    # SYSTEM STATUS
    html.Div([

        html.Div([

            html.Span(
                className="live-connection-dot",
                id="live-connection-dot"
            ),

            html.Div([

                html.Div(
                    "SYSTEM CONNECTION",
                    className="live-status-caption"
                ),

                html.Div(
                    "Connecting to UrbanPulse API...",
                    id="api-connection-status",
                    className="live-status-main"
                )

            ])

        ], className="live-status-left"),

        html.Div([

            html.Div(
                "LAST TELEMETRY UPDATE",
                className="live-status-caption"
            ),

            html.Div(
                "Waiting for data",
                id="live-last-update",
                className="live-status-main"
            )

        ], className="live-status-right")

    ], className="live-system-banner"),

    # KPI CARDS
    dbc.Row([

        dbc.Col(
            metric_card(
                "CAMPUS CONSUMPTION",
                "live-consumption",
                "L/h",
                "Current simulated demand",
                "accent-cyan"
            ),
            xs=12, sm=6, xl=3
        ),

        dbc.Col(
            metric_card(
                "WATER SUPPLY",
                "live-supply",
                "L/h",
                "Assumed supply capacity",
                "accent-blue"
            ),
            xs=12, sm=6, xl=3
        ),

        dbc.Col(
            metric_card(
                "OVERHEAD TANK",
                "live-tank",
                "%",
                "Estimated simulated level",
                "accent-green"
            ),
            xs=12, sm=6, xl=3
        ),

        dbc.Col(
            metric_card(
                "SYSTEM CONDITION",
                "live-system-status",
                "",
                "Simulator status classification",
                "accent-orange"
            ),
            xs=12, sm=6, xl=3
        )

    ], className="g-3 live-kpi-row"),

    # CHART AND TANK
    dbc.Row([

        dbc.Col(

            dbc.Card(
                dbc.CardBody([

                    html.Div([

                        html.Div([

                            html.H5(
                                "Campus Consumption Trend",
                                className="live-panel-title"
                            ),

                            html.P(
                                "Latest saved telemetry snapshots",
                                className="live-panel-subtitle"
                            )

                        ]),

                        html.Span(
                            "AUTO REFRESH · 5 SEC",
                            className="live-chart-tag"
                        )

                    ], className="live-panel-heading"),

                    dcc.Graph(
                        id="live-consumption-chart",
                        figure=make_empty_chart(),
                        config={
                            "displayModeBar": False,
                            "responsive": True
                        }
                    )

                ]),

                className="live-panel h-100"
            ),

            lg=8
        ),

        dbc.Col(

            dbc.Card(
                dbc.CardBody([

                    html.H5(
                        "Tank Storage",
                        className="live-panel-title"
                    ),

                    html.P(
                        "Simulated overhead tank level",
                        className="live-panel-subtitle"
                    ),

                    html.Div([

                        html.Span(
                            "—",
                            id="live-tank-large",
                            className="live-tank-large-value"
                        ),

                        html.Span(
                            "%",
                            className="live-tank-percent"
                        )

                    ], className="live-tank-reading"),

                    dbc.Progress(
                        id="live-tank-progress",
                        value=0,
                        className="live-tank-progress"
                    ),

                    html.Div([

                        html.Span("Tank capacity"),

                        html.Strong(
                            "50,000 L",
                            className="live-tank-detail"
                        )

                    ], className="live-tank-detail-row"),

                    html.Div([

                        html.Span("Supply rate"),

                        html.Strong(
                            "—",
                            id="live-tank-supply",
                            className="live-tank-detail"
                        )

                    ], className="live-tank-detail-row"),

                    html.Div([

                        html.Span("Current demand"),

                        html.Strong(
                            "—",
                            id="live-tank-demand",
                            className="live-tank-detail"
                        )

                    ], className="live-tank-detail-row"),

                    html.Div(
                        "Capacity and supply are prototype assumptions.",
                        className="live-tank-note"
                    )

                ]),

                className="live-panel h-100"
            ),

            lg=4
        )

    ], className="g-3 live-chart-row"),

    # ZONE MONITORING
    html.Div([

        html.Div([

            html.Div([

                html.H5(
                    "Campus Zone Monitoring",
                    className="live-panel-title"
                ),

                html.P(
                    "Latest consumption and pressure readings "
                    "from all five simulated zones.",
                    className="live-panel-subtitle"
                )

            ]),

            html.Span(
                "5 ZONES",
                className="live-chart-tag"
            )

        ], className="live-panel-heading"),

        dbc.Row(
            id="live-zone-cards",
            children=[
                dbc.Col(
                    html.P(
                        "Waiting for zone readings...",
                        className="live-empty-message"
                    )
                )
            ],
            className="g-3"
        )

    ], className="live-zones-section"),

    # ALERTS AND TELEMETRY
    dbc.Row([

        dbc.Col(

            dbc.Card(
                dbc.CardBody([

                    html.Div([

                        html.Div([

                            html.H5(
                                "Recent System Alerts",
                                className="live-panel-title"
                            ),

                            html.P(
                                "Latest recorded system events",
                                className="live-panel-subtitle"
                            )

                        ]),

                        html.Div(
                            "0 UNACKNOWLEDGED IN LATEST 10",
                            id="live-alert-summary",
                            className="live-alert-summary"
                        )

                    ], className="live-panel-heading"),

                    # ACKNOWLEDGEMENT FEEDBACK
                    html.Div(
                        id="live-alert-action-feedback",
                        children="",
                        className="live-alert-feedback"
                    ),

                    html.Div(
                        id="live-alert-list",
                        children=html.P(
                            "Waiting for alerts...",
                            className="live-empty-message"
                        ),
                        className="live-alert-list"
                    )

                ]),

                className="live-panel h-100"
            ),

            lg=8
        ),

        dbc.Col(

            dbc.Card(
                dbc.CardBody([

                    html.H5(
                        "Telemetry Information",
                        className="live-panel-title"
                    ),

                    html.P(
                        "Current data pipeline",
                        className="live-panel-subtitle"
                    ),

                    html.Div([

                        html.Span("Data source"),
                        html.Strong("SIMULATED")

                    ], className="live-info-row"),

                    html.Div([

                        html.Span("Operating mode"),
                        html.Strong("SIMULATION")

                    ], className="live-info-row"),

                    html.Div([

                        html.Span("Refresh interval"),
                        html.Strong("5 seconds")

                    ], className="live-info-row"),

                    html.Div([

                        html.Span("Saved snapshots"),
                        html.Strong(
                            "—",
                            id="live-snapshot-count"
                        )

                    ], className="live-info-row"),

                    html.Div([

                        html.Span("Zone readings"),
                        html.Strong(
                            "—",
                            id="live-zone-count"
                        )

                    ], className="live-info-row")

                ]),

                className="live-panel h-100"
            ),

            lg=4
        )

    ], className="g-3 live-alert-row"),

    # AUTO REFRESH
    dcc.Interval(
        id="live-refresh",
        interval=REFRESH_INTERVAL,
        n_intervals=0
    )

], fluid=True, className="dashboard-content live-container")


# ============================================================
# 5. LIVE TELEMETRY CALLBACK
# ============================================================

@callback(

    Output("api-connection-status", "children"),
    Output("live-connection-dot", "className"),

    Output("live-consumption", "children"),
    Output("live-supply", "children"),
    Output("live-tank", "children"),
    Output("live-system-status", "children"),

    Output("live-last-update", "children"),
    Output("live-snapshot-count", "children"),
    Output("live-zone-count", "children"),

    Output("live-consumption-chart", "figure"),
    Output("live-zone-cards", "children"),

    Output("live-alert-list", "children"),
    Output("live-alert-summary", "children"),

    Output("live-tank-large", "children"),
    Output("live-tank-progress", "value"),
    Output("live-tank-supply", "children"),
    Output("live-tank-demand", "children"),

    Input("live-refresh", "n_intervals")

)
def update_live_dashboard(n_intervals):

    # --------------------------------------------------------
    # FETCH API DATA
    # --------------------------------------------------------

    latest = fetch_api("/api/telemetry/latest")

    history = fetch_api(
        "/api/telemetry/history?limit=50"
    )

    zones_response = fetch_api("/api/zones")

    alerts_response = fetch_api(
        "/api/alerts?limit=10"
    )

    # Latest endpoint returns a direct object
    if not isinstance(latest, dict) or history is None:

        return (
            "API unavailable — check FastAPI.",
            "live-connection-dot offline",
            "—", "—", "—", "OFFLINE",
            "No connection",
            "—", "—",
            make_empty_chart(),
            html.P(
                "Unable to load zone readings.",
                className="live-empty-message"
            ),
            html.P(
                "Alerts unavailable.",
                className="live-empty-message"
            ),
            "Alerts unavailable",
            "—", 0, "—", "—"
        )

    telemetry = latest

    # --------------------------------------------------------
    # CURRENT METRICS
    # --------------------------------------------------------

    consumption_value = telemetry.get(
        "total_consumption_lph"
    )

    supply_value = telemetry.get("supply_lph")

    tank_value = telemetry.get("tank_level_percent")

    consumption = format_number(consumption_value)

    supply = format_number(supply_value)

    tank = format_number(tank_value)

    status = str(
        telemetry.get("system_status", "UNKNOWN")
    ).upper()

    timestamp = format_timestamp(
        telemetry.get("timestamp")
    )

    snapshot_count = str(
        telemetry.get("reading_count", "—")
    )

    try:

        tank_progress = max(
            0,
            min(100, float(tank_value))
        )

    except (ValueError, TypeError):

        tank_progress = 0

    # --------------------------------------------------------
    # CONSUMPTION HISTORY CHART
    # --------------------------------------------------------

    history_rows = get_rows(history)

    history_df = pd.DataFrame(history_rows)

    figure = make_empty_chart()

    required_columns = {
        "timestamp",
        "total_consumption_lph"
    }

    if (
        not history_df.empty
        and required_columns.issubset(history_df.columns)
    ):

        history_df["timestamp"] = pd.to_datetime(
            history_df["timestamp"],
            errors="coerce"
        )

        history_df["total_consumption_lph"] = pd.to_numeric(
            history_df["total_consumption_lph"],
            errors="coerce"
        )

        history_df = (
            history_df.dropna(
                subset=[
                    "timestamp",
                    "total_consumption_lph"
                ]
            )
            .sort_values("timestamp")
        )

        if not history_df.empty:

            figure = go.Figure()

            figure.add_trace(

                go.Scatter(

                    x=history_df["timestamp"],

                    y=history_df["total_consumption_lph"],

                    mode="lines",

                    name="Campus consumption",

                    line=dict(
                        color="#38bdf8",
                        width=2.7
                    ),

                    fill="tozeroy",

                    fillcolor="rgba(56,189,248,0.08)",

                    hovertemplate=(
                        "%{x|%d %b, %H:%M:%S}<br>"
                        "<b>%{y:,.1f} L/h</b>"
                        "<extra></extra>"
                    )

                )

            )

            figure.update_layout(

                template="plotly_dark",

                height=330,

                margin=dict(
                    l=15,
                    r=15,
                    t=15,
                    b=35
                ),

                paper_bgcolor="rgba(0,0,0,0)",

                plot_bgcolor="rgba(0,0,0,0)",

                hovermode="x unified",

                showlegend=False,

                xaxis=dict(
                    title=None,
                    showgrid=False,
                    color="#94a3b8",
                    tickfont=dict(size=10)
                ),

                yaxis=dict(
                    title="Consumption (L/h)",
                    title_font=dict(
                        size=11,
                        color="#94a3b8"
                    ),
                    gridcolor="rgba(148,163,184,0.12)",
                    zeroline=False,
                    color="#94a3b8",
                    tickfont=dict(size=10)
                )

            )

    # --------------------------------------------------------
    # ZONE CARDS
    # --------------------------------------------------------

    zone_rows = get_rows(zones_response)

    zone_cards = [
        make_zone_card(zone)
        for zone in zone_rows
    ]

    if not zone_cards:

        zone_content = html.P(
            "No zone readings available.",
            className="live-empty-message"
        )

    else:

        zone_content = zone_cards

    # --------------------------------------------------------
    # ALERTS
    # --------------------------------------------------------

    alert_rows = get_rows(alerts_response)

    # API already orders alerts by newest ID first.
    # Keep this order; do not reverse it.

    alert_items = [
        make_alert_item(alert)
        for alert in alert_rows
    ]

    unacknowledged_count = sum(
        1
        for alert in alert_rows
        if not bool(alert.get("acknowledged", 0))
    )

    alert_summary = (
        f"{unacknowledged_count} UNACKNOWLEDGED IN LATEST 10"
    )

    if not alert_items:

        alert_content = html.P(
            "No alerts have been recorded.",
            className="live-empty-message"
        )

    else:

        alert_content = alert_items

    # --------------------------------------------------------
    # RETURN DASHBOARD VALUES
    # --------------------------------------------------------

    return (

        "Connected · Simulation data",

        "live-connection-dot online",

        consumption,
        supply,
        tank,
        status,

        timestamp,

        snapshot_count,
        str(len(zone_rows)),

        figure,

        zone_content,

        alert_content,
        alert_summary,

        tank,
        tank_progress,

        f"{supply} L/h",
        f"{consumption} L/h"

    )


# ============================================================
# 6. ALERT ACKNOWLEDGEMENT CALLBACK
# ============================================================

@callback(

    Output(
        "live-alert-action-feedback",
        "children"
    ),

    Input(
        {
            "type": "acknowledge-alert",
            "index": ALL
        },
        "n_clicks"
    ),

    prevent_initial_call=True

)
def acknowledge_alert_callback(n_clicks):

    # Identify which alert button was clicked.
    triggered_id = ctx.triggered_id

    if not isinstance(triggered_id, dict):
        raise PreventUpdate

    alert_id = triggered_id.get("index")

    if alert_id is None:
        raise PreventUpdate

    # Ignore callbacks that did not come from a real click.
    triggered_value = (
        ctx.triggered[0].get("value")
        if ctx.triggered
        else None
    )

    if not triggered_value:
        raise PreventUpdate

    # Send acknowledgement request to FastAPI.
    try:

        response = requests.patch(
            (
                f"{API_BASE_URL}/api/alerts/"
                f"{alert_id}/acknowledge"
            ),
            timeout=5
        )

        response.raise_for_status()

        result = response.json()

        if result.get("success"):

            return html.Div(
                [
                    html.Strong("Success: "),
                    f"Alert #{alert_id} acknowledged. "
                    "The alert list will refresh automatically."
                ],
                className="live-alert-feedback-success"
            )

        return html.Div(
            f"Alert #{alert_id} could not be acknowledged.",
            className="live-alert-feedback-error"
        )

    except requests.RequestException as error:

        return html.Div(
            (
                f"Unable to acknowledge alert #{alert_id}. "
                f"API error: {error}"
            ),
            className="live-alert-feedback-error"
        )

    except (ValueError, TypeError):

        return html.Div(
            "The API returned an unexpected response.",
            className="live-alert-feedback-error"
        )
