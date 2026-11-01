import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Filter, Siren } from "lucide-react";

import api from "../services/api.js";
import { useToast } from "../components/Toast.jsx";
import AlertHistory from "../components/AlertHistory.jsx";
import NotificationList from "../components/NotificationList.jsx";

const STATUSES = ["all", "active", "acknowledged", "resolved", "cancelled"];

export default function Alerts() {
  const toast = useToast();
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [retryingId, setRetryingId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/alerts");
      setAlerts(data);
    } catch (err) {
      toast.error(err.message || "Could not load alerts");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    load();
  }, [load]);

  const updateStatus = async (alert, status) => {
    try {
      await api.patch(`/alerts/${alert.id}/status`, { status });
      toast.success(`Alert marked as ${status}.`);
      load();
    } catch (err) {
      toast.error(err.message || "Could not update the alert");
    }
  };

  const cancelAlert = (alert) => updateStatus(alert, "cancelled");

  // Update a single alert in local state without refetching the whole list.
  const replaceAlert = (alertId, updater) => {
    setAlerts((prev) => prev.map((a) => (a.id === alertId ? updater(a) : a)));
  };

  const retryNotifications = async (alert) => {
    setRetryingId(alert.id);
    try {
      const { data } = await api.post(`/alerts/${alert.id}/notifications/retry`);
      replaceAlert(alert.id, (a) => ({ ...a, notifications: data.notifications, delivery: data.delivery }));
      const delivered = data.delivery?.delivered || 0;
      const sent = data.delivery?.sent || 0;
      const failed = data.delivery?.failed || 0;
      if (failed === 0) {
        toast.success(`Retry complete. ${sent + delivered} of ${data.delivery.total} SMS accepted.`);
      } else if (failed === data.delivery.total) {
        toast.error(`Retry failed for all ${failed} contact(s). See details below.`);
      } else {
        toast.warning(`Retry complete. ${sent + delivered} accepted, ${failed} still failing.`);
      }
    } catch (err) {
      toast.error(err.message || "Could not retry notifications");
    } finally {
      setRetryingId(null);
    }
  };

  const filtered =
    filter === "all" ? alerts : alerts.filter((a) => a.status === filter);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">Emergency Alerts</h1>
          <p className="page-subtitle">Full history of your recorded alerts.</p>
        </div>
      </div>

      {/* Filters */}
      <div className="filter-bar">
        <Filter size={16} />
        <div className="filter-buttons">
          {STATUSES.map((s) => (
            <button
              key={s}
              type="button"
              className={`filter-btn ${filter === s ? "active" : ""}`}
              onClick={() => setFilter(s)}
            >
              {s === "all" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Summary of selected alert */}
      {loading ? (
        <p className="muted">Loading alerts…</p>
      ) : filtered.length === 0 ? (
        <div className="empty-state big">
          <Siren size={34} />
          <h3>No alerts found</h3>
          <p>{filter === "all" ? "You haven't sent any emergency alerts yet." : `No ${filter} alerts.`}</p>
          <Link to="/dashboard" className="btn btn-primary">
            Go to dashboard
          </Link>
        </div>
      ) : (
        <div className="alert-detail-list">
          {filtered.map((a) => (
            <div key={a.id} className="card alert-detail">
              <div className="alert-detail-main">
                <span className="alert-detail-id">Alert #{a.id}</span>
                <AlertHistory alerts={[a]} />
                <div className="alert-detail-actions">
                  {a.status === "active" && (
                    <>
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        onClick={() => updateStatus(a, "acknowledged")}
                      >
                        Mark acknowledged
                      </button>
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        onClick={() => updateStatus(a, "resolved")}
                      >
                        Mark resolved
                      </button>
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm danger"
                        onClick={() => cancelAlert(a)}
                      >
                        Cancel alert
                      </button>
                    </>
                  )}
                </div>
                <NotificationList
                  notifications={a.notifications || []}
                  delivery={a.delivery}
                  onRetry={() => retryNotifications(a)}
                  retrying={retryingId === a.id}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
