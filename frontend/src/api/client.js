/**
 * Thin fetch wrapper around the FastAPI backend. All calls go through the
 * Vite dev proxy at /api (see vite.config.js), which forwards to
 * http://127.0.0.1:8000 and strips the /api prefix.
 */
const BASE = "/api";
const AUTH_LOST = "sep-auth-lost";

let authToken = localStorage.getItem("sep_token");

export function setAuthToken(token) {
  authToken = token || null;
}

async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }

  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers,
  });
  if (res.status === 401) {
    localStorage.removeItem("sep_token");
    localStorage.removeItem("sep_user");
    authToken = null;
    window.dispatchEvent(new Event(AUTH_LOST));
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // response wasn't JSON, keep statusText
    }
    throw new Error(`${res.status} ${detail}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  register: (data) =>
    request("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data) =>
    request("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  me: () => request("/auth/me"),

  listInstructors: () => request("/instructors"),
  listStudents: () => request("/students"),

  createEnvironmentDefinition: (data) =>
    request("/environment-definitions", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  listEnvironmentDefinitions: () => request("/environment-definitions"),
  getEnvironmentDefinition: (id) => request(`/environment-definitions/${id}`),

  createEnrollment: (data) =>
    request("/enrollments", { method: "POST", body: JSON.stringify(data) }),
  listEnrollments: () => request("/enrollments"),

  getStudentStatus: (studentId) => request(`/students/${studentId}/status`),
  getComplianceSummary: (envDefId) =>
    request(`/environment-definitions/${envDefId}/compliance`),
  getRiskReport: (envDefId) =>
    request(`/environment-definitions/${envDefId}/risk-report`),
};
