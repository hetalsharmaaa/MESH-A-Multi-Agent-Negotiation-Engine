import { useState } from "react";
import {
  negotiatePatientSurge,
  negotiateEquipmentFailure,
  negotiateMedicineShortage,
  negotiateOtOverload,
} from "../api/client";
import NegotiationResult from "./NegotiationResult";

const SCENARIOS = {
  patient_surge: { label: "Patient Surge", fields: ["ward", "patient_count"] },
  equipment_failure: { label: "Equipment Failure", fields: ["ward", "equipment_type"] },
  medicine_shortage: { label: "Medicine Shortage", fields: ["medicine", "amount"] },
  ot_overload: { label: "OT Overload", fields: ["surgery_count"] },
};

function ScenarioPanel() {
  const [scenarioType, setScenarioType] = useState("patient_surge");
  const [form, setForm] = useState({
    ward: "ICU",
    patient_count: 5,
    equipment_type: "ventilator",
    medicine: "Paracetamol",
    amount: 150,
    surgery_count: 2,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let data;
      if (scenarioType === "patient_surge") {
        data = await negotiatePatientSurge({
          scenario_type: "patient_surge",
          ward: form.ward,
          patient_count: Number(form.patient_count),
        });
      } else if (scenarioType === "equipment_failure") {
        data = await negotiateEquipmentFailure({
          scenario_type: "equipment_failure",
          ward: form.ward,
          details: { equipment_type: form.equipment_type },
        });
      } else if (scenarioType === "medicine_shortage") {
        data = await negotiateMedicineShortage({
          scenario_type: "medicine_shortage",
          details: { medicine: form.medicine, amount: Number(form.amount) },
        });
      } else if (scenarioType === "ot_overload") {
        data = await negotiateOtOverload({
          scenario_type: "ot_overload",
          details: { surgery_count: Number(form.surgery_count) },
        });
      }
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const activeFields = SCENARIOS[scenarioType].fields;

  return (
    <div className="panel">
      <h2>Trigger Scenario</h2>

      <label>
        Scenario type:
        <select value={scenarioType} onChange={(e) => setScenarioType(e.target.value)}>
          {Object.entries(SCENARIOS).map(([key, cfg]) => (
            <option key={key} value={key}>{cfg.label}</option>
          ))}
        </select>
      </label>

      <div className="form-fields">
        {activeFields.includes("ward") && (
          <label>Ward: <input value={form.ward} onChange={(e) => handleChange("ward", e.target.value)} /></label>
        )}
        {activeFields.includes("patient_count") && (
          <label>Patient Count: <input type="number" value={form.patient_count} onChange={(e) => handleChange("patient_count", e.target.value)} /></label>
        )}
        {activeFields.includes("equipment_type") && (
          <label>Equipment Type: <input value={form.equipment_type} onChange={(e) => handleChange("equipment_type", e.target.value)} /></label>
        )}
        {activeFields.includes("medicine") && (
          <label>Medicine: <input value={form.medicine} onChange={(e) => handleChange("medicine", e.target.value)} /></label>
        )}
        {activeFields.includes("amount") && (
          <label>Amount Needed: <input type="number" value={form.amount} onChange={(e) => handleChange("amount", e.target.value)} /></label>
        )}
        {activeFields.includes("surgery_count") && (
          <label>Surgery Count: <input type="number" value={form.surgery_count} onChange={(e) => handleChange("surgery_count", e.target.value)} /></label>
        )}
      </div>

      <button onClick={handleSubmit} disabled={loading}>
        {loading ? "Negotiating..." : "Run Negotiation"}
      </button>

      {error && <p className="error-text">Error: {error}</p>}

      <NegotiationResult result={result} />
    </div>
  );
}

export default ScenarioPanel;