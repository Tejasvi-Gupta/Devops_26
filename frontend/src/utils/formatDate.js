/**
 * Formats an ISO timestamp (as returned by the backend, always UTC) into
 * Indian Standard Time for display -- regardless of the viewer's own
 * machine/browser timezone setting.
 */
export function formatIST(isoString) {
  if (!isoString) return null;
  return new Date(isoString).toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  }) + " IST";
}
