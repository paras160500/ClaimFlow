import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { RequireAuth, RequireRole } from "./components/Guards";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import ClaimsListPage from "./pages/ClaimsListPage";
import ClaimDetailPage from "./pages/ClaimDetailPage";
import InvestigationsPage from "./pages/InvestigationsPage";
import EmployeesPage from "./pages/EmployeesPage";
import AuditLogPage from "./pages/AuditLogPage";

function LoginRoute() {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) return <Navigate to="/" replace />;
  return <LoginPage />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginRoute />} />

          <Route
            element={
              <RequireAuth>
                <Layout />
              </RequireAuth>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/claims" element={<ClaimsListPage />} />
            <Route path="/claims/:claimId" element={<ClaimDetailPage />} />
            <Route path="/investigations" element={<InvestigationsPage />} />
            <Route
              path="/employees"
              element={
                <RequireRole roles={["ADMIN"]}>
                  <EmployeesPage />
                </RequireRole>
              }
            />
            <Route
              path="/audit-log"
              element={
                <RequireRole roles={["ADMIN"]}>
                  <AuditLogPage />
                </RequireRole>
              }
            />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
