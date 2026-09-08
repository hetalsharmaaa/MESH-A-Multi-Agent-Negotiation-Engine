import { useState, useEffect } from "react";
import { getTrustSnapshot } from "../api/client";

function TrustPanel({ refreshKey }) {
  const [trust, setTrust] = useState(null);
  const [error, setError] = useState(null);

  const fetchTrust = async () => {
    try {
      const data = await getTrustSnapshot();
      setTrust(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchTrust();
  }, [refreshKey]);

  return (
    <div className="panel">
      <div className="panel-header-row">
        <h2>Agent Trust Scores</h2>
        <button onClick={fetchTrust}>Refresh</button>
      </div>

      {error && <p className="error-text">Error: {error}</p>}

      {trust && (
        <div className="trust-list">
          {Object.entries(trust).map(([agent, data]) => (
            <TrustBar key={agent} agent={agent} data={data} />
          ))}
        </div>
      )}
    </div>
  );
}

function TrustBar({ agent, data }) {
  const percent = Math.round(data.reliability_score * 100);
  const color = percent >= 75 ? "#2e7d32" : percent >= 50 ? "#f9a825" : "#c62828";

  return (
    <div className="trust-row">
      <div className="trust-label">
        <span className="agent-name">{agent}</span>
        <span className="trust-percent">{percent}%</span>
      </div>
      <div className="trust-bar-bg">
        <div className="trust-bar-fill" style={{ width: `${percent}%`, background: color }} />
      </div>
      <div className="trust-meta">
        {data.successful_proposals} won / {data.failed_proposals} failed / {data.total_proposals} total
      </div>
    </div>
  );
}

export default TrustPanel;