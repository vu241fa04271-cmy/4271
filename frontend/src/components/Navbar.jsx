import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  LifeBuoy,
  Siren,
  LogOut,
  Shield,
  Menu,
  X,
} from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/contacts", label: "Contacts", icon: Users },
  { to: "/alerts", label: "Alerts", icon: Siren },
  { to: "/resources", label: "Resources", icon: LifeBuoy },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    setOpen(false);
    navigate("/login");
  };

  const close = () => setOpen(false);

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link to={user ? "/dashboard" : "/login"} className="brand" onClick={close}>
          <Shield size={22} className="brand-icon" />
          <span className="brand-text">
            <span className="brand-title">SafeHer</span>
            <span className="brand-sub">Emergency Alert</span>
          </span>
        </Link>

        {user && (
          <button
            type="button"
            className="nav-toggle"
            aria-label="Toggle navigation"
            aria-expanded={open}
            onClick={() => setOpen((o) => !o)}
          >
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>
        )}

        {user && (
          <nav className={`nav-links ${open ? "open" : ""}`}>
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className="nav-link"
                onClick={close}
              >
                <Icon size={18} />
                <span>{label}</span>
              </NavLink>
            ))}
            <div className="nav-user">
              <span className="nav-user-name">{user.name}</span>
              <button type="button" className="btn btn-ghost nav-logout" onClick={handleLogout}>
                <LogOut size={16} /> Logout
              </button>
            </div>
          </nav>
        )}

        {!user && (
          <div className="nav-auth">
            <Link to="/login" className="btn btn-ghost">Login</Link>
            <Link to="/register" className="btn btn-primary">Sign up</Link>
          </div>
        )}
      </div>
    </header>
  );
}
