import { useState } from "react";
import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState("login");
  const [role, setRole] = useState("instructor");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "register") {
        if (!name.trim()) throw new Error("Name is required");
        if (password.length < 8) throw new Error("Password must be at least 8 characters");
        await register(name.trim(), email.trim(), password, role);
      } else {
        await login(email.trim(), password, role);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-md py-16">
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] p-8">
        <h1 className="text-lg font-semibold tracking-tight">
          Student Environment Platform
        </h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Sign in to manage environment definitions or check your setup.
        </p>

        <div className="mt-6 flex gap-1 rounded-lg bg-[var(--color-surface)] p-1">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition ${
              mode === "login"
                ? "bg-[var(--color-panel)] text-[var(--color-ink)] shadow-sm"
                : "text-[var(--color-muted)]"
            }`}
          >
            Sign in
          </button>
          <button
            type="button"
            onClick={() => setMode("register")}
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition ${
              mode === "register"
                ? "bg-[var(--color-panel)] text-[var(--color-ink)] shadow-sm"
                : "text-[var(--color-muted)]"
            }`}
          >
            Register
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-lg border border-[var(--color-missing)]/30 bg-[var(--color-missing-bg)] px-4 py-3 text-sm text-[var(--color-missing)]">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--color-muted)]">
            Role
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="rounded-md border border-[var(--color-border)] px-3 py-2 text-sm text-[var(--color-ink)]"
            >
              <option value="instructor">Instructor</option>
              <option value="student">Student</option>
            </select>
          </label>

          {mode === "register" && (
            <label className="flex flex-col gap-1 text-xs font-medium text-[var(--color-muted)]">
              Name
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Dr. Smith"
                className="rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
                required
              />
            </label>
          )}

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--color-muted)]">
            Email
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@university.edu"
              type="email"
              className="rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
              required
            />
          </label>

          <label className="flex flex-col gap-1 text-xs font-medium text-[var(--color-muted)]">
            Password
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              minLength={8}
              className="rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
              required
            />
          </label>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-40"
          >
            {submitting
              ? "Please wait..."
              : mode === "login"
                ? "Sign in"
                : "Create account"}
          </button>
        </form>
      </div>
    </div>
  );
}
