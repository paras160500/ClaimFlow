import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FileSearch,
  ClipboardList,
  Users,
  ScrollText,
  LogOut,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const initials = (name = "") =>
  name
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

export default function Sidebar() {
  const { employee, logout, hasRole } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <div className="sidebar__mark">CF</div>
        <div>
          <div className="sidebar__wordmark">ClaimFlow</div>
          <div className="sidebar__tagline">Claims Intelligence</div>
        </div>
      </div>

      <nav className="sidebar__nav">
        <NavLink to="/" end className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
          <LayoutDashboard /> Dashboard
        </NavLink>
        <NavLink to="/claims" className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
          <FileSearch /> Claims
        </NavLink>
        <NavLink
          to="/investigations"
          className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
        >
          <ClipboardList /> Investigations
        </NavLink>

        {hasRole("ADMIN") && (
          <>
            <div className="sidebar__section-label">Administration</div>
            <NavLink
              to="/employees"
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              <Users /> Employees
            </NavLink>
            <NavLink
              to="/audit-log"
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              <ScrollText /> Audit Log
            </NavLink>
          </>
        )}
      </nav>

      <div className="sidebar__footer">
        <div className="user-chip">
          <div className="user-chip__avatar">{initials(employee?.name)}</div>
          <div style={{ minWidth: 0 }}>
            <div className="user-chip__name">{employee?.name}</div>
            <div className="user-chip__role">{employee?.role}</div>
          </div>
        </div>
        <button className="logout-btn" onClick={logout}>
          <LogOut size={14} /> Sign out
        </button>
      </div>
    </aside>
  );
}
