import { CheckCheck, RefreshCw, Send, XCircle } from "lucide-react";

const STATUS_LABEL = {
  pending: "Pending",
  sent: "Sent",
  delivered: "Delivered",
  failed: "Failed",
};

/**
 * Shows the per-contact SMS delivery status for one emergency alert.
 * Renders summary chips, a row per recipient (with any error), and a retry
 * button when at least one notification failed.
 */
export default function NotificationList({
  notifications = [],
  delivery = null,
  onRetry,
  retrying = false,
}) {
  if (!notifications.length) {
    return (
      <div className="notif-empty">
        <Send size={18} />
        <span>No SMS notifications were sent for this alert (no trusted contacts at the time).</span>
      </div>
    );
  }

  const s = delivery || {
    total: notifications.length,
    sent: notifications.filter((n) => n.status === "sent").length,
    delivered: notifications.filter((n) => n.status === "delivered").length,
    failed: notifications.filter((n) => n.status === "failed").length,
  };
  const hasFailed = s.failed > 0;

  return (
    <div className="notif-list">
      <div className="notif-summary">
        <span className="notif-summary-title">
          <Send size={15} /> SMS notifications
        </span>
        <span className="notif-chips">
          {s.delivered > 0 && (
            <span className="notif-chip notif-delivered">{s.delivered} delivered</span>
          )}
          {s.sent > 0 && (
            <span className="notif-chip notif-sent">{s.sent} sent</span>
          )}
          {s.failed > 0 && (
            <span className="notif-chip notif-failed">{s.failed} failed</span>
          )}
        </span>
        {hasFailed && onRetry && (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={onRetry}
            disabled={retrying}
          >
            <RefreshCw size={14} /> {retrying ? "Retrying…" : "Retry failed"}
          </button>
        )}
      </div>

      <ul className="notif-items">
        {notifications.map((n) => (
          <li key={n.id} className="notif-item">
            <div className="notif-item-main">
              <span className={`notif-badge notif-${n.status}`}>
                {n.status === "delivered" ? <CheckCheck size={12} /> : n.status === "failed" ? <XCircle size={12} /> : null}
                {STATUS_LABEL[n.status] || n.status}
              </span>
              <span className="notif-recipient">{n.recipient_name}</span>
              <span className="notif-phone">{n.phone}</span>
            </div>
            {n.error && <span className="notif-error">{n.error}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
