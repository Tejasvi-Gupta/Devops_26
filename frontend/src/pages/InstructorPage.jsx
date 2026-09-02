import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import StatusBadge from "../components/StatusBadge";
import { formatIST } from "../utils/formatDate";

const EMPTY_REQUIREMENT = { tool_name: "", min_version: "" };
const VERSION_PATTERN = /^\d+(\.\d+)*$/;

const RISK_STYLES = {
  high: "bg-[var(--color-missing-bg)] text-[var(--color-missing)]",
  medium: "bg-[var(--color-outdated-bg)] text-[var(--color-outdated)]",
  low: "bg-[var(--color-satisfied-bg)] text-[var(--color-satisfied)]",
};

function RiskBadge({ level }) {
  const style = RISK_STYLES[level] || "bg-gray-100 text-gray-600";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${style}`}
    >
      {level} risk
    </span>
  );
}

export default function InstructorPage() {
  const { user } = useAuth();
  const [envDefs, setEnvDefs] = useState([]);
  const [selectedEnvId, setSelectedEnvId] = useState(null);
  const [compliance, setCompliance] = useState(null);
  const [riskReport, setRiskReport] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const [envName, setEnvName] = useState("");
  const [requirements, setRequirements] = useState([{ ...EMPTY_REQUIREMENT }]);
  const [submitting, setSubmitting] = useState(false);

  async function loadAll() {
    setLoading(true);
    setError(null);
    try {
      const e = await api.listEnvironmentDefinitions();
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
    if (!selectedEnvId) {
      setCompliance(null);
      setRiskReport(null);
      return;
    }
    Promise.all([
      api.getComplianceSummary(selectedEnvId),
      api.getRiskReport(selectedEnvId),
    ])
      .then(([c, r]) => {
        setCompliance(c);
        setRiskReport(r);
      })
      .catch((err) => setError(err.message));
  }, [selectedEnvId]);

  function updateRequirement(idx, field, value) {
    if (field === "min_version") {
      value = value.replace(/^\s*(>=|<=|~|\^|=|>|<)\s*/, "");
    }
    setRequirements((reqs) =>
      reqs.map((r, i) => (i === idx ? { ...r, [field]: value } : r))
    );
  }

  function addRequirementRow() {
    setRequirements((reqs) => [...reqs, { ...EMPTY_REQUIREMENT }]);
  }

  function removeRequirementRow(idx) {
    setRequirements((reqs) => reqs.filter((_, i) => i !== idx));
  }

  async function handleCreateEnvironment(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const cleanRequirements = requirements
        .filter((r) => r.tool_name.trim() && r.min_version.trim())
        .map((r) => ({
          tool_name: r.tool_name.trim(),
          min_version: r.min_version.trim(),
        }));

      if (!envName.trim()) throw new Error("Environment name is required");
      const badVersion = cleanRequirements.find(
        (r) => !VERSION_PATTERN.test(r.min_version)
      );
      if (badVersion)
        throw new Error(
          `"${badVersion.min_version}" isn't a valid version for ${badVersion.tool_name} — use a plain number like 3.11.0`
        );
      if (cleanRequirements.length === 0)
        throw new Error("Add at least one requirement");

      const created = await api.createEnvironmentDefinition({
        name: envName.trim(),
        requirements: cleanRequirements,
      });

      setEnvName("");
      setRequirements([{ ...EMPTY_REQUIREMENT }]);
      await loadAll();
      setSelectedEnvId(created.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  const riskByStudent = {};
  if (riskReport) {
    for (const row of riskReport.students) {
      riskByStudent[row.student_id] = row;
    }
  }

  return (
    <div className="space-y-8">
      {error && (
        <div className="rounded-lg border border-[var(--color-missing)]/30 bg-[var(--color-missing-bg)] px-4 py-3 text-sm text-[var(--color-missing)]">
          {error}
        </div>
      )}

      <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] p-6">
        <h2 className="text-sm font-semibold text-[var(--color-ink)]">
          New environment definition
        </h2>
        <p className="mt-1 text-xs text-[var(--color-muted)]">
          Signed in as {user.name}. Define the tools and minimum versions
          students in this course need.
        </p>

        <form onSubmit={handleCreateEnvironment} className="mt-4 space-y-4">
          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--color-muted)]">
            Environment name
            <input
              value={envName}
              onChange={(e) => setEnvName(e.target.value)}
              placeholder="CS101 Fall 2026"
              className="w-full max-w-sm rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
            />
          </label>

          <div className="space-y-2">
            <span className="text-xs font-medium text-[var(--color-muted)]">
              Requirements
            </span>
            <p className="text-xs text-[var(--color-muted)]">
              Version must be a plain number like <code>3.11.0</code> — no{" "}
              <code>&gt;=</code>, <code>^</code>, or <code>~</code>.
            </p>
            {requirements.map((req, idx) => {
              const versionInvalid =
                req.min_version.trim() !== "" &&
                !VERSION_PATTERN.test(req.min_version.trim());
              return (
                <div key={idx} className="flex items-center gap-2">
                  <input
                    value={req.tool_name}
                    onChange={(e) =>
                      updateRequirement(idx, "tool_name", e.target.value)
                    }
                    placeholder="python"
                    className="w-40 rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
                  />
                  <div className="flex flex-col">
                    <input
                      value={req.min_version}
                      onChange={(e) =>
                        updateRequirement(idx, "min_version", e.target.value)
                      }
                      placeholder="3.11.0"
                      className={`w-32 rounded-md border px-3 py-2 text-sm font-mono ${
                        versionInvalid
                          ? "border-[var(--color-missing)]"
                          : "border-[var(--color-border)]"
                      }`}
                    />
                  </div>
                  {versionInvalid && (
                    <span className="text-xs text-[var(--color-missing)]">
                      Use a plain version, e.g. 3.11.0
                    </span>
                  )}
                  {requirements.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeRequirementRow(idx)}
                      className="text-xs text-[var(--color-muted)] hover:text-[var(--color-missing)]"
                    >
                      Remove
                    </button>
                  )}
                </div>
              );
            })}
            <button
              type="button"
              onClick={addRequirementRow}
              className="text-xs font-medium text-[var(--color-accent)] hover:underline"
            >
              + Add another requirement
            </button>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-40"
          >
            {submitting ? "Creating..." : "Create environment definition"}
          </button>
        </form>
      </section>

      <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] p-6">
        <h2 className="text-sm font-semibold text-[var(--color-ink)]">
          Environment definitions
        </h2>

        {loading ? (
          <p className="mt-4 text-sm text-[var(--color-muted)]">Loading...</p>
        ) : envDefs.length === 0 ? (
          <p className="mt-4 text-sm text-[var(--color-muted)]">
            No environment definitions yet. Create one above.
          </p>
        ) : (
          <div className="mt-4 flex flex-wrap gap-2">
            {envDefs.map((env) => (
              <button
                key={env.id}
                onClick={() => setSelectedEnvId(env.id)}
                className={`rounded-full border px-3 py-1.5 text-sm transition ${
                  selectedEnvId === env.id
                    ? "border-[var(--color-accent)] bg-[var(--color-accent)]/10 text-[var(--color-accent)]"
                    : "border-[var(--color-border)] text-[var(--color-muted)] hover:border-[var(--color-accent)]"
                }`}
              >
                {env.name}
              </button>
            ))}
          </div>
        )}

        {compliance && (
          <div className="mt-6 border-t border-[var(--color-border)] pt-6">
            <div className="flex items-baseline justify-between">
              <h3 className="text-sm font-semibold">
                {compliance.environment_definition_name}
              </h3>
              <span className="text-xs text-[var(--color-muted)]">
                {compliance.fully_compliant} / {compliance.total_enrolled} fully
                compliant
              </span>
            </div>

            {compliance.students.length === 0 ? (
              <p className="mt-3 text-sm text-[var(--color-muted)]">
                No students enrolled yet.
              </p>
            ) : (
              <div className="mt-3 overflow-hidden rounded-lg border border-[var(--color-border)]">
                <table className="w-full text-sm">
                  <thead className="bg-[var(--color-surface)] text-left text-xs text-[var(--color-muted)]">
                    <tr>
                      <th className="px-4 py-2 font-medium">Student</th>
                      <th className="px-4 py-2 font-medium">Requirements</th>
                      <th className="px-4 py-2 font-medium">Setup risk</th>
                      <th className="px-4 py-2 font-medium">Last checked</th>
                    </tr>
                  </thead>
                  <tbody>
                    {compliance.students.map((s) => {
                      const env = s.environments[0];
                      const risk = riskByStudent[s.student_id];
                      return (
                        <tr
                          key={s.student_id}
                          className="border-t border-[var(--color-border)]"
                        >
                          <td className="px-4 py-3 font-medium">
                            {s.student_name}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex flex-wrap gap-1.5">
                              {env.requirements.map((r) => (
                                <span
                                  key={r.requirement_id}
                                  className="inline-flex items-center gap-1"
                                  title={`${r.tool_name} >= ${r.min_version}`}
                                >
                                  <StatusBadge status={r.status} />
                                </span>
                              ))}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            {risk ? (
                              <span title={risk.reasons.join("; ")}>
                                <RiskBadge level={risk.risk_level} />
                              </span>
                            ) : (
                              <span className="text-xs text-[var(--color-muted)]">
                                —
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-[var(--color-muted)]">
                            {env.last_checked_at
                              ? formatIST(env.last_checked_at)
                              : "Never"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
