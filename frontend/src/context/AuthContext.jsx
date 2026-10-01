import { createContext, useContext, useState, useCallback } from "react";
import { api, apiErrorMessage } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [employee, setEmployee] = useState(() => {
    const stored = localStorage.getItem("claimflow_employee");
    return stored ? JSON.parse(stored) : null;
  });

  const login = useCallback(async (email, password) => {
    try {
      const { data } = await api.post("/api/auth/login", { email, password });
      localStorage.setItem("claimflow_token", data.access_token);
      localStorage.setItem("claimflow_employee", JSON.stringify(data.employee));
      setEmployee(data.employee);
      return { ok: true };
    } catch (err) {
      return { ok: false, error: apiErrorMessage(err, "Invalid email or password.") };
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("claimflow_token");
    localStorage.removeItem("claimflow_employee");
    setEmployee(null);
  }, []);

  const hasRole = useCallback(
    (...roles) => !!employee && roles.includes(employee.role),
    [employee]
  );

  return (
    <AuthContext.Provider value={{ employee, login, logout, hasRole, isAuthenticated: !!employee }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
