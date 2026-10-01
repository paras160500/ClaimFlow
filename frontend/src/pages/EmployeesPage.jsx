import { useEffect, useState } from "react";
import { UserPlus, X, Users } from "lucide-react";
import { api, apiErrorMessage } from "../api/client";
import { Loader, Banner, EmptyState, formatDate } from "../components/Common";

const ROLES = ["ADMIN", "INVESTIGATOR", "REVIEWER"];

export default function EmployeesPage() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/api/employees");
      setEmployees(data.employees || []);
    } catch (err) {
      setError(apiErrorMessage(err, "Could not load employees."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-header__eyebrow">Administration</div>
          <h1>Employees</h1>
          <div className="page-header__meta">{employees.length} employee accounts</div>
        </div>
        <button className="btn btn-primary" onClick={() => setModalOpen(true)}>
          <UserPlus /> New employee
        </button>
      </div>

      {error && <Banner type="error">{error}</Banner>}

      <div className="card">
        {loading ? (
          <Loader label="Loading employees…" />
        ) : employees.length === 0 ? (
          <EmptyState title="No employees yet" hint="Add your first employee account." />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Department</th>
                <th>Joined</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((emp) => (
                <tr key={emp.id}>
                  <td style={{ fontWeight: 600 }}>{emp.name}</td>
                  <td className="text-secondary">{emp.email}</td>
                  <td>
                    <span className="badge badge-accent">{emp.role}</span>
                  </td>
                  <td className="text-secondary">{emp.department || "—"}</td>
                  <td className="text-secondary">{formatDate(emp.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {modalOpen && (
        <AddEmployeeModal
          onClose={() => setModalOpen(false)}
          onCreated={() => {
            setModalOpen(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function AddEmployeeModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "INVESTIGATOR", department: "" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await api.post("/api/employees", form);
      onCreated();
    } catch (err) {
      setError(apiErrorMessage(err, "Could not create employee."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <div className="card__title">
            <Users /> New employee
          </div>
          <button className="icon-btn" onClick={onClose}>
            <X />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal__body">
            {error && <Banner type="error">{error}</Banner>}
            <div className="field">
              <label>Full name</label>
              <input required value={form.name} onChange={(e) => update("name", e.target.value)} />
            </div>
            <div className="field">
              <label>Work email</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
              />
            </div>
            <div className="field">
              <label>Temporary password</label>
              <input
                type="password"
                required
                minLength={8}
                value={form.password}
                onChange={(e) => update("password", e.target.value)}
              />
            </div>
            <div className="field">
              <label>Role</label>
              <select
                className="select-input"
                style={{ width: "100%" }}
                value={form.role}
                onChange={(e) => update("role", e.target.value)}
              >
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Department (optional)</label>
              <input value={form.department} onChange={(e) => update("department", e.target.value)} />
            </div>
          </div>
          <div className="modal__footer">
            <button type="button" className="btn btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Creating…" : "Create employee"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
