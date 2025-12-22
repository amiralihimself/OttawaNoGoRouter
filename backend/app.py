from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/api/find_route")
def find_route():
    """
    Expects JSON like:
    {
      "start": "1125 Colonel By Dr",
      "end": "75 Laurier Avenue East",
      "avoid": ["Bank St", "Rideau St"]
    }
    """
    data = request.get_json(silent=True) or {}
    start = (data.get("start") or "").strip()
    end = (data.get("end") or "").strip()
    avoid = data.get("avoid") or []

    if not start or not end:
        return jsonify({"error": "start and end are required"}), 400

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
            "start": start,
            "end": end,
            "avoid_count": len(avoid),
        },
    }

    return jsonify({"route": dummy_geojson})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
