import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import StatusBadge from "../components/StatusBadge";
import { formatIST } from "../utils/formatDate";

export default function StudentPage() {
  const { user } = useAuth();
  const [envDefs, setEnvDefs] = useState([]);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [enrollEnvId, setEnrollEnvId] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [e, s] = await Promise.all([
          api.listEnvironmentDefinitions(),
          api.getStudentStatus(user.id),
        ]);
        if (!cancelled) {
          setEnvDefs(e);
          setStatus(s);
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [user.id]);

  async function handleEnroll(e) {
    e.preventDefault();
    setError(null);
    try {
      if (!enrollEnvId) throw new Error("Select an environment definition");
      await api.createEnrollment({
        environment_definition_id: enrollEnvId,
      });
      setEnrollEnvId("");
      const refreshed = await api.getStudentStatus(user.id);
      setStatus(refreshed);
    } catch (err) {
      setError(err.message);
    }
  }

  const enrolledIds = new Set(
    (status?.environments || []).map((env) => env.environment_definition_id)
  );
  const availableEnvs = envDefs.filter((env) => !enrolledIds.has(env.id));

  return (
    <div className="space-y-8">
      {error && (
        <div className="rounded-lg border border-[var(--color-missing)]/30 bg-[var(--color-missing-bg)] px-4 py-3 text-sm text-[var(--color-missing)]">
          {error}
        </div>
      )}

      <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] p-6">
        <h2 className="text-sm font-semibold text-[var(--color-ink)]">
          Enroll in an environment definition
        </h2>
        <p className="mt-1 text-xs text-[var(--color-muted)]">
          Signed in as {user.name} ({user.email}).
        </p>
        <form onSubmit={handleEnroll} className="mt-4 flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--color-muted)]">
            Environment
            <select
              value={enrollEnvId}
              onChange={(e) => setEnrollEnvId(e.target.value)}
              className="w-full max-w-sm rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
            >
              <option value="">-- select --</option>
              {availableEnvs.map((env) => (
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

      <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] p-6">
        <h2 className="text-sm font-semibold text-[var(--color-ink)]">
          Your environment status
        </h2>

        {loading ? (
          <p className="mt-4 text-sm text-[var(--color-muted)]">Loading...</p>
        ) : !status || status.environments.length === 0 ? (
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
                <p className="mt-1 font-mono text-xs text-[var(--color-muted)]">
                  python agent.py check --email {user.email} --password
                  &lt;your-password&gt; --env-id {env.environment_definition_id}
                </p>
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
    </div>
  );
}
