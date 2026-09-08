import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  headers: { "Content-Type": "application/json" },
});

// ---------- Digital Twin ----------
export const seedTwin = () => apiClient.get("/twin/seed").then((res) => res.data);
export const loadTwin = () => apiClient.get("/twin/load").then((res) => res.data);
export const breakEquipment = (equipmentId) =>
  apiClient.post(`/twin/break-equipment/${equipmentId}`).then((res) => res.data);

// ---------- Negotiation ----------
export const negotiatePatientSurge = (payload) =>
  apiClient.post("/negotiate/patient-surge", payload).then((res) => res.data);

export const negotiateEquipmentFailure = (payload) =>
  apiClient.post("/negotiate/equipment-failure", payload).then((res) => res.data);

export const negotiateMedicineShortage = (payload) =>
  apiClient.post("/negotiate/medicine-shortage", payload).then((res) => res.data);

export const negotiateOtOverload = (payload) =>
  apiClient.post("/negotiate/ot-overload", payload).then((res) => res.data);

// ---------- Trust & History ----------
export const getTrustSnapshot = () =>
  apiClient.get("/trust/snapshot").then((res) => res.data);

export const getNegotiationHistory = () =>
  apiClient.get("/history/negotiations").then((res) => res.data);

export default apiClient;