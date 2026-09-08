import { useState } from "react";
import { seedTwin } from "./api/client";

function App() {
  const [twinData, setTwinData] = useState(null);
  const [error, setError] = useState(null);

  const handleSeed = async () => {
    try {
      setError(null);
      const data = await seedTwin();
      setTwinData(data);
    } catch (err) {
      setError(err.message || "Failed to connect to backend");
    }
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>MESH — Multi-Agent Negotiation Engine</h1>
      <button onClick={handleSeed}>Seed Digital Twin</button>

      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {twinData && (
        <pre style={{ background: "#f4f4f4", padding: "1rem", marginTop: "1rem" }}>
          {JSON.stringify(twinData, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default App;