function NegotiationResult({ result }) {
  if (!result) return null;

  const { decision_summary, verification_failed_completely } = result;

  return (
    <div className="negotiation-result">
      <h3>Decision</h3>

      {verification_failed_completely && (
        <p className="error-text">⚠ No feasible verified action was found.</p>
      )}

      {decision_summary && (
        <>
          <p className="recommendation">
            Recommendation: <strong>{decision_summary.recommendation}</strong>
          </p>
          <p className="confidence">
            Confidence: <strong>{decision_summary.confidence_percent}%</strong>
          </p>

          <h4>Reasoning Chain</h4>
          <ol className="reasoning-chain">
            {decision_summary.chain.map((step, idx) => (
              <li key={idx}>{step}</li>
            ))}
          </ol>
        </>
      )}

      <details>
        <summary>Raw negotiation data (debug)</summary>
        <pre className="raw-json">{JSON.stringify(result, null, 2)}</pre>
      </details>
    </div>
  );
}

export default NegotiationResult;