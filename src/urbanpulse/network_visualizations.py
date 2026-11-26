
import plotly.graph_objects as go

from src.urbanpulse.network import build_network


def create_network_map():

    graph, config = build_network()

    fig = go.Figure()

    # ---------------------------------
    # PIPE CONNECTIONS
    # ---------------------------------

    for u, v, data in graph.edges(data=True):

        x1 = graph.nodes[u]["x"]
        y1 = graph.nodes[u]["y"]

        x2 = graph.nodes[v]["x"]
        y2 = graph.nodes[v]["y"]

        fig.add_trace(
            go.Scatter(
                x=[x1, x2],
                y=[y1, y2],
                mode="lines",
                line=dict(
                    color="#2586C7",
                    width=4
                ),
                hovertemplate=(
                    f"Pipe: {data['pipe_id']}<br>"
                    f"Length: {data['length_m']} m<br>"
                    f"Diameter: {data['diameter_mm']} mm"
                    "<extra></extra>"
                ),
                showlegend=False
            )
        )

    # ---------------------------------
    # NODE TYPES
    # ---------------------------------

    styles = {
        "reservoir": {
            "color": "#1689D4",
            "symbol": "square",
            "size": 24
        },
        "pump": {
            "color": "#E58B24",
            "symbol": "diamond",
            "size": 24
        },
        "tank": {
            "color": "#16A36A",
            "symbol": "square",
            "size": 28
        },
        "junction": {
            "color": "#8A63C7",
            "symbol": "circle",
            "size": 17
        },
        "demand_zone": {
            "color": "#D44F58",
            "symbol": "circle",
            "size": 22
        }
    }

    for node_type, style in styles.items():

        nodes = [
            (node_id, data)
            for node_id, data in graph.nodes(data=True)
            if data["type"] == node_type
        ]

        if not nodes:
            continue

        x_values = [
            data["x"] for _, data in nodes
        ]

        y_values = [
            data["y"] for _, data in nodes
        ]

        labels = [
            data["name"] for _, data in nodes
        ]

        ids = [
            node_id for node_id, _ in nodes
        ]

        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="markers+text",
                text=labels,
                textposition="top center",
                customdata=ids,
                marker=dict(
                    size=style["size"],
                    color=style["color"],
                    symbol=style["symbol"],
                    line=dict(
                        color="white",
                        width=1
                    )
                ),
                name=node_type.replace("_", " ").title(),
                hovertemplate=(
                    "Node: %{customdata}<br>"
                    "Name: %{text}<extra></extra>"
                )
            )
        )

    # ---------------------------------
    # MAP LAYOUT
    # ---------------------------------

    fig.update_layout(
        title={
            "text": (
                "UrbanPulse AI - "
                "Virtual Campus Water Distribution Network"
            ),
            "x": 0.5
        },
        xaxis=dict(
            title="Conceptual X Position",
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            title="Conceptual Y Position",
            showgrid=True,
            zeroline=False,
            scaleanchor="x",
            scaleratio=1
        ),
        template="plotly_white",
        height=700,
        hovermode="closest",
        legend=dict(
            title="Network Components",
            orientation="h",
            y=-0.18
        ),
        annotations=[
            dict(
                x=0.5,
                y=-0.27,
                xref="paper",
                yref="paper",
                text=(
                    "Conceptual network diagram | "
                    "Not an actual surveyed campus map"
                ),
                showarrow=False,
                font=dict(size=11, color="gray")
            )
        ],
        margin=dict(
            l=50,
            r=50,
            t=90,
            b=120
        )
    )

    return fig


def save_network_map():

    fig = create_network_map()

    output_path = (
        "artifacts/reports/plots/"
        "campus_network_2d.html"
    )

    import os

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True
    )

    fig.write_html(
        output_path,
        include_plotlyjs=True
    )

    print("\n2D engineering map generated!")
    print(f"Saved at: {output_path}")

    return output_path
