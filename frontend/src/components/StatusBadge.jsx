const STYLES = {
  satisfied: "bg-[var(--color-satisfied-bg)] text-[var(--color-satisfied)]",
  outdated: "bg-[var(--color-outdated-bg)] text-[var(--color-outdated)]",
  missing: "bg-[var(--color-missing-bg)] text-[var(--color-missing)]",
  error: "bg-[var(--color-missing-bg)] text-[var(--color-missing)]",
};

const LABELS = {
  satisfied: "Satisfied",
  outdated: "Outdated",
  missing: "Missing",
  error: "Error",
};

export default function StatusBadge({ status }) {
  const style = STYLES[status] || "bg-gray-100 text-gray-600";
  const label = LABELS[status] || status;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}
    >
      {label}
    </span>
  );
}
