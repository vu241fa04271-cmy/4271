const LABELS = {
  active: "Active",
  acknowledged: "Acknowledged",
  resolved: "Resolved",
  cancelled: "Cancelled",
};

export default function StatusBadge({ status }) {
  const cls = `status-badge status-${status || "active"}`;
  return <span className={cls}>{LABELS[status] || status}</span>;
}
