from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import ValidationError

from routing_algorithms import RoutingWithContinuousDeletions
from utils import OttawaGraphNetwork
from schemas import RouteRequest

app = Flask(__name__)
CORS(app)

OTTAWA_GRAPH_NETWORK: OttawaGraphNetwork = (
    OttawaGraphNetwork()
)  # loading up the ottawa road network


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"success": True}


@app.post("/api/find_route")
def find_route():
    """
    Expects JSON like:
    {
      "start_address": "1125 Colonel By Dr",
      "destination_address": "75 Laurier Avenue East",
      "avoid": ["Bank St", "Rideau St"]
    }
    """
    data = request.get_json(silent=True) or {}
    try:
        payload = RouteRequest.model_validate(data)
    except ValidationError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "log": "validation failed for /api/find_route",
                    "error": "Invalid request payload",
                    "details": e.errors(),
                }
            ),
            400,
        )

    start_address = payload.start_address
    destination_address = payload.destination_address
    avoid = payload.avoid

    source_vertex, source_address_interpretation = (
        OTTAWA_GRAPH_NETWORK.get_closest_vertex_to_an_ottawa_address(start_address)
    )
    destination_vertex, destination_address_interpretation = (
        OTTAWA_GRAPH_NETWORK.get_closest_vertex_to_an_ottawa_address(
            destination_address
        )
    )

    street_names_to_avoid, edges_to_avoid = (
        OTTAWA_GRAPH_NETWORK.get_street_edges_to_avoid(avoid)
    )

    # The algorithm is now instantiated
    algorithm = RoutingWithContinuousDeletions(
        ottawa_road_network=OTTAWA_GRAPH_NETWORK.G,
        source_vertex=source_vertex,
        destination_vertex=destination_vertex,
        edges_to_avoid=edges_to_avoid,
        street_names_to_avoid=street_names_to_avoid,
    )

    path_edges, log = algorithm.find_route()
    path_nodes = [path_edges[0][0]] + [v for (_, v, _) in path_edges]
    path_coords = [
        (OTTAWA_GRAPH_NETWORK.G.nodes[n]["y"], OTTAWA_GRAPH_NETWORK.G.nodes[n]["x"])
        for n in path_nodes
    ]
    geojson = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": path_coords,
        },
        "properties": {
            "start": source_address_interpretation,
            "end": destination_address_interpretation,
            "avoid_count": len(avoid),
        },
    }

    return (
        jsonify(
            {
                "success": True,
                "log": log,
                "route": geojson,
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
