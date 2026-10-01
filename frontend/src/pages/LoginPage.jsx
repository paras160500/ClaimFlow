import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck, ArrowRight } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const DEMO_ACCOUNTS = [
  { role: "Admin", email: "admin@claimflow.demo", password: "ClaimFlow!Admin1" },
  { role: "Investigator", email: "investigator@claimflow.demo", password: "ClaimFlow!Invest1" },
  { role: "Reviewer", email: "reviewer@claimflow.demo", password: "ClaimFlow!Review1" },
];

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    const result = await login(email, password);
    setLoading(false);
    if (result.ok) {
      navigate("/", { replace: true });
    } else {
      setError(result.error);
    }
  }

  function useDemo(account) {
    setEmail(account.email);
    setPassword(account.password);
  }

  return (
    <div className="login-screen">
      <div className="login-screen__side">
        <div className="login-side__brand">
          <div className="sidebar__mark">CF</div>
          <div style={{ color: "var(--text-on-ink)", fontFamily: "var(--font-display)", fontWeight: 600 }}>
            ClaimFlow
          </div>
        </div>

        <div className="login-side__quote">
          Risk models, business rules, and claim history —{" "}
          <span>in one place, for every claim your team reviews.</span>
        </div>

        <div className="login-side__foot">
          Internal claims investigation platform · Employee access only
        </div>
      </div>

      <div className="login-screen__form-side">
        <div className="login-card">
          <h1>Sign in to ClaimFlow</h1>
          <p className="login-card__sub">Enter your employee credentials to continue.</p>

          {error && <div className="login-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="email">Work email</label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@claimflow.demo"
                autoComplete="email"
              />
            </div>
            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
              />
            </div>
            <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
              {loading ? "Signing in…" : "Sign in"} <ArrowRight />
            </button>
          </form>

          <div className="demo-accounts">
            <div className="demo-accounts__title">
              <ShieldCheck size={12} style={{ verticalAlign: "-1px", marginRight: 5 }} />
              Demo accounts (Stage 3 seed data)
            </div>
            {DEMO_ACCOUNTS.map((acc) => (
              <button key={acc.role} type="button" className="demo-account-btn" onClick={() => useDemo(acc)}>
                <span>{acc.role}</span>
                <span className="text-muted mono">{acc.email}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
