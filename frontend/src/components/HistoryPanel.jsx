import { useState, useEffect } from "react";
import { getNegotiationHistory } from "../api/client";

function HistoryPanel({ refreshKey }) {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);

  const fetchHistory = async () => {
    try {
      const data = await getNegotiationHistory();
      setHistory(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [refreshKey]);

  return (
    <div className="panel">
      <div className="panel-header-row">
        <h2>Negotiation History</h2>
        <button onClick={fetchHistory}>Refresh</button>
      </div>

      {error && <p className="error-text">Error: {error}</p>}

      {history.length === 0 ? (
        <p className="muted">No negotiations run yet.</p>
      ) : (
        <table className="history-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Scenario</th>
              <th>Winning Action</th>
              <th>Verified</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {history.map((log) => (
              <tr key={log.id}>
                <td>{log.id}</td>
                <td>{log.scenario_type}</td>
                <td>
                  {log.winning_action
                    ? `${log.winning_action.action} (${log.winning_action.target_id ?? "-"})`
                    : "None"}
                </td>
                <td>
                  <span className={log.verification_passed ? "tag-pass" : "tag-fail"}>
                    {log.verification_passed ? "✓" : "✗"}
                  </span>
                </td>
                <td>{new Date(log.created_at).toLocaleTimeString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default HistoryPanel;