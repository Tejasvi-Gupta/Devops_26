/**
 * Thin fetch wrapper around the FastAPI backend. All calls go through the
 * Vite dev proxy at /api (see vite.config.js), which forwards to
 * http://127.0.0.1:8000 and strips the /api prefix.
 */
const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
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
  // Instructors
  createInstructor: (data) =>
    request("/instructors", { method: "POST", body: JSON.stringify(data) }),
  listInstructors: () => request("/instructors"),

  // Students
  createStudent: (data) =>
    request("/students", { method: "POST", body: JSON.stringify(data) }),
  listStudents: () => request("/students"),

  // Environment definitions
  createEnvironmentDefinition: (data) =>
    request("/environment-definitions", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  listEnvironmentDefinitions: () => request("/environment-definitions"),
  getEnvironmentDefinition: (id) => request(`/environment-definitions/${id}`),

  // Enrollments
  createEnrollment: (data) =>
    request("/enrollments", { method: "POST", body: JSON.stringify(data) }),
  listEnrollments: () => request("/enrollments"),

  // Status / compliance (read models)
  getStudentStatus: (studentId) => request(`/students/${studentId}/status`),
  getComplianceSummary: (envDefId) =>
    request(`/environment-definitions/${envDefId}/compliance`),
};
