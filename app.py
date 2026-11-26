
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# URBANPULSE AI - CAMPUS WATER MANAGEMENT DASHBOARD
# ============================================================

st.set_page_config(
    page_title="UrbanPulse AI | Water Management",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "artifacts" / "reports"

FORECAST_DIR = REPORTS_DIR / "forecasting"
HYDRAULIC_DIR = REPORTS_DIR / "hydraulic"
SCENARIO_DIR = REPORTS_DIR / "scenario_analysis"
SCENARIOS_DIR = REPORTS_DIR / "scenarios"
OPTIMIZATION_DIR = REPORTS_DIR / "optimization"

# Dashboard styling
st.markdown("""
<style>
    .main {
        background-color: #f5f8fc;
    }
    .block-container {
        padding-top: 1.5rem;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #12304a;
    }
    .subtitle {
        color: #60758a;
        font-size: 1rem;
    }
    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e2eaf2;
        padding: 16px;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

@st.cache_data
def load_csv(file_path):
    """Load a CSV file safely."""
    path = Path(file_path)

    if not path.exists():
        return None

    try:
        return pd.read_csv(path)
    except Exception:
        return None


def show_missing(message):
    st.info(message)


def first_existing_column(df, candidates):
    """Find the first matching column name."""
    if df is None:
        return None

    for candidate in candidates:
        if candidate in df.columns:
            return candidate

    return None


def numeric_columns(df, exclude=None):
    """Return numeric columns, excluding selected columns."""
    if df is None:
        return []

    exclude = exclude or []
    return [
        col for col in df.select_dtypes(include="number").columns
        if col not in exclude
    ]


def prepare_time_column(df):
    """Convert a likely timestamp column to datetime."""
    if df is None or df.empty:
        return df

    time_col = first_existing_column(
        df,
        ["timestamp", "datetime", "date", "time"]
    )

    if time_col:
        df = df.copy()
        df[time_col] = pd.to_datetime(
            df[time_col], errors="coerce"
        )

    return df


def format_liters(value):
    if pd.isna(value):
        return "N/A"

    return f"{value:,.0f} L"


def display_download_button(file_path, label):
    """Show a download button if a file exists."""
    path = Path(file_path)

    if path.exists() and path.is_file():
        try:
            with open(path, "rb") as file:
                st.download_button(
                    label=label,
                    data=file.read(),
                    file_name=path.name,
                    mime="text/csv" if path.suffix.lower() == ".csv"
                    else "text/plain",
                    key=f"download_{str(path)}"
                )
        except Exception:
            st.warning(f"Could not read {path.name}.")


def display_data_table(df):
    if df is not None and not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        show_missing("No data is available in this file yet.")


def show_file_status():
    files = {
        "Forecast": FORECAST_DIR / "next_24_hour_forecast.csv",
        "Hydraulic pressure": HYDRAULIC_DIR / "node_pressure.csv",
        "Scenario comparison": SCENARIO_DIR / "scenario_comparison.csv",
        "Optimization summary": OPTIMIZATION_DIR / "zone_allocation_summary.csv",
    }

    for name, path in files.items():
        if path.exists():
            st.success(f"{name}: Available")
        else:
            st.warning(f"{name}: File not found")


# ============================================================
# LOAD PROJECT DATA
# ============================================================

forecast_df = load_csv(
    FORECAST_DIR / "next_24_hour_forecast.csv"
)

forecast_metrics_df = load_csv(
    FORECAST_DIR / "model_comparison_metrics.csv"
)

campus_forecast_df = load_csv(
    FORECAST_DIR / "campus_total_forecast.csv"
)

pressure_df = load_csv(
    HYDRAULIC_DIR / "node_pressure.csv"
)

tank_df = load_csv(
    HYDRAULIC_DIR / "tank_level.csv"
)

flow_df = load_csv(
    HYDRAULIC_DIR / "pipe_flowrate.csv"
)

velocity_df = load_csv(
    HYDRAULIC_DIR / "pipe_velocity.csv"
)

scenario_comparison_df = load_csv(
    SCENARIO_DIR / "scenario_comparison.csv"
)

scenario_summary_df = load_csv(
    SCENARIOS_DIR / "all_scenarios_summary.csv"
)

allocation_df = load_csv(
    OPTIMIZATION_DIR / "hourly_water_allocation.csv"
)

allocation_summary_df = load_csv(
    OPTIMIZATION_DIR / "zone_allocation_summary.csv"
)

allocation_totals_df = load_csv(
    OPTIMIZATION_DIR / "hourly_allocation_totals.csv"
)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:
    st.title("💧 UrbanPulse AI")
    st.caption("Smart Campus Water Management")

    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Overview",
            "AI Forecasting",
            "Hydraulic Simulation",
            "Scenario Analysis",
            "Water Optimization",
            "Reports"
        ]
    )

    st.divider()

    st.caption("Project: UrbanPulse AI")
    st.caption("Final Year B.Tech Project")
    st.caption("Software-based decision support system")


# ============================================================
# COMMON HEADER
# ============================================================

st.markdown(
    '<div class="main-title">💧 UrbanPulse AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-Powered Campus Water Management and Digital Twin Dashboard'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# ============================================================
# PAGE 1: OVERVIEW
# ============================================================

if page == "Overview":

    st.subheader("Campus Water Management Overview")

    st.write(
        "Monitor synthetic campus water demand, forecasted demand, "
        "water allocation and simulated system performance."
    )

    total_demand = None
    total_allocated = None
    total_unmet = None
    shortage_percent = None

    if allocation_summary_df is not None and not allocation_summary_df.empty:
        demand_col = first_existing_column(
            allocation_summary_df,
            ["predicted_demand_liters", "total_demand_liters"]
        )

        allocated_col = first_existing_column(
            allocation_summary_df,
            ["allocated_water_liters", "total_allocated_liters"]
        )

        unmet_col = first_existing_column(
            allocation_summary_df,
            ["unmet_demand_liters", "total_unmet_demand_liters"]
        )

        if demand_col:
            total_demand = pd.to_numeric(
                allocation_summary_df[demand_col], errors="coerce"
            ).sum()

        if allocated_col:
            total_allocated = pd.to_numeric(
                allocation_summary_df[allocated_col], errors="coerce"
            ).sum()

        if unmet_col:
            total_unmet = pd.to_numeric(
                allocation_summary_df[unmet_col], errors="coerce"
            ).sum()

    if total_demand is None and allocation_totals_df is not None:
        demand_col = first_existing_column(
            allocation_totals_df,
            ["total_demand_liters"]
        )
        allocated_col = first_existing_column(
            allocation_totals_df,
            ["total_allocated_liters"]
        )
        unmet_col = first_existing_column(
            allocation_totals_df,
            ["total_unmet_demand_liters"]
        )

        if demand_col:
            total_demand = pd.to_numeric(
                allocation_totals_df[demand_col], errors="coerce"
            ).sum()

        if allocated_col:
            total_allocated = pd.to_numeric(
                allocation_totals_df[allocated_col], errors="coerce"
            ).sum()

        if unmet_col:
            total_unmet = pd.to_numeric(
                allocation_totals_df[unmet_col], errors="coerce"
            ).sum()

    if total_demand is not None and total_demand > 0 and total_unmet is not None:
        shortage_percent = (total_unmet / total_demand) * 100

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Predicted Water Demand",
            format_liters(total_demand)
        )

    with col2:
        st.metric(
            "Allocated Water",
            format_liters(total_allocated)
        )

    with col3:
        st.metric(
            "Unmet Demand",
            format_liters(total_unmet)
        )

    with col4:
        st.metric(
            "Water Shortage",
            f"{shortage_percent:.2f}%"
            if shortage_percent is not None else "N/A"
        )

    st.divider()

    st.subheader("Zone-wise Water Demand")

    if allocation_summary_df is not None and not allocation_summary_df.empty:
        zone_col = first_existing_column(
            allocation_summary_df, ["zone"]
        )
        demand_col = first_existing_column(
            allocation_summary_df,
            ["predicted_demand_liters", "total_demand_liters"]
        )

        if zone_col and demand_col:
            fig = px.bar(
                allocation_summary_df,
                x=zone_col,
                y=demand_col,
                color=zone_col,
                title="Predicted Water Demand by Campus Zone",
                labels={
                    zone_col: "Campus Zone",
                    demand_col: "Demand (Liters)"
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            display_data_table(allocation_summary_df)
    else:
        show_missing(
            "Zone allocation summary not found. "
            "Run the water optimization script first."
        )

    st.subheader("Project Data Status")
    show_file_status()

    st.info(
        "Important: This dashboard currently displays results generated "
        "from synthetic demand data and conceptual network assumptions. "
        "It is a software decision-support prototype, not a live campus "
        "monitoring or pump-control system."
    )


# ============================================================
# PAGE 2: AI FORECASTING
# ============================================================

elif page == "AI Forecasting":

    st.subheader("🤖 AI Water Demand Forecasting")

    st.write(
        "Compare forecasting model performance and view the next "
        "24-hour predicted water demand for each campus zone."
    )

    if forecast_df is not None and not forecast_df.empty:

        forecast_df = prepare_time_column(forecast_df)

        zone_col = first_existing_column(forecast_df, ["zone"])
        time_col = first_existing_column(
            forecast_df, ["timestamp", "datetime", "date", "time"]
        )
        prediction_col = first_existing_column(
            forecast_df,
            ["predicted_demand_liters", "predicted_demand", "demand_liters"]
        )

        if zone_col and prediction_col:

            if time_col:
                fig = px.line(
                    forecast_df,
                    x=time_col,
                    y=prediction_col,
                    color=zone_col,
                    markers=True,
                    title="Next 24-Hour Water Demand Forecast",
                    labels={
                        time_col: "Time",
                        prediction_col: "Predicted Demand (Liters)",
                        zone_col: "Campus Zone"
                    }
                )
            else:
                fig = px.bar(
                    forecast_df,
                    x=zone_col,
                    y=prediction_col,
                    color=zone_col,
                    title="Predicted Water Demand by Zone"
                )

            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Forecast Data")
            display_data_table(forecast_df)

        else:
            st.warning(
                "The forecast file does not contain the expected "
                "zone and predicted demand columns."
            )
            display_data_table(forecast_df)

    else:
        show_missing(
            "Forecast file not found. Run "
            "`python -m scripts.run_forecasting` first."
        )

    st.divider()

    st.subheader("Forecasting Model Performance")

    if forecast_metrics_df is not None and not forecast_metrics_df.empty:

        display_data_table(forecast_metrics_df)

        rmse_col = first_existing_column(
            forecast_metrics_df, ["RMSE", "rmse"]
        )
        model_col = first_existing_column(
            forecast_metrics_df, ["model", "Model"]
        )
        zone_col = first_existing_column(
            forecast_metrics_df, ["zone"]
        )

        if rmse_col and model_col:
            fig = px.bar(
                forecast_metrics_df,
                x=model_col,
                y=rmse_col,
                color=zone_col if zone_col else model_col,
                barmode="group",
                title="Forecasting Model RMSE Comparison",
                labels={rmse_col: "RMSE (lower is better)"}
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        show_missing("Forecasting model metrics file not found.")

    display_download_button(
        FORECAST_DIR / "next_24_hour_forecast.csv",
        "⬇️ Download 24-Hour Forecast CSV"
    )


# ============================================================
# PAGE 3: HYDRAULIC SIMULATION
# ============================================================

elif page == "Hydraulic Simulation":

    st.subheader("🌊 Virtual Campus Hydraulic Simulation")

    st.write(
        "Explore simulated water pressure, tank levels, "
        "pipe flow rates and pipe velocities."
    )

    if pressure_df is not None and not pressure_df.empty:

        pressure_df = prepare_time_column(pressure_df)

        st.markdown("#### Node Pressure")

        pressure_time_col = first_existing_column(
            pressure_df, ["timestamp", "datetime", "time", "date"]
        )

        pressure_value_cols = numeric_columns(
            pressure_df,
            exclude=[pressure_time_col] if pressure_time_col else []
        )

        if pressure_value_cols:

            # Remove reservoir/tank columns when displaying zone pressure.
            zone_pressure_cols = [
                col for col in pressure_value_cols
                if str(col).upper().startswith("Z")
            ]

            selected_cols = zone_pressure_cols or pressure_value_cols

            plot_df = pressure_df.copy()

            if pressure_time_col:
                plot_df = plot_df.melt(
                    id_vars=[pressure_time_col],
                    value_vars=selected_cols,
                    var_name="Node",
                    value_name="Pressure (m)"
                )

                fig = px.line(
                    plot_df,
                    x=pressure_time_col,
                    y="Pressure (m)",
                    color="Node",
                    title="Simulated Node Pressure"
                )
            else:
                plot_df = pressure_df[selected_cols].reset_index()
                plot_df = plot_df.melt(
                    id_vars=["index"],
                    var_name="Node",
                    value_name="Pressure (m)"
                )

                fig = px.line(
                    plot_df,
                    x="index",
                    y="Pressure (m)",
                    color="Node",
                    title="Simulated Node Pressure"
                )

            st.plotly_chart(fig, use_container_width=True)

        else:
            display_data_table(pressure_df)

    else:
        show_missing("Hydraulic pressure data not found.")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Tank Water Level")

        if tank_df is not None and not tank_df.empty:
            tank_df = prepare_time_column(tank_df)
            time_col = first_existing_column(
                tank_df, ["timestamp", "datetime", "time", "date"]
            )
            values = numeric_columns(
                tank_df, exclude=[time_col] if time_col else []
            )

            if values:
                fig = px.line(
                    tank_df,
                    x=time_col if time_col else tank_df.index,
                    y=values,
                    title="Simulated Tank Level"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                display_data_table(tank_df)
        else:
            show_missing("Tank level data not found.")

    with col2:
        st.markdown("#### Pipe Flow Rate")

        if flow_df is not None and not flow_df.empty:
            flow_df = prepare_time_column(flow_df)
            time_col = first_existing_column(
                flow_df, ["timestamp", "datetime", "time", "date"]
            )
            values = numeric_columns(
                flow_df, exclude=[time_col] if time_col else []
            )

            if values:
                fig = px.line(
                    flow_df,
                    x=time_col if time_col else flow_df.index,
                    y=values,
                    title="Simulated Pipe Flow Rate"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                display_data_table(flow_df)
        else:
            show_missing("Pipe flow data not found.")

    st.divider()

    st.markdown("#### Pipe Velocity")

    if velocity_df is not None and not velocity_df.empty:
        velocity_df = prepare_time_column(velocity_df)
        display_data_table(velocity_df)
    else:
        show_missing("Pipe velocity data not found.")

    st.info(
        "Hydraulic results are based on the project's conceptual network "
        "and assumed parameters. They are simulations, not verified "
        "measurements of the actual campus water network."
    )


# ============================================================
# PAGE 4: SCENARIO ANALYSIS
# ============================================================

elif page == "Scenario Analysis":

    st.subheader("⚠️ Water System Scenario Analysis")

    st.write(
        "Compare how different simulated operating conditions "
        "affect the virtual campus water network."
    )

    scenario_df = (
        scenario_comparison_df
        if scenario_comparison_df is not None
        else scenario_summary_df
    )

    if scenario_df is not None and not scenario_df.empty:

        st.markdown("#### Scenario Comparison Data")
        display_data_table(scenario_df)

        scenario_col = first_existing_column(
            scenario_df, ["scenario", "Scenario", "scenario_name"]
        )

        metric_candidates = [
            "minimum_zone_pressure_m",
            "min_zone_pressure_m",
            "average_zone_pressure_m",
            "avg_zone_pressure_m",
            "minimum_tank_level_m",
            "min_tank_level_m",
            "max_flow_m3_s"
        ]

        available_metrics = [
            col for col in metric_candidates if col in scenario_df.columns
        ]

        if scenario_col and available_metrics:

            selected_metric = st.selectbox(
                "Select a scenario performance metric",
                available_metrics
            )

            fig = px.bar(
                scenario_df,
                x=scenario_col,
                y=selected_metric,
                color=scenario_col,
                title=f"Scenario Comparison: {selected_metric}"
            )

            st.plotly_chart(fig, use_container_width=True)

        elif not scenario_col:
            st.caption(
                "Scenario name column was not detected. "
                "The available data is shown above."
            )

    else:
        show_missing(
            "Scenario comparison files not found. Run "
            "`python -m scripts.run_scenarios` and "
            "`python -m scripts.run_scenario_analysis` first."
        )

    st.divider()

    st.markdown("#### Scenario Types")

    scenario_descriptions = {
        "Normal": "Baseline virtual campus operating condition.",
        "Peak Demand": "Simulates an increase in campus water demand.",
        "Drought": "Simulates a reduction in reservoir supply head.",
        "Leakage": "Adds an assumed extra water discharge.",
        "Pipe Burst": "Simulates a larger extra water discharge.",
        "Water Conservation": "Reduces the assumed water demand.",
        "Pump Outage": "Simulates the pump being unavailable."
    }

    for name, description in scenario_descriptions.items():
        with st.expander(name):
            st.write(description)

    st.info(
        "Leakage and pipe-burst scenarios use simplified additional "
        "junction demand. They are not calibrated physical pipe-break models."
    )


# ============================================================
# PAGE 5: WATER OPTIMIZATION
# ============================================================

elif page == "Water Optimization":

    st.subheader("⚙️ Water Allocation Optimization")

    st.write(
        "View the optimized allocation of forecasted water demand "
        "across the five campus zones."
    )

    if allocation_summary_df is not None and not allocation_summary_df.empty:

        zone_col = first_existing_column(
            allocation_summary_df, ["zone"]
        )

        demand_col = first_existing_column(
            allocation_summary_df,
            ["predicted_demand_liters", "total_demand_liters"]
        )

        allocated_col = first_existing_column(
            allocation_summary_df,
            ["allocated_water_liters", "total_allocated_liters"]
        )

        unmet_col = first_existing_column(
            allocation_summary_df,
            ["unmet_demand_liters", "total_unmet_demand_liters"]
        )

        percentage_col = first_existing_column(
            allocation_summary_df,
            ["allocation_percentage"]
        )

        if demand_col and allocated_col and unmet_col and zone_col:

            chart_df = allocation_summary_df.melt(
                id_vars=[zone_col],
                value_vars=[demand_col, allocated_col, unmet_col],
                var_name="Water Metric",
                value_name="Liters"
            )

            fig = px.bar(
                chart_df,
                x=zone_col,
                y="Liters",
                color="Water Metric",
                barmode="group",
                title="Zone-wise Water Demand and Allocation"
            )

            st.plotly_chart(fig, use_container_width=True)

            if percentage_col:
                fig = px.bar(
                    allocation_summary_df,
                    x=zone_col,
                    y=percentage_col,
                    color=zone_col,
                    title="Zone-wise Allocation Percentage",
                    labels={
                        percentage_col: "Allocation (%)",
                        zone_col: "Campus Zone"
                    }
                )
                fig.update_yaxes(range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Zone-wise Allocation Summary")
        display_data_table(allocation_summary_df)

    else:
        show_missing(
            "Optimization summary not found. Run "
            "`python -m scripts.run_optimization` first."
        )

    st.divider()

    st.markdown("#### Hourly Allocation")

    if allocation_df is not None and not allocation_df.empty:
        display_data_table(allocation_df)

    else:
        show_missing("Hourly allocation data not found.")

    if allocation_totals_df is not None and not allocation_totals_df.empty:

        st.markdown("#### Hourly Supply Utilization")

        time_col = first_existing_column(
            allocation_totals_df,
            ["timestamp", "datetime", "time"]
        )

        available_cols = [
            col for col in [
                "total_demand_liters",
                "total_allocated_liters",
                "total_unmet_demand_liters",
                "available_supply_liters",
                "unused_supply_liters"
            ]
            if col in allocation_totals_df.columns
        ]

        if available_cols:
            fig = px.line(
                allocation_totals_df,
                x=time_col if time_col else allocation_totals_df.index,
                y=available_cols,
                title="Hourly Water Allocation and Supply"
            )
            st.plotly_chart(fig, use_container_width=True)

    st.info(
        "Allocation priorities, minimum allocation percentages and "
        "available supply are project assumptions. Optimization output "
        "is a decision-support result, not an official campus water policy."
    )


# ============================================================
# PAGE 6: REPORTS
# ============================================================

elif page == "Reports":

    st.subheader("📁 Project Reports and Downloads")

    st.write(
        "Download generated CSV datasets and text reports "
        "from the UrbanPulse AI project."
    )

    report_files = [
        (
            "Synthetic Campus Demand Dataset",
            BASE_DIR / "data" / "synthetic" / "campus_water_demand.csv"
        ),
        (
            "Data Validation Report",
            REPORTS_DIR / "data_validation_report.txt"
        ),
        (
            "Forecasting Results",
            FORECAST_DIR / "next_24_hour_forecast.csv"
        ),
        (
            "Forecasting Model Metrics",
            FORECAST_DIR / "model_comparison_metrics.csv"
        ),
        (
            "Hydraulic Node Pressure",
            HYDRAULIC_DIR / "node_pressure.csv"
        ),
        (
            "Hydraulic Tank Level",
            HYDRAULIC_DIR / "tank_level.csv"
        ),
        (
            "Hydraulic Pipe Flow Rate",
            HYDRAULIC_DIR / "pipe_flowrate.csv"
        ),
        (
            "Scenario Comparison",
            SCENARIO_DIR / "scenario_comparison.csv"
        ),
        (
            "All Scenario Results",
            SCENARIOS_DIR / "all_scenarios_summary.csv"
        ),
        (
            "Zone Allocation Summary",
            OPTIMIZATION_DIR / "zone_allocation_summary.csv"
        ),
        (
            "Hourly Water Allocation",
            OPTIMIZATION_DIR / "hourly_water_allocation.csv"
        ),
        (
            "Hourly Allocation Totals",
            OPTIMIZATION_DIR / "hourly_allocation_totals.csv"
        ),
        (
            "Optimization Report",
            OPTIMIZATION_DIR / "optimization_report.txt"
        )
    ]

    available_count = 0

    for label, file_path in report_files:
        if file_path.exists():
            available_count += 1

            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"📄 {label}")
                st.caption(file_path.name)

            with col2:
                display_download_button(
                    file_path,
                    "⬇️ Download"
                )

            st.divider()

    st.metric("Available Project Files", available_count)

    if available_count == 0:
        show_missing(
            "No report files were found. Complete the earlier "
            "project milestones to generate them."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#718096; padding:10px;">
        <b>UrbanPulse AI</b><br>
        AI-Powered Campus Water Management Digital Twin<br>
        <small>Academic prototype | Synthetic data | Decision support only</small>
    </div>
    """,
    unsafe_allow_html=True
)
