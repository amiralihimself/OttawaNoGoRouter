import { useMemo, useState } from "react";

export default function App() {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [avoidText, setAvoidText] = useState("");

  const avoidList = useMemo(() => {
    return avoidText
      .split("\n")          // split textarea into lines
      .map((s) => s.trim()) // remove surrounding spaces
      .filter(Boolean);     // remove empty lines
  }, [avoidText]);

  function handleRoute() {
    const payload = { start, end, avoid: avoidList };
    console.log("Route payload:", payload);
    alert(`Payload printed to console.\nAvoid count: ${avoidList.length}`);
  }

  function handleClear() {
    setStart("");
    setEnd("");
    setAvoidText("");
    alert("All fields have been cleared.")
  }

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#6fe5dbe3", padding: 24 }}>
      <div style={{ maxWidth: 700, margin: "40px auto", fontFamily: "system-ui" }}>
        <h1>OttawaNoGoRouter</h1>
        <label style={{ display: "block", marginTop: 12, fontWeight: 600 }}>
          Start Address
        </label>
        <input
          value={start}
          onChange={(e) => setStart(e.target.value)}
          placeholder="Example: 1125 Colonel By Dr,"
          style={{ width: "100%", padding: 10, boxSizing: "border-box" }}
        />

        <label style={{ display: "block", marginTop: 12, fontWeight: 600 }}>
          Destination Address
        </label>
        <input
          value={end}
          onChange={(e) => setEnd(e.target.value)}
          placeholder="Example: 75 Laurier Avenue East"
          style={{ width: "100%", padding: 10, boxSizing: "border-box" }}
        />

        <label style={{ display: "block", marginTop: 12, fontWeight: 600 }}>
          Avoid streets (one per line)
        </label>
        <textarea
          value={avoidText}
          onChange={(e) => setAvoidText(e.target.value)}
          placeholder={"Bank St\nRideau St\nQueensway"}
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
          <div style={{ fontWeight: 700 }}>Avoid list preview ({avoidList.length})</div>
          {avoidList.length === 0 ? (
            <p style={{ color: "#666" }}>Nothing to avoid yet.</p>
          ) : (
            <ul>
              {avoidList.map((street) => (
                <li key={street}>{street}</li>
              ))}
            </ul>
          )}
        </div>

        <hr style={{ margin: "24px 0" }} />

        <p style={{ color: "#480606ff" }}>
          Try typing values, add avoid streets on separate lines, click Route, and
          check your browser console.
        </p>
        <p>Amirali Madani, 2025</p>
      </div>
    </div>

  );
}
