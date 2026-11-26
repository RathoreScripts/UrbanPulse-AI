
"""
UrbanPulse AI - Overview Dashboard Page

Displays existing project data:
1. Historical water consumption KPIs
2. Hourly campus demand trend
3. Zone-wise water consumption
4. Saved campus demand forecast
5. Zone-wise forecast summary

This page reads existing project files only.
It does not generate data or retrain models.
"""

import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import dash_bootstrap_components as dbc
from dash import html, dcc

from dashboard import data_loader


# ============================================================
# 1. COMMON HELPERS
# ============================================================

def empty_dataframe(columns):
    """Create an empty DataFrame with the requested columns."""
    return pd.DataFrame(columns=columns)


def safe_load(loader, required_columns, section_name):
    """
    Load one project dataset safely.

    If a file is missing or invalid, return an empty DataFrame
    so that the rest of the Overview page can still load.
    """

    try:
        df = loader()

        if not isinstance(df, pd.DataFrame):
            raise ValueError("The loader did not return a DataFrame.")

        missing = [
            column for column in required_columns
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing required columns: {', '.join(missing)}"
            )

        return df.copy()

    except Exception as error:
        print(f"[OVERVIEW] Could not load {section_name}: {error}")
        return empty_dataframe(required_columns)


def clean_numeric_data(df, column):
    """Convert a column to numeric and remove invalid values."""

    if column not in df.columns:
        return df

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    df = df.dropna(subset=[column])

    df = df[
        df[column].apply(
            lambda value: math.isfinite(float(value))
        )
    ]

    return df


def format_liters(value):
    """Format a numeric value as litres."""

    if value is None or pd.isna(value):
        return "N/A"

    return f"{value:,.0f} L"


def format_date(value, date_format="%d %b %Y"):
    """Safely format a date or timestamp."""

    if value is None or pd.isna(value):
        return "N/A"

    return pd.Timestamp(value).strftime(date_format)


def empty_chart(message, height=360):
    """Create a consistent empty chart message."""

    figure = go.Figure()

    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=14, color="#94a3b8")
    )

    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    return figure


def style_chart(figure, height=360):
    """Apply a consistent dashboard chart style."""

    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=30),
        height=height,
        font=dict(
            color="#cbd5e1",
            family="Arial, sans-serif"
        ),
        title=dict(
            font=dict(size=16, color="#f1f5f9")
        ),
        hoverlabel=dict(
            bgcolor="#111a2e",
            font_color="#f8fafc"
        ),
        xaxis=dict(
            gridcolor="rgba(148,163,184,0.12)",
            zerolinecolor="rgba(148,163,184,0.12)"
        ),
        yaxis=dict(
            gridcolor="rgba(148,163,184,0.12)",
            zerolinecolor="rgba(148,163,184,0.12)"
        ),
        autosize=True
    )

    return figure


# ============================================================
# 2. LOAD PROJECT DATA SAFELY
# ============================================================

demand_df = safe_load(
    data_loader.load_demand_data,
    ["timestamp", "zone", "demand_liters"],
    "historical demand"
)

forecast_df = safe_load(
    data_loader.load_forecast_data,
    ["timestamp", "zone", "predicted_demand_liters"],
    "zone forecast"
)

campus_forecast_df = safe_load(
    data_loader.load_campus_forecast,
    ["timestamp", "predicted_demand_liters"],
    "campus forecast"
)


# ============================================================
# 3. CLEAN HISTORICAL DATA
# ============================================================

if not demand_df.empty:

    demand_df["timestamp"] = pd.to_datetime(
        demand_df["timestamp"],
        errors="coerce"
    )

    demand_df["zone"] = (
        demand_df["zone"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    demand_df = clean_numeric_data(
        demand_df,
        "demand_liters"
    )

    demand_df = demand_df.dropna(
        subset=["timestamp", "zone"]
    )

    demand_df = demand_df[
        demand_df["demand_liters"] >= 0
    ]

    demand_df = demand_df.sort_values(
        "timestamp"
    ).reset_index(drop=True)


# ============================================================
# 4. CLEAN FORECAST DATA
# ============================================================

if not forecast_df.empty:

    forecast_df["timestamp"] = pd.to_datetime(
        forecast_df["timestamp"],
        errors="coerce"
    )

    forecast_df["zone"] = (
        forecast_df["zone"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    forecast_df = clean_numeric_data(
        forecast_df,
        "predicted_demand_liters"
    )

    forecast_df = forecast_df.dropna(
        subset=["timestamp", "zone"]
    )

    forecast_df = forecast_df[
        forecast_df["predicted_demand_liters"] >= 0
    ]

    forecast_df = forecast_df.sort_values(
        ["timestamp", "zone"]
    ).reset_index(drop=True)


# ============================================================
# 5. CLEAN CAMPUS FORECAST DATA
# ============================================================

if not campus_forecast_df.empty:

    campus_forecast_df["timestamp"] = pd.to_datetime(
        campus_forecast_df["timestamp"],
        errors="coerce"
    )

    campus_forecast_df = clean_numeric_data(
        campus_forecast_df,
        "predicted_demand_liters"
    )

    campus_forecast_df = campus_forecast_df.dropna(
        subset=["timestamp"]
    )

    campus_forecast_df = campus_forecast_df[
        campus_forecast_df["predicted_demand_liters"] >= 0
    ]

    campus_forecast_df = (
        campus_forecast_df
        .groupby("timestamp", as_index=False)
        ["predicted_demand_liters"]
        .sum()
        .sort_values("timestamp")
        .reset_index(drop=True)
    )


# ============================================================
# 6. PREPARE HISTORICAL DEMAND
# ============================================================

if not demand_df.empty:

    hourly_demand = (
        demand_df.groupby("timestamp", as_index=False)
        ["demand_liters"]
        .sum()
        .sort_values("timestamp")
    )

    zone_demand = (
        demand_df.groupby("zone", as_index=False)
        ["demand_liters"]
        .sum()
        .sort_values(
            "demand_liters",
            ascending=False
        )
    )

    total_demand = demand_df["demand_liters"].sum()

    average_hourly_demand = (
        hourly_demand["demand_liters"].mean()
    )

    total_zones = demand_df["zone"].nunique()

    historical_start = demand_df["timestamp"].min()
    historical_end = demand_df["timestamp"].max()

    total_records = len(demand_df)

else:

    hourly_demand = empty_dataframe(
        ["timestamp", "demand_liters"]
    )

    zone_demand = empty_dataframe(
        ["zone", "demand_liters"]
    )

    total_demand = None
    average_hourly_demand = None
    total_zones = 0
    historical_start = None
    historical_end = None
    total_records = 0


# ============================================================
# 7. PREPARE FORECAST SUMMARY
# ============================================================

if not campus_forecast_df.empty:

    forecast_start = campus_forecast_df["timestamp"].min()
    forecast_end = campus_forecast_df["timestamp"].max()

    forecast_total = (
        campus_forecast_df["predicted_demand_liters"].sum()
    )

else:

    forecast_start = None
    forecast_end = None
    forecast_total = None


# Prefer the saved campus forecast.
# If unavailable, derive the campus total from the saved
# zone-wise forecast, without generating new predictions.

if campus_forecast_df.empty and not forecast_df.empty:

    campus_forecast_df = (
        forecast_df.groupby("timestamp", as_index=False)
        ["predicted_demand_liters"]
        .sum()
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    forecast_start = campus_forecast_df["timestamp"].min()
    forecast_end = campus_forecast_df["timestamp"].max()

    forecast_total = (
        campus_forecast_df["predicted_demand_liters"].sum()
    )


if not forecast_df.empty:

    zone_forecast = (
        forecast_df.groupby("zone", as_index=False)
        ["predicted_demand_liters"]
        .sum()
        .sort_values(
            "predicted_demand_liters",
            ascending=False
        )
    )

elif not campus_forecast_df.empty:

    zone_forecast = empty_dataframe(
        ["zone", "predicted_demand_liters"]
    )

else:

    zone_forecast = empty_dataframe(
        ["zone", "predicted_demand_liters"]
    )


forecast_hours = (
    campus_forecast_df["timestamp"].nunique()
    if not campus_forecast_df.empty
    else 0
)


# ============================================================
# 8. KPI CARD COMPONENT
# ============================================================

def create_kpi_card(title, value, description, symbol):

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.Div(
                            symbol,
                            className="overview-kpi-icon"
                        ),

                        html.P(
                            title,
                            className="overview-kpi-label"
                        )
                    ],
                    className="overview-kpi-top"
                ),

                html.H3(
                    value,
                    className="overview-kpi-value"
                ),

                html.P(
                    description,
                    className="overview-kpi-description"
                )
            ]
        ),
        className="overview-kpi-card h-100"
    )


# ============================================================
# 9. HISTORICAL DEMAND CHART
# ============================================================

if not hourly_demand.empty:

    historical_chart = px.line(
        hourly_demand,
        x="timestamp",
        y="demand_liters",
        labels={
            "timestamp": "Date and Time",
            "demand_liters": "Water Demand (Litres)"
        }
    )

    historical_chart.update_traces(
        line=dict(
            color="#38bdf8",
            width=2
        ),
        hovertemplate=(
            "Time: %{x|%d %b %Y, %H:%M}<br>"
            "Demand: %{y:,.2f} L"
            "<extra></extra>"
        )
    )

    historical_chart.update_layout(
        title="Campus Water Consumption Over Time",
        hovermode="x unified"
    )

    historical_chart = style_chart(historical_chart)

else:

    historical_chart = empty_chart(
        "Historical demand data is unavailable."
    )


# ============================================================
# 10. ZONE-WISE DEMAND CHART
# ============================================================

if not zone_demand.empty:

    zone_chart = px.bar(
        zone_demand,
        x="zone",
        y="demand_liters",
        color="zone",
        labels={
            "zone": "Campus Zone",
            "demand_liters": "Total Consumption (Litres)"
        },
        text_auto=".3s"
    )

    zone_chart.update_layout(
        title="Historical Water Consumption by Zone",
        showlegend=False
    )

    zone_chart.update_traces(
        hovertemplate=(
            "Zone: %{x}<br>"
            "Consumption: %{y:,.0f} L"
            "<extra></extra>"
        )
    )

    zone_chart = style_chart(zone_chart)

else:

    zone_chart = empty_chart(
        "Zone-wise historical data is unavailable."
    )


# ============================================================
# 11. CAMPUS FORECAST CHART
# ============================================================

if not campus_forecast_df.empty:

    forecast_chart = go.Figure()

    forecast_chart.add_trace(
        go.Scatter(
            x=campus_forecast_df["timestamp"],
            y=campus_forecast_df["predicted_demand_liters"],
            mode="lines+markers",
            name="Predicted Demand",
            line=dict(
                color="#38bdf8",
                width=3
            ),
            marker=dict(size=5),
            hovertemplate=(
                "Time: %{x|%d %b %Y, %H:%M}<br>"
                "Predicted: %{y:,.2f} L"
                "<extra></extra>"
            )
        )
    )

    forecast_chart.update_layout(
        title="Saved Campus Water Demand Forecast",
        xaxis_title="Forecast Time",
        yaxis_title="Predicted Demand (Litres)",
        hovermode="x unified"
    )

    forecast_chart = style_chart(forecast_chart)

else:

    forecast_chart = empty_chart(
        "Saved campus forecast is unavailable."
    )


# ============================================================
# 12. ZONE FORECAST TABLE
# ============================================================

if not zone_forecast.empty:

    forecast_table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Campus Zone"),
                        html.Th(
                            "Forecast (L)",
                            className="text-end"
                        )
                    ]
                )
            ),

            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(
                                str(row["zone"]).title()
                            ),

                            html.Td(
                                f'{row["predicted_demand_liters"]:,.2f}',
                                className="text-end"
                            )
                        ]
                    )
                    for _, row in zone_forecast.iterrows()
                ]
            )
        ],
        striped=True,
        bordered=False,
        hover=True,
        responsive=True,
        class_name="overview-table"
    )

else:

    forecast_table = dbc.Alert(
        "Zone forecast data is unavailable.",
        color="secondary",
        className="mb-0"
    )


# ============================================================
# 13. FORECAST PERIOD DESCRIPTION
# ============================================================

if forecast_start is not None and forecast_end is not None:

    forecast_period_text = (
        f"{format_date(forecast_start, '%d %b %Y, %H:%M')} "
        f"to {format_date(forecast_end, '%d %b %Y, %H:%M')}"
    )

    forecast_description = (
        f"{forecast_hours} forecast time points"
    )

else:

    forecast_period_text = "Forecast period unavailable"
    forecast_description = "No saved forecast available"


# ============================================================
# 14. HISTORICAL DATA PERIOD DESCRIPTION
# ============================================================

if historical_start is not None and historical_end is not None:

    historical_period_text = (
        f"Historical data: "
        f"{format_date(historical_start)} to "
        f"{format_date(historical_end, '%d %b %Y, %H:%M')}"
    )

else:

    historical_period_text = (
        "Historical data is currently unavailable."
    )


# ============================================================
# 15. OVERVIEW PAGE LAYOUT
# ============================================================

layout = dbc.Container(
    [

        # ----------------------------------------------------
        # PAGE HEADER
        # ----------------------------------------------------

        html.Div(
            [
                html.Div(
                    [
                        html.H3(
                            "Campus Water Overview",
                            className="overview-page-title"
                        ),

                        html.P(
                            "Monitor historical campus water "
                            "consumption and review saved AI "
                            "demand forecasts across campus zones.",
                            className="overview-page-description"
                        )
                    ]
                ),

                dbc.Badge(
                    "HISTORICAL DATA + SAVED FORECAST",
                    color="info",
                    className="overview-data-badge"
                )
            ],
            className="overview-page-header"
        ),

        # ----------------------------------------------------
        # PROTOTYPE NOTICE
        # ----------------------------------------------------

        dbc.Alert(
            [
                html.Strong("Prototype Notice: "),
                "This page displays historical synthetic campus "
                "data and previously generated forecasting results. "
                "It is not connected to physical sensors, pumps, "
                "or valve controls."
            ],
            color="info",
            className="overview-notice"
        ),

        # ----------------------------------------------------
        # KPI CARDS
        # ----------------------------------------------------

        dbc.Row(
            [
                dbc.Col(
                    create_kpi_card(
                        "TOTAL HISTORICAL DEMAND",
                        format_liters(total_demand),
                        (
                            f"{format_date(historical_start)} "
                            f"to {format_date(historical_end)}"
                            if historical_start is not None
                            else "Historical data unavailable"
                        ),
                        "L"
                    ),
                    xs=12,
                    sm=6,
                    xl=3
                ),

                dbc.Col(
                    create_kpi_card(
                        "AVERAGE HOURLY DEMAND",
                        format_liters(average_hourly_demand),
                        "Average campus demand per hour",
                        "H"
                    ),
                    xs=12,
                    sm=6,
                    xl=3
                ),

                dbc.Col(
                    create_kpi_card(
                        "CAMPUS ZONES",
                        str(total_zones),
                        "Zones found in historical data",
                        "Z"
                    ),
                    xs=12,
                    sm=6,
                    xl=3
                ),

                dbc.Col(
                    create_kpi_card(
                        "SAVED FORECAST TOTAL",
                        format_liters(forecast_total),
                        forecast_description,
                        "F"
                    ),
                    xs=12,
                    sm=6,
                    xl=3
                )
            ],
            className="g-3 overview-kpi-row"
        ),

        # ----------------------------------------------------
        # HISTORICAL DEMAND AND ZONE CHARTS
        # ----------------------------------------------------

        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    figure=historical_chart,
                                    config={
                                        "displayModeBar": False,
                                        "responsive": True
                                    },
                                    responsive=True,
                                    style={"width": "100%"}
                                )
                            ]
                        ),
                        className="overview-chart-card h-100"
                    ),
                    xs=12,
                    xl=8
                ),

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    figure=zone_chart,
                                    config={
                                        "displayModeBar": False,
                                        "responsive": True
                                    },
                                    responsive=True,
                                    style={"width": "100%"}
                                )
                            ]
                        ),
                        className="overview-chart-card h-100"
                    ),
                    xs=12,
                    xl=4
                )
            ],
            className="g-3 overview-chart-row"
        ),

        # ----------------------------------------------------
        # FORECAST CHART AND ZONE TABLE
        # ----------------------------------------------------

        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    figure=forecast_chart,
                                    config={
                                        "displayModeBar": False,
                                        "responsive": True
                                    },
                                    responsive=True,
                                    style={"width": "100%"}
                                )
                            ]
                        ),
                        className="overview-chart-card h-100"
                    ),
                    xs=12,
                    xl=8
                ),

                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                "Saved Zone Forecast"
                            ),

                            dbc.CardBody(
                                [
                                    forecast_table,

                                    html.P(
                                        f"Forecast period: "
                                        f"{forecast_period_text}",
                                        className="overview-period-note"
                                    )
                                ]
                            )
                        ],
                        className="overview-chart-card h-100"
                    ),
                    xs=12,
                    xl=4
                )
            ],
            className="g-3 overview-chart-row"
        ),

        # ----------------------------------------------------
        # DATA SOURCE INFORMATION
        # ----------------------------------------------------

        html.Div(
            [
                html.Span(historical_period_text),

                html.Span(" | "),

                html.Span(
                    "Source: campus_water_demand.csv"
                )
            ],
            className="overview-source-note"
        )

    ],
    fluid=True,
    className="dashboard-content overview-container"
)