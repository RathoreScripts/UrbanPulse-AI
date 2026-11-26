
"""
UrbanPulse AI - Main Plotly Dash Application

Main entry point for the UrbanPulse dashboard.
The original Streamlit application remains untouched.
"""

from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc

from dashboard.pages import overview, live


# ============================================================
# 1. APPLICATION CONFIGURATION
# ============================================================

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="UrbanPulse AI | Campus Water Intelligence",
    suppress_callback_exceptions=True
)

server = app.server


# ============================================================
# 2. SIDEBAR NAVIGATION
# ============================================================

sidebar = html.Div(
    [
        html.Div(
            [
                html.Div("UP", className="brand-icon"),

                html.Div(
                    [
                        html.H5(
                            "UrbanPulse AI",
                            className="brand-title"
                        ),

                        html.P(
                            "CAMPUS WATER INTELLIGENCE",
                            className="brand-subtitle"
                        )
                    ]
                )
            ],
            className="brand-container"
        ),

        html.Hr(className="sidebar-divider"),

        html.P("MAIN MENU", className="menu-heading"),

        dbc.Nav(
            [
                dbc.NavLink(
                    "Overview",
                    href="/",
                    active="exact"
                ),

                dbc.NavLink(
                    "Live Operations",
                    href="/live",
                    active="exact"
                ),

                dbc.NavLink(
                    "Demand Monitoring",
                    href="/demand",
                    active="exact"
                ),

                dbc.NavLink(
                    "AI Forecasting",
                    href="/forecasting",
                    active="exact"
                ),

                dbc.NavLink(
                    "Hydraulic Network",
                    href="/hydraulic",
                    active="exact"
                ),

                dbc.NavLink(
                    "Scenario Analysis",
                    href="/scenarios",
                    active="exact"
                ),

                dbc.NavLink(
                    "Water Optimization",
                    href="/optimization",
                    active="exact"
                ),

                dbc.NavLink(
                    "Reports",
                    href="/reports",
                    active="exact"
                )
            ],
            vertical=True,
            pills=True,
            className="sidebar-nav"
        ),

        html.Div(
            [
                html.Div(className="status-dot"),

                html.Span(
                    "Simulation Mode",
                    className="status-text"
                )
            ],
            className="sidebar-status"
        )
    ],
    className="sidebar"
)


# ============================================================
# 3. MAIN CONTENT HEADER
# ============================================================

header = html.Div(
    [
        html.Div(
            [
                html.P(
                    "CAMPUS WATER MANAGEMENT SYSTEM",
                    className="header-eyebrow"
                ),

                html.H4(
                    "Water Intelligence Dashboard",
                    className="header-title"
                )
            ]
        ),

        html.Div(
            [
                html.Span(
                    "●",
                    className="prototype-dot"
                ),

                html.Span(
                    "Simulation Mode",
                    className="prototype-label"
                )
            ],
            className="header-status"
        )
    ],
    className="top-header"
)


# ============================================================
# 4. MAIN APPLICATION LAYOUT
# ============================================================

app.layout = html.Div(
    [
        dcc.Location(
            id="url",
            refresh=False
        ),

        sidebar,

        html.Div(
            [
                header,

                html.Div(
                    id="page-content",
                    children=overview.layout
                ),

                html.Footer(
                    [
                        html.Span("UrbanPulse AI"),
                        html.Span(" | "),
                        html.Span("Final Year B.Tech Project"),
                        html.Span(" | "),
                        html.Span("Synthetic Data Prototype")
                    ],
                    className="dashboard-footer"
                )
            ],
            className="main-container"
        )
    ],
    className="app-wrapper"
)


# ============================================================
# 5. PAGE ROUTING
# ============================================================

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):

    if pathname == "/":
        return overview.layout

    elif pathname == "/live":
        return live.layout

    elif pathname in [
        "/demand",
        "/forecasting",
        "/hydraulic",
        "/scenarios",
        "/optimization",
        "/reports"
    ]:

        return dbc.Container(
            [
                html.H3(
                    "Module Under Development",
                    className="overview-page-title"
                ),

                html.P(
                    "This module will be integrated using "
                    "the existing UrbanPulse project data "
                    "and simulation outputs.",
                    className="overview-page-description"
                ),

                dbc.Button(
                    "Return to Overview",
                    href="/",
                    color="success",
                    className="mt-3"
                )
            ],
            fluid=True,
            className="dashboard-content"
        )

    else:

        return dbc.Container(
            [
                html.H3("Page Not Found"),

                dbc.Button(
                    "Go to Overview",
                    href="/",
                    color="success"
                )
            ],
            className="dashboard-content"
        )


# ============================================================
# 6. APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=8050,
        debug=True
    )
