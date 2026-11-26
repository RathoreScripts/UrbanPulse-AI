
import networkx as nx

from src.urbanpulse.network import (
    build_network,
    load_network_config
)


def validate_network():

    graph, config = build_network()

    errors = []
    warnings = []

    node_ids = [
        node["id"]
        for node in config["nodes"]
    ]

    pipe_ids = [
        pipe["id"]
        for pipe in config["pipes"]
    ]

    # 1. Check duplicate node IDs
    if len(node_ids) != len(set(node_ids)):
        errors.append("Duplicate node IDs found.")

    # 2. Check duplicate pipe IDs
    if len(pipe_ids) != len(set(pipe_ids)):
        errors.append("Duplicate pipe IDs found.")

    # 3. Check pipe endpoints
    for pipe in config["pipes"]:

        if pipe["from"] not in graph.nodes:
            errors.append(
                f"Unknown start node in {pipe['id']}"
            )

        if pipe["to"] not in graph.nodes:
            errors.append(
                f"Unknown end node in {pipe['id']}"
            )

        if pipe["length_m"] <= 0:
            errors.append(
                f"Invalid pipe length: {pipe['id']}"
            )

        if pipe["diameter_mm"] <= 0:
            errors.append(
                f"Invalid pipe diameter: {pipe['id']}"
            )

    # 4. Check network connectivity
    connected = nx.is_connected(graph)

    if not connected:
        errors.append("Network contains disconnected nodes.")

    # 5. Check node types
    node_types = [
        node["type"]
        for node in config["nodes"]
    ]

    for required in ["reservoir", "pump", "tank", "demand_zone"]:
        if required not in node_types:
            errors.append(
                f"Missing required node type: {required}"
            )

    # 6. Check number of demand zones
    zones = [
        node for node in config["nodes"]
        if node["type"] == "demand_zone"
    ]

    if len(zones) != 5:
        warnings.append(
            f"Expected 5 zones, found {len(zones)}"
        )

    # 7. Check ring-main structure
    ring_nodes = ["TANK1", "J1", "J2", "J3", "J4", "J5"]

    ring_exists = all(
        graph.has_edge(
            ring_nodes[i],
            ring_nodes[(i + 1) % len(ring_nodes)]
        )
        for i in range(len(ring_nodes))
    )

    if not ring_exists:
        errors.append("Main ring connection is incomplete.")

    # 8. Summary
    results = {
        "total_nodes": graph.number_of_nodes(),
        "total_pipes": graph.number_of_edges(),
        "connected": connected,
        "ring_main_valid": ring_exists,
        "total_demand_zones": len(zones),
        "errors": errors,
        "warnings": warnings,
        "status": "PASS" if not errors else "FAILED"
    }

    return results


def print_network_report(results):

    print("\n" + "=" * 55)
    print("       URBANPULSE AI - NETWORK VALIDATION")
    print("=" * 55)

    for key, value in results.items():

        print(f"{key.replace('_', ' ').title()}: {value}")

    print("=" * 55)


if __name__ == "__main__":

    results = validate_network()

    print_network_report(results)
