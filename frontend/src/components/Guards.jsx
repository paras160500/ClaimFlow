import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ShieldOff } from "lucide-react";

export function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

export function RequireRole({ roles, children }) {
  const { hasRole } = useAuth();
  if (!hasRole(...roles)) {
    return (
      <div className="page">
        <div className="empty-state">
          <ShieldOff />
          <div className="empty-state__title">You don't have access to this page</div>
          <div>This section is restricted to: {roles.join(", ")}</div>
        </div>
      </div>
    );
  }
  return children;
}
