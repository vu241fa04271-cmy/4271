import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  ExternalLink,
  LifeBuoy,
  LocateFixed,
  MapPin,
  Phone,
  Share2,
  Siren,
  Users,
} from "lucide-react";

import api from "../services/api.js";
import {
  getCurrentPosition,
  googleMapsUrl,
  isGeolocationAvailable,
} from "../services/geolocation.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useToast } from "../components/Toast.jsx";
import SOSButton from "../components/SOSButton.jsx";
import LocationMap from "../components/LocationMap.jsx";
import AlertHistory from "../components/AlertHistory.jsx";

const SAFETY_TIPS = [
  "Save emergency numbers (112 and 181) on speed dial.",
  "Share your live location with a trusted contact before traveling alone.",
  "Stay aware of your surroundings and avoid distractions on your phone.",
  "Keep your phone charged and a power bank handy.",
];

export default function Dashboard() {
  const { user } = useAuth();
  const toast = useToast();

  const [contacts, setContacts] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loadingContacts, setLoadingContacts] = useState(true);
  const [loadingAlerts, setLoadingAlerts] = useState(true);

  // Location state
  const [position, setPosition] = useState(null); // {latitude, longitude, accuracy}
  const [locating, setLocating] = useState(false);
  const [sharing, setSharing] = useState(false); // location sharing active
  const [sendingSos, setSendingSos] = useState(false);

  const loadContacts = useCallback(async () => {
    setLoadingContacts(true);
    try {
      const { data } = await api.get("/contacts");
      setContacts(data);
    } catch (err) {
      toast.error(err.message || "Could not load contacts");
    } finally {
      setLoadingContacts(false);
    }
  }, [toast]);

  const loadAlerts = useCallback(async () => {
    setLoadingAlerts(true);
    try {
      const { data } = await api.get("/alerts");
      setAlerts(data);
    } catch (err) {
      toast.error(err.message || "Could not load alerts");
    } finally {
      setLoadingAlerts(false);
    }
  }, [toast]);

  useEffect(() => {
    loadContacts();
    loadAlerts();
  }, [loadContacts, loadAlerts]);

  // ---- Location ----
  const locateMe = async () => {
    if (!isGeolocationAvailable()) {
      toast.error("Geolocation is not supported by this browser.");
      return;
    }
    setLocating(true);
    try {
      const pos = await getCurrentPosition();
      setPosition(pos);
      setSharing(false);
      toast.success("Got your current location.");
      // Persist it so backend has the latest fix.
      api.post("/location", {
        latitude: pos.latitude,
        longitude: pos.longitude,
      }).catch(() => {
        /* non-blocking */
      });
    } catch (err) {
      toast.error(err.message || "Could not get your location.");
    } finally {
      setLocating(false);
    }
  };

  const startSharing = async () => {
    if (!position) {
      await locateMe();
      return;
    }
    setSharing(true);
    toast.info(
      "Live location sharing is active. Use the Google Maps link to share it with a trusted contact."
    );
  };

  const stopSharing = () => {
    setSharing(false);
    toast.info("Location sharing turned off.");
  };

  const copyMapLink = async () => {
    if (!position) return;
    const url = googleMapsUrl(position.latitude, position.longitude);
    try {
      await navigator.clipboard.writeText(url);
      toast.success("Google Maps link copied to clipboard.");
    } catch {
      // Fallback: open the link so the user can copy manually.
      window.open(url, "_blank", "noopener");
    }
  };

  // ---- SOS ----
  const triggerSos = async () => {
    if (sendingSos) return;
    setSendingSos(true);
    let pos = position;
    if (!pos) {
      try {
        pos = await getCurrentPosition();
        setPosition(pos);
      } catch (err) {
        // Fallback: reuse the last saved location from the backend if we
        // cannot get a fresh GPS fix.
        try {
          const { data } = await api.get("/location/latest");
          pos = { latitude: data.latitude, longitude: data.longitude };
          setPosition(pos);
          toast.warning(
            (err.message || "Could not get a fresh GPS fix.") +
              " Using your last saved location instead."
          );
        } catch {
          toast.error(
            (err.message || "Could not get your location.") +
              " Please call 112 directly — the alert could not be recorded without a location."
          );
          setSendingSos(false);
          return;
        }
      }
    }

    try {
      // Save the location fix and create the alert in parallel.
      const [, alertRes] = await Promise.all([
        api.post("/location", {
          latitude: pos.latitude,
          longitude: pos.longitude,
        }).catch(() => {}),
        api.post("/alerts", {
          latitude: pos.latitude,
          longitude: pos.longitude,
        }),
      ]);

      // The backend returns the alert (with nested notifications + delivery) and a note.
      const alertObj = alertRes.data?.alert;
      const note = alertRes.data?.note;
      const delivery = alertObj?.delivery;
      const notifications = alertObj?.notifications || [];
      const total = delivery?.total ?? notifications.length;
      const failed = delivery?.failed ?? 0;
      const ok = (delivery?.sent ?? 0) + (delivery?.delivered ?? 0);

      if (total === 0) {
        toast.warning(note || "Alert recorded, but you have no trusted contacts to notify. Add contacts and call 112.");
      } else if (failed === total) {
        toast.error(note || `Emergency alert recorded, but SMS delivery failed for all ${failed} contact(s). Call 112 directly.`);
      } else {
        toast.success(note || `Emergency alert recorded. SMS sent to ${ok} of ${total} contact(s). Call 112 to confirm.`);
      }
      await loadAlerts();
      setSharing(true);
    } catch (err) {
      toast.error(err.message || "Failed to record your emergency alert.");
    } finally {
      setSendingSos(false);
    }
  };

  const cancelAlert = async (alert) => {
    try {
      await api.patch(`/alerts/${alert.id}/status`, { status: "cancelled" });
      toast.success("Alert cancelled.");
      loadAlerts();
    } catch (err) {
      toast.error(err.message || "Could not cancel the alert.");
    }
  };

  const recentAlerts = alerts.slice(0, 5);
  const topContacts = contacts.slice(0, 3);

  return (
    <div className="dashboard">
      <div className="page-head">
        <div>
          <h1 className="page-title">Hello, {user?.name?.split(" ")[0] || "there"}</h1>
          <p className="page-subtitle">Stay safe. Your dashboard is ready.</p>
        </div>
        <div className={`sharing-pill ${sharing ? "active" : ""}`}>
          <span className="sharing-dot" />
          {sharing ? "Location sharing on" : "Location sharing off"}
        </div>
      </div>

      <div className="dashboard-grid">
        {/* SOS */}
        <section className="card sos-card">
          <div className="card-head">
            <h2 className="card-title">
              <Siren size={18} /> Emergency SOS
            </h2>
          </div>
          <SOSButton onTrigger={triggerSos} sending={sendingSos} />
          <p className="sos-note">
            <AlertTriangle size={14} /> This app records alerts locally and does not replace
            calling emergency services directly. Always call 112 in a real emergency.
          </p>
        </section>

        {/* Location */}
        <section className="card location-card">
          <div className="card-head">
            <h2 className="card-title">
              <MapPin size={18} /> Your location
            </h2>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={locateMe}
              disabled={locating}
            >
              <LocateFixed size={15} /> {locating ? "Locating…" : "Find me"}
            </button>
          </div>

          {position ? (
            <>
              <LocationMap
                latitude={position.latitude}
                longitude={position.longitude}
                label="You are here"
              />
              <div className="location-coords">
                <div className="coord-row">
                  <span className="coord-label">Latitude</span>
                  <span className="coord-value">{position.latitude.toFixed(5)}</span>
                </div>
                <div className="coord-row">
                  <span className="coord-label">Longitude</span>
                  <span className="coord-value">{position.longitude.toFixed(5)}</span>
                </div>
                {position.accuracy != null && (
                  <div className="coord-row">
                    <span className="coord-label">Accuracy</span>
                    <span className="coord-value">±{Math.round(position.accuracy)} m</span>
                  </div>
                )}
              </div>
              <div className="location-actions">
                {sharing ? (
                  <button type="button" className="btn btn-ghost btn-sm" onClick={stopSharing}>
                    Stop sharing
                  </button>
                ) : (
                  <button type="button" className="btn btn-primary btn-sm" onClick={startSharing}>
                    <Share2 size={15} /> Share location
                  </button>
                )}
                <button type="button" className="btn btn-ghost btn-sm" onClick={copyMapLink}>
                  <Share2 size={15} /> Copy map link
                </button>
                <a
                  href={googleMapsUrl(position.latitude, position.longitude)}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-ghost btn-sm"
                >
                  <ExternalLink size={15} /> Google Maps
                </a>
              </div>
            </>
          ) : (
            <div className="location-empty">
              <MapPin size={30} />
              <p>Press “Find me” to detect and display your current location.</p>
              {!isGeolocationAvailable() && (
                <p className="location-unavailable">
                  Geolocation is not available in this browser.
                </p>
              )}
            </div>
          )}
        </section>

        {/* Trusted contacts */}
        <section className="card contacts-card">
          <div className="card-head">
            <h2 className="card-title">
              <Users size={18} /> Trusted contacts
            </h2>
            <Link to="/contacts" className="btn btn-ghost btn-sm">
              Manage
            </Link>
          </div>
          {loadingContacts ? (
            <p className="muted">Loading contacts…</p>
          ) : topContacts.length === 0 ? (
            <div className="empty-state">
              <Users size={26} />
              <p>No contacts yet.</p>
              <Link to="/contacts" className="btn btn-primary btn-sm">
                Add a contact
              </Link>
            </div>
          ) : (
            <ul className="mini-contacts">
              {topContacts.map((c) => (
                <li key={c.id} className="mini-contact">
                  <div className="mini-contact-info">
                    <span className="mini-contact-name">{c.name}</span>
                    <span className="mini-contact-phone">{c.phone}</span>
                  </div>
                  <a
                    href={`tel:${c.phone}`}
                    className="icon-btn"
                    aria-label={`Call ${c.name}`}
                    title="Quick call"
                  >
                    <Phone size={16} />
                  </a>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Recent alerts */}
        <section className="card alerts-card">
          <div className="card-head">
            <h2 className="card-title">
              <Siren size={18} /> Recent alerts
            </h2>
            <Link to="/alerts" className="btn btn-ghost btn-sm">
              View all
            </Link>
          </div>
          <AlertHistory
            alerts={recentAlerts}
            loading={loadingAlerts}
            onCancel={cancelAlert}
          />
        </section>

        {/* Safety tips */}
        <section className="card tips-card">
          <div className="card-head">
            <h2 className="card-title">
              <LifeBuoy size={18} /> Safety tips
            </h2>
          </div>
          <ul className="tips-list">
            {SAFETY_TIPS.map((t) => (
              <li key={t}>
                <LifeBuoy size={15} /> {t}
              </li>
            ))}
          </ul>
          <Link to="/resources" className="btn btn-ghost btn-sm">
            More resources
          </Link>
        </section>

        {/* Quick resources */}
        <section className="card resources-card">
          <div className="card-head">
            <h2 className="card-title">
              <LifeBuoy size={18} /> Quick emergency numbers
            </h2>
          </div>
          <div className="quick-contacts">
            <a href="tel:112" className="quick-contact emergency">
              <span className="qc-label">Emergency</span>
              <span className="qc-number">112</span>
              <Phone size={16} />
            </a>
            <a href="tel:181" className="quick-contact">
              <span className="qc-label">Women&apos;s helpline</span>
              <span className="qc-number">181</span>
              <Phone size={16} />
            </a>
          </div>
        </section>
      </div>
    </div>
  );
}
