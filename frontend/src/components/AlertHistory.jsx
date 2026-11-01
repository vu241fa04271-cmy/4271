import { Clock, MapPin, Siren } from "lucide-react";
import { googleMapsUrl } from "../services/geolocation.js";
import StatusBadge from "./StatusBadge.jsx";

const fmt = (iso) => {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
};

/**
 * Reusable list of emergency alerts. When `onCancel` is provided, active
 * alerts show a "Cancel alert" button.
 */
export default function AlertHistory({ alerts = [], loading = false, onCancel }) {
  if (loading) {
    return <p className="muted">Loading alerts…</p>;
  }
  if (!alerts.length) {
    return (
      <div className="empty-state">
        <Siren size={28} />
        <p>No emergency alerts yet.</p>
      </div>
    );
  }

  return (
    <ul className="alert-list">
      {alerts.map((a) => (
        <li key={a.id} className="alert-item">
          <div className="alert-item-main">
            <div className="alert-item-head">
              <StatusBadge status={a.status} />
              <span className="alert-time">
                <Clock size={13} /> {fmt(a.timestamp)}
              </span>
            </div>
            <div className="alert-coords">
              <MapPin size={13} />
              <span>
                {a.latitude?.toFixed(5)}, {a.longitude?.toFixed(5)}
              </span>
              <a
                href={googleMapsUrl(a.latitude, a.longitude)}
                target="_blank"
                rel="noreferrer"
                className="alert-map-link"
              >
                Open in Google Maps
              </a>
            </div>
          </div>
          {onCancel && a.status === "active" && (
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => onCancel(a)}
            >
              Cancel alert
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}
