from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import ValidationError

from utils import OttawaGraphNetwork
from schemas import RouteRequest

app = Flask(__name__)
CORS(app)

OTTAWA_GRAPH_NETWORK: OttawaGraphNetwork = (
    OttawaGraphNetwork()
)  # loading up the ottawa road network


@app.get("/health")
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
    street_names_to_avoid = payload.avoid

    source_vertex, source_address_interpretation = (
        OTTAWA_GRAPH_NETWORK.get_closest_vertex_to_an_ottawa_address(start_address)
    )
    destination_vertex, destination_address_interpretation = (
        OTTAWA_GRAPH_NETWORK.get_closest_vertex_to_an_ottawa_address(
            destination_address
        )
    )

    street_names_to_avoid, edges_to_avoid = (
        OTTAWA_GRAPH_NETWORK.get_street_edges_to_avoid(street_names_to_avoid)
    )

    avoid = payload.avoid
    # TODO: replace this with real routing
    # For now, return a dummy polyline to prove plumbing works.
    dummy_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [-75, 45],
                [-76, 46],
            ],
        },
        "properties": {
            "start": start_address,
            "end": destination_address,
            "avoid_count": len(avoid),
        },
    }

    return (
        jsonify(
            {
                "success": True,
                "log": f"route computed (dummy) start='{source_address_interpretation}' end='{destination_address_interpretation}' avoid_count={len(avoid)}",
                "route": dummy_geojson,
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
