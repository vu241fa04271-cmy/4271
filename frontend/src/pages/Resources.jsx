import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  BookOpen,
  LifeBuoy,
  Phone,
  ShieldCheck,
  Users,
} from "lucide-react";

import api from "../services/api.js";
import { useToast } from "../components/Toast.jsx";

const HELPLINES = [
  { label: "Emergency (All India)", number: "112", note: "Police, fire, ambulance." },
  { label: "Women's Helpline", number: "181", note: "24x7 support for women in distress." },
  { label: "Police", number: "100", note: "Police control room." },
  { label: "Ambulance", number: "108", note: "Emergency medical services." },
  { label: "Child Helpline", number: "1098", note: "For children in need of care." },
  { label: "Cyber Crime", number: "1930", note: "Report financial cyber fraud." },
];

const PREPAREDNESS = [
  "Memorize or speed-dial 112 and your trusted contacts.",
  "Carry a charged phone and a small power bank.",
  "Before traveling alone, share your live location with someone you trust.",
  "Note nearby police stations and well-lit routes.",
  "Keep personal safety apps and emergency SOS features enabled.",
  "Trust your instincts — leave a situation that feels unsafe.",
];

const SAFETY_TIPS = [
  "Stay alert to your surroundings; avoid being absorbed in your phone in unfamiliar areas.",
  "Use busy, well-lit streets and avoid shortcuts through isolated areas at night.",
  "Share your trip and expected arrival time with a trusted contact.",
  "Use ride-share trip sharing features when available.",
  "Carry a personal safety alarm or whistle if possible.",
  "If followed, head toward a public place or a police station and call for help.",
];

export default function Resources() {
  const toast = useToast();
  const [contacts, setContacts] = useState([]);

  useEffect(() => {
    api
      .get("/contacts")
      .then(({ data }) => setContacts(data))
      .catch((err) => toast.error(err.message || "Could not load contacts"));
  }, [toast]);

  return (
    <div className="page resources">
      <div className="page-head">
        <div>
          <h1 className="page-title">Safety Resources</h1>
          <p className="page-subtitle">
            Emergency numbers, preparedness guidance, and safety tips.
          </p>
        </div>
      </div>

      <div className="alert-banner">
        <AlertTriangle size={18} />
        <p>
          <strong>Important:</strong> This app records alerts and shares your location, but it
          does <strong>not</strong> replace contacting emergency services. In a real emergency,
          always call <strong>112</strong> directly.
        </p>
      </div>

      {/* Helplines */}
      <section className="card">
        <div className="card-head">
          <h2 className="card-title">
            <Phone size={18} /> Emergency helpline numbers (India)
          </h2>
        </div>
        <div className="helpline-grid">
          {HELPLINES.map((h) => (
            <a key={h.label} href={`tel:${h.number}`} className="helpline-card">
              <div className="helpline-top">
                <span className="helpline-label">{h.label}</span>
                <Phone size={16} />
              </div>
              <span className="helpline-number">{h.number}</span>
              <span className="helpline-note">{h.note}</span>
            </a>
          ))}
        </div>
      </section>

      <div className="resources-grid">
        {/* Preparedness */}
        <section className="card">
          <div className="card-head">
            <h2 className="card-title">
              <ShieldCheck size={18} /> Emergency preparedness
            </h2>
          </div>
          <ul className="tips-list">
            {PREPAREDNESS.map((t) => (
              <li key={t}>
                <ShieldCheck size={15} /> {t}
              </li>
            ))}
          </ul>
        </section>

        {/* Safety tips */}
        <section className="card">
          <div className="card-head">
            <h2 className="card-title">
              <BookOpen size={18} /> Women&apos;s safety tips
            </h2>
          </div>
          <ul className="tips-list">
            {SAFETY_TIPS.map((t) => (
              <li key={t}>
                <BookOpen size={15} /> {t}
              </li>
            ))}
          </ul>
        </section>

        {/* Quick contacts */}
        <section className="card">
          <div className="card-head">
            <h2 className="card-title">
              <Users size={18} /> Quick access to your contacts
            </h2>
            <Link to="/contacts" className="btn btn-ghost btn-sm">
              Manage
            </Link>
          </div>
          {contacts.length === 0 ? (
            <div className="empty-state">
              <Users size={26} />
              <p>No contacts added yet.</p>
            </div>
          ) : (
            <ul className="mini-contacts">
              {contacts.map((c) => (
                <li key={c.id} className="mini-contact">
                  <div className="mini-contact-info">
                    <span className="mini-contact-name">{c.name}</span>
                    <span className="mini-contact-phone">{c.phone}</span>
                  </div>
                  <a href={`tel:${c.phone}`} className="icon-btn" aria-label={`Call ${c.name}`}>
                    <Phone size={16} />
                  </a>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <div className="resource-cta">
        <LifeBuoy size={20} />
        <span>Need to alert someone now?</span>
        <Link to="/dashboard" className="btn btn-primary btn-sm">
          Go to SOS dashboard
        </Link>
      </div>
    </div>
  );
}
