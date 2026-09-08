import { useState } from "react";
import { seedTwin, loadTwin } from "../api/client";

function TwinPanel({ twinData, setTwinData }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSeed = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await seedTwin();
      setTwinData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLoad = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await loadTwin();
      setTwinData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <h2>Hospital Digital Twin</h2>

      <div className="button-row">
        <button onClick={handleSeed} disabled={loading}>
          Seed Fresh Data
        </button>
        <button onClick={handleLoad} disabled={loading}>
          Load From DB
        </button>
      </div>

      {error && <p className="error-text">Error: {error}</p>}
      {loading && <p>Loading...</p>}

      {twinData && (
        <div className="twin-grid">
          <TwinSection title="Beds" data={twinData.beds} />
          <TwinSection title="Staff" data={twinData.staff} />
          <TwinSection title="Equipment" data={twinData.equipment} />
          <TwinSection title="Pharmacy" data={twinData.pharmacy} />
        </div>
      )}
    </div>
  );
}

function TwinSection({ title, data }) {
  const entries = Object.entries(data || {});
  return (
    <div className="twin-section">
      <h3>{title}</h3>
      {entries.length === 0 && <p className="muted">No data yet</p>}
      <ul>
        {entries.map(([id, item]) => (
          <li key={id}>
            <TwinItemLine item={item} />
          </li>
        ))}
      </ul>
    </div>
  );
}

function TwinItemLine({ item }) {
  // Handles beds, staff, equipment, pharmacy shapes generically
  if ("bed_id" in item) return <span>{item.bed_id} — {item.ward} — <StatusTag status={item.status} /></span>;
  if ("staff_id" in item) return <span>{item.staff_id} — {item.role} — {item.ward} — {item.available ? "available" : "unavailable"}</span>;
  if ("equipment_id" in item) return <span>{item.equipment_id} — {item.type} — {item.ward} — <StatusTag status={item.status} /></span>;
  if ("name" in item) return <span>{item.name} — qty: {item.quantity}</span>;
  return <span>{JSON.stringify(item)}</span>;
}

function StatusTag({ status }) {
  const colors = {
    free: "#2e7d32",
    available: "#2e7d32",
    occupied: "#c62828",
    in_use: "#c62828",
    faulty: "#c62828",
    reserved: "#f9a825",
  };
  return (
    <span style={{ color: colors[status] || "#555", fontWeight: 600 }}>
      {status}
    </span>
  );
}

export default TwinPanel;