import { useMemo, useState } from "react";
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap } from "react-leaflet";
import L from "leaflet";


function FitToRoute(props) {
  const map = useMap();
  const points = props.points;

  if (!points || points.length === 0) return null;

  map.fitBounds(L.latLngBounds(points), { padding: [30, 30] });
  return null;
}

export default function App() {

  const [serverRouteLatLong, setServerRouteLatLong] = useState([]);
  const [startPos, setStartPos] = useState(null);
  const [endPos, setEndPos] = useState(null);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [avoidText, setAvoidText] = useState("");
  const [routingLog, SetRoutingLog] = useState("");
  const avoidList = useMemo(function () {
    return avoidText
      .split("\n")
      .map(function (s) {
        return s.trim();
      })
      .filter(Boolean);
  }, [avoidText]);

  async function handleRoute() {
    if (start.trim() === "" || end.trim() === "") {
      alert("Start and Destination Addresses cannot be empty, please try again.");
      return;
    }
    SetRoutingLog("");
    const payload = {
      start_address: start, destination_address: end, avoid: avoidList
    }
    SetRoutingLog("Routing in progress....");
    console.log("Route payload:", payload);

    try {
      const response = await fetch("/api/find_route", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload), });
      //clearForm();
      const data = await response.json();
      console.log(data);

      if (!response.ok || !data.success) {
        alert(data.error || "Backend failed");
        return;
      }
      const coords = data.route.geometry.coordinates;
      setServerRouteLatLong(coords);
      setStartPos(coords[0]);
      setEndPos(coords[coords.length - 1]);
      SetRoutingLog(data.log || "");

    }

    catch (err) {
      console.log(err);
      alert("error occurred.")
    }
  }

  function clearForm() {
    setStart("");
    setEnd("");
    setAvoidText("");
    setServerRouteLatLong([]);
    setStartPos(null);
    setEndPos(null);
  }


  function handleClear() {
    clearForm();
    alert("All fields have been cleared.");
  }

  return (
    <div style={{ height: "100vh", width: "100vw", display: "flex" }}>
      <div
        style={{
          width: "50%",
          backgroundColor: "#e9efe6e2",
          padding: 24,
          overflowY: "auto",
          boxSizing: "border-box",
          fontFamily: "system-ui",
        }}
      >
        <div style={{ maxWidth: 700, margin: "40px auto" }}>
          <h1>OttawaNoGoRouter</h1>

          <label style={{ display: "block", marginTop: 12, fontWeight: 600 }}>
            Start Address
          </label>
          <input
            value={start}
            onChange={function (e) {
              setStart(e.target.value);
            }}
            placeholder="Example: 1125 Colonel By Dr"
            style={{ width: "100%", padding: 10, boxSizing: "border-box" }}
          />

          <label style={{ display: "block", marginTop: 12, fontWeight: 600 }}>
            Destination Address
          </label>
          <input
            value={end}
            onChange={function (e) {
              setEnd(e.target.value);
            }}
            placeholder="Example: 75 Laurier Avenue East"
            style={{ width: "100%", padding: 10, boxSizing: "border-box" }}
          />

          <label style={{ display: "block", marginTop: 12, fontWeight: 600 }}>
            Avoid streets (one per line)
          </label>
          <textarea
            value={avoidText}
            onChange={function (e) {
              setAvoidText(e.target.value);
            }}
            placeholder={"Example: Bank St\nRideau St\nQueensway"}
            rows={6}
            style={{ width: "100%", padding: 10, boxSizing: "border-box" }}
          />

          <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
            <button onClick={handleRoute} style={{ padding: "10px 12px" }}>
              Route (log payload)
            </button>
            <button onClick={handleClear} style={{ padding: "10px 12px" }}>
              Clear
            </button>
          </div>

          <div style={{ marginTop: 18 }}>
            <div style={{ fontWeight: 700 }}>
              Avoid list preview ({avoidList.length})
            </div>
            {avoidList.length === 0 ? (
              <p style={{ color: "#666" }}>Nothing to avoid yet.</p>
            ) : (
              <ul>
                {avoidList.map(function (street) {
                  return <li key={street}>{street}</li>;
                })}
              </ul>
            )}
          </div>
          <p style={{ color: "#480606ff" }}>
            {routingLog} </p>
          <hr style={{ margin: "24px 0" }} />


          <p>Amirali Madani, 2025</p>
        </div>
      </div>

      <div style={{ flex: 1 }}>
        <MapContainer
          center={[45.4215, -75.6972]}
          zoom={13}
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {serverRouteLatLong.length > 0 ? (
            <>
              <FitToRoute points={serverRouteLatLong} />

              <Polyline
                positions={serverRouteLatLong}
                pathOptions={{ weight: 5, opacity: 0.8 }}
              />

              <CircleMarker center={startPos} radius={6} pathOptions={{ weight: 3 }}>
                <Popup>Start</Popup>
              </CircleMarker>

              <CircleMarker center={endPos} radius={6} pathOptions={{ weight: 3 }}>
                <Popup>End</Popup>
              </CircleMarker>
            </>
          ) : null}

        </MapContainer>
      </div>
    </div>
  );
}
