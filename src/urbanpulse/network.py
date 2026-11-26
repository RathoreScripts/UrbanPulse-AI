
import yaml
import networkx as nx

from src.urbanpulse.config import get_project_path


def load_network_config():

    config_path = get_project_path(
        "config/network_config.yaml"
    )

    if not config_path.exists():
        raise FileNotFoundError(
            f"Network config not found: {config_path}"
        )

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return config


def build_network():

    config = load_network_config()

    graph = nx.Graph()

    # Add nodes
    for node in config["nodes"]:

        graph.add_node(
            node["id"],
            name=node["name"],
            type=node["type"],
            x=node["x"],
            y=node["y"],
            zone=node.get("zone")
        )

    # Add pipes as edges
    for pipe in config["pipes"]:

        graph.add_edge(
            pipe["from"],
            pipe["to"],
            pipe_id=pipe["id"],
            length_m=pipe["length_m"],
            diameter_mm=pipe["diameter_mm"]
        )

    return graph, config


def get_network_summary(graph, config):

    return {
        "network_name": config["network"]["name"],
        "total_nodes": graph.number_of_nodes(),
        "total_pipes": graph.number_of_edges(),
        "total_pipe_length_m": sum(
            data["length_m"]
            for _, _, data in graph.edges(data=True)
        ),
        "total_zones": sum(
            1 for _, data in graph.nodes(data=True)
            if data["type"] == "demand_zone"
        ),
        "is_connected": nx.is_connected(graph)
    }
