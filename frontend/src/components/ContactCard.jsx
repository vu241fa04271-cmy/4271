import { Mail, Pencil, Phone, Trash2, User } from "lucide-react";

export default function ContactCard({ contact, onEdit, onDelete }) {
  return (
    <div className="card contact-card">
      <div className="contact-avatar">
        <User size={20} />
      </div>
      <div className="contact-info">
        <h4 className="contact-name">{contact.name}</h4>
        <a href={`tel:${contact.phone}`} className="contact-line contact-phone">
          <Phone size={14} /> {contact.phone}
        </a>
        {contact.email && (
          <a
            href={`mailto:${contact.email}`}
            className="contact-line contact-email"
          >
            <Mail size={14} /> {contact.email}
          </a>
        )}
      </div>
      <div className="contact-actions">
        <a
          href={`tel:${contact.phone}`}
          className="btn btn-primary btn-sm"
          aria-label={`Call ${contact.name}`}
          title="Quick call"
        >
          <Phone size={15} /> Call
        </a>
        <button
          type="button"
          className="icon-btn"
          aria-label={`Edit ${contact.name}`}
          title="Edit"
          onClick={() => onEdit(contact)}
        >
          <Pencil size={16} />
        </button>
        <button
          type="button"
          className="icon-btn icon-btn-danger"
          aria-label={`Delete ${contact.name}`}
          title="Delete"
          onClick={() => onDelete(contact)}
        >
          <Trash2 size={16} />
        </button>
      </div>
    </div>
  );
}
