import { useCallback, useEffect, useState } from "react";
import { Phone, Plus, UserPlus, X } from "lucide-react";

import api from "../services/api.js";
import { useToast } from "../components/Toast.jsx";
import ContactCard from "../components/ContactCard.jsx";

const EMPTY = { name: "", phone: "", email: "" };

export default function Contacts() {
  const toast = useToast();
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null); // contact being edited, or null for new
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/contacts");
      setContacts(data);
    } catch (err) {
      toast.error(err.message || "Could not load contacts");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    load();
  }, [load]);

  const openAdd = () => {
    setEditing(null);
    setForm(EMPTY);
    setErrors({});
    setShowForm(true);
  };

  const openEdit = (contact) => {
    setEditing(contact);
    setForm({ name: contact.name, phone: contact.phone, email: contact.email || "" });
    setErrors({});
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditing(null);
    setForm(EMPTY);
    setErrors({});
  };

  const validate = () => {
    const errs = {};
    if (!form.name.trim()) errs.name = "Name is required";
    if (!form.phone.trim()) errs.phone = "Phone is required";
    if (form.email.trim() && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email.trim())) {
      errs.email = "Enter a valid email";
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setSaving(true);
    const payload = {
      name: form.name.trim(),
      phone: form.phone.trim(),
      email: form.email.trim(),
    };
    try {
      if (editing) {
        const { data } = await api.put(`/contacts/${editing.id}`, payload);
        setContacts((prev) => prev.map((c) => (c.id === data.id ? data : c)));
        toast.success("Contact updated.");
      } else {
        const { data } = await api.post("/contacts", payload);
        setContacts((prev) => [...prev, data]);
        toast.success("Contact added.");
      }
      closeForm();
    } catch (err) {
      toast.error(err.message || "Could not save contact");
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async (contact) => {
    if (!window.confirm(`Delete ${contact.name}? This cannot be undone.`)) return;
    try {
      await api.delete(`/contacts/${contact.id}`);
      setContacts((prev) => prev.filter((c) => c.id !== contact.id));
      toast.success("Contact deleted.");
    } catch (err) {
      toast.error(err.message || "Could not delete contact");
    }
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">Trusted Contacts</h1>
          <p className="page-subtitle">
            People who should be reached quickly in an emergency.
          </p>
        </div>
        <button type="button" className="btn btn-primary" onClick={openAdd}>
          <Plus size={16} /> Add contact
        </button>
      </div>

      {loading ? (
        <p className="muted">Loading contacts…</p>
      ) : contacts.length === 0 ? (
        <div className="empty-state big">
          <UserPlus size={34} />
          <h3>No trusted contacts yet</h3>
          <p>Add the people you would call in an emergency so they're one tap away.</p>
          <button type="button" className="btn btn-primary" onClick={openAdd}>
            <Plus size={16} /> Add your first contact
          </button>
        </div>
      ) : (
        <div className="contacts-grid">
          {contacts.map((c) => (
            <ContactCard key={c.id} contact={c} onEdit={openEdit} onDelete={onDelete} />
          ))}
        </div>
      )}

      {/* Slide-over form */}
      {showForm && (
        <div className="drawer-overlay" onClick={closeForm}>
          <div
            className="drawer"
            role="dialog"
            aria-modal="true"
            aria-label={editing ? "Edit contact" : "Add contact"}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="drawer-head">
              <h2>{editing ? "Edit contact" : "Add contact"}</h2>
              <button type="button" className="icon-btn" onClick={closeForm} aria-label="Close">
                <X size={18} />
              </button>
            </div>
            <form className="auth-form" onSubmit={onSubmit} noValidate>
              <div className="form-group">
                <label htmlFor="c-name">Name</label>
                <input
                  id="c-name"
                  name="name"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="e.g. Mom"
                  aria-invalid={!!errors.name}
                />
                {errors.name && <span className="field-error">{errors.name}</span>}
              </div>
              <div className="form-group">
                <label htmlFor="c-phone">Phone</label>
                <input
                  id="c-phone"
                  name="phone"
                  value={form.phone}
                  onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                  placeholder="+91 98XXXXXXXX"
                  aria-invalid={!!errors.phone}
                />
                {errors.phone && <span className="field-error">{errors.phone}</span>}
              </div>
              <div className="form-group">
                <label htmlFor="c-email">Email (optional)</label>
                <input
                  id="c-email"
                  name="email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  placeholder="contact@example.com"
                  aria-invalid={!!errors.email}
                />
                {errors.email && <span className="field-error">{errors.email}</span>}
              </div>
              <div className="drawer-actions">
                <button type="button" className="btn btn-ghost" onClick={closeForm}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  <Phone size={15} /> {saving ? "Saving…" : editing ? "Save changes" : "Add contact"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
