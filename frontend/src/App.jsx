import { useState } from "react";
import TwinPanel from "./components/TwinPanel";
import ScenarioPanel from "./components/ScenarioPanel";
import "./App.css";

function App() {
  const [twinData, setTwinData] = useState(null);

  return (
    <div className="app-container">
      <header>
        <h1>MESH</h1>
        <p className="subtitle">AI-Driven Multi-Agent Decision Intelligence Engine — Hospital Digital Twin</p>
      </header>

      <main className="dashboard-grid">
        <TwinPanel twinData={twinData} setTwinData={setTwinData} />
        <ScenarioPanel />
      </main>
    </div>
  );
}

export default App;