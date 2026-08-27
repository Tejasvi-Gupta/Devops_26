export default function Shell({ view, onChangeView, children }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--color-border)] bg-[var(--color-panel)]">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-base font-semibold tracking-tight">
              Student Environment Platform
            </h1>
            <p className="text-xs text-[var(--color-muted)]">
              Environment provisioning &amp; compliance tracking
            </p>
          </div>
          <nav className="flex gap-1 rounded-lg bg-[var(--color-surface)] p-1">
            <button
              onClick={() => onChangeView("instructor")}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                view === "instructor"
                  ? "bg-[var(--color-panel)] text-[var(--color-ink)] shadow-sm"
                  : "text-[var(--color-muted)] hover:text-[var(--color-ink)]"
              }`}
            >
              Instructor
            </button>
            <button
              onClick={() => onChangeView("student")}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                view === "student"
                  ? "bg-[var(--color-panel)] text-[var(--color-ink)] shadow-sm"
                  : "text-[var(--color-muted)] hover:text-[var(--color-ink)]"
              }`}
            >
              Student
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-8">{children}</main>
    </div>
  );
}
