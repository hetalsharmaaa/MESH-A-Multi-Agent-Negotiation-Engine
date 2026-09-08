import { useState } from "react";
import TwinPanel from "./components/TwinPanel";
import ScenarioPanel from "./components/ScenarioPanel";
import TrustPanel from "./components/TrustPanel";
import HistoryPanel from "./components/HistoryPanel";
import "./App.css";

function App() {
  const [twinData, setTwinData] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleNegotiationComplete = () => {
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="app-container">
      <header>
        <h1>MESH</h1>
        <p className="subtitle">AI-Driven Multi-Agent Decision Intelligence Engine — Hospital Digital Twin</p>
      </header>

      <main className="dashboard-grid">
        <TwinPanel twinData={twinData} setTwinData={setTwinData} />
        <ScenarioPanel onNegotiationComplete={handleNegotiationComplete} />
      </main>

      <section className="dashboard-grid" style={{ marginTop: "1.5rem" }}>
        <TrustPanel refreshKey={refreshKey} />
        <HistoryPanel refreshKey={refreshKey} />
      </section>
    </div>
  );
}

export default App;