import { useEffect, useState } from "react";
import { api } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import { formatIST } from "../utils/formatDate";

export default function StudentPage() {
  const [students, setStudents] = useState([]);
  const [envDefs, setEnvDefs] = useState([]);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const [newName, setNewName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [enrollEnvId, setEnrollEnvId] = useState("");

  async function loadAll() {
    setLoading(true);
    setError(null);
    try {
      const [s, e] = await Promise.all([
        api.listStudents(),
        api.listEnvironmentDefinitions(),
      ]);
      setStudents(s);
      setEnvDefs(e);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  useEffect(() => {
    if (!selectedStudentId) {
      setStatus(null);
      return;
    }
    api
      .getStudentStatus(selectedStudentId)
      .then(setStatus)
      .catch((err) => setError(err.message));
  }, [selectedStudentId]);

  async function handleCreateStudent(e) {
    e.preventDefault();
    setError(null);
    try {
      const created = await api.createStudent({ name: newName, email: newEmail });
      setNewName("");
      setNewEmail("");
      await loadAll();
      setSelectedStudentId(created.id);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleEnroll(e) {
    e.preventDefault();
    setError(null);
    try {
      if (!selectedStudentId) throw new Error("Select a student first");
      if (!enrollEnvId) throw new Error("Select an environment definition");
      await api.createEnrollment({
        student_id: selectedStudentId,
        environment_definition_id: enrollEnvId,
      });
      setEnrollEnvId("");
      const refreshed = await api.getStudentStatus(selectedStudentId);
      setStatus(refreshed);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="space-y-8">
      {error && (
        <div className="rounded-lg border border-[var(--color-missing)]/30 bg-[var(--color-missing-bg)] px-4 py-3 text-sm text-[var(--color-missing)]">
          {error}
        </div>
      )}

      {/* Student selection / creation */}
      <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] p-6">
        <h2 className="text-sm font-semibold text-[var(--color-ink)]">
          Student
        </h2>
        <p className="mt-1 text-xs text-[var(--color-muted)]">
          Select an existing student to view their status, or create a new one.
        </p>

        <div className="mt-4">
          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--color-muted)]">
            Existing student
            <select
              value={selectedStudentId}
              onChange={(e) => setSelectedStudentId(e.target.value)}
              className="w-full max-w-sm rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
            >
              <option value="">-- none selected --</option>
              {students.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.email})
                </option>
              ))}
            </select>
          </label>
        </div>

        <form
          onSubmit={handleCreateStudent}
          className="mt-4 flex flex-wrap items-end gap-3 border-t border-[var(--color-border)] pt-4"
        >
          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--color-muted)]">
            New student name
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Alice"
              className="rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--color-muted)]">
            Email
            <input
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              placeholder="alice@university.edu"
              type="email"
              className="rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
            />
          </label>
          <button
            type="submit"
            disabled={!newName || !newEmail}
            className="rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-40"
          >
            Create student
          </button>
        </form>
      </section>

      {selectedStudentId && (
        <>
          {/* Enroll in an environment */}
          <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] p-6">
            <h2 className="text-sm font-semibold text-[var(--color-ink)]">
              Enroll in an environment definition
            </h2>
            <form onSubmit={handleEnroll} className="mt-4 flex flex-wrap items-end gap-3">
              <label className="flex flex-col gap-1 text-xs font-medium text-[var(--color-muted)]">
                Environment
                <select
                  value={enrollEnvId}
                  onChange={(e) => setEnrollEnvId(e.target.value)}
                  className="w-full max-w-sm rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
                >
                  <option value="">-- select --</option>
                  {envDefs.map((env) => (
                    <option key={env.id} value={env.id}>
                      {env.name}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="submit"
                className="rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-accent-hover)]"
              >
                Enroll
              </button>
            </form>
          </section>

          {/* Status */}
          <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] p-6">
            <h2 className="text-sm font-semibold text-[var(--color-ink)]">
              Your environment status
            </h2>

            {!status || status.environments.length === 0 ? (
              <p className="mt-4 text-sm text-[var(--color-muted)]">
                Not enrolled in any environment definitions yet.
              </p>
            ) : (
              <div className="mt-4 space-y-6">
                {status.environments.map((env) => (
                  <div key={env.environment_definition_id}>
                    <div className="flex items-baseline justify-between">
                      <h3 className="text-sm font-semibold">
                        {env.environment_definition_name}
                      </h3>
                      <span className="text-xs text-[var(--color-muted)]">
                        {env.last_checked_at
                          ? `Last checked ${formatIST(env.last_checked_at)}`
                          : "Never checked — run the Student Agent"}
                      </span>
                    </div>
                    <div className="mt-2 overflow-hidden rounded-lg border border-[var(--color-border)]">
                      <table className="w-full text-sm">
                        <thead className="bg-[var(--color-surface)] text-left text-xs text-[var(--color-muted)]">
                          <tr>
                            <th className="px-4 py-2 font-medium">Tool</th>
                            <th className="px-4 py-2 font-medium">Required</th>
                            <th className="px-4 py-2 font-medium">Found</th>
                            <th className="px-4 py-2 font-medium">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {env.requirements.map((r) => (
                            <tr
                              key={r.requirement_id}
                              className="border-t border-[var(--color-border)]"
                            >
                              <td className="px-4 py-3 font-medium">{r.tool_name}</td>
                              <td className="px-4 py-3 font-mono text-[var(--color-muted)]">
                                {r.min_version}
                              </td>
                              <td className="px-4 py-3 font-mono text-[var(--color-muted)]">
                                {r.found_version || "—"}
                              </td>
                              <td className="px-4 py-3">
                                <StatusBadge status={r.status} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
