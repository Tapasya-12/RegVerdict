import { useState } from "react";
import { API_BASE } from "../api";

// Reached via a plain URL (?token=...) printed to the server console by
// request_password_reset() — there's no router in this app, App.jsx decides
// to render this component based on window.location alone.
export default function ResetPassword({ token, onDone }) {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (submitting) return;
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/confirm-reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || "This reset link is invalid or has expired.");
      }
      onDone();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="ambient"></div>
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="auth-wordmark">
          Reg<em>Verdict</em>
        </div>
        <div className="auth-sub">Set a new password</div>

        <div className="auth-field">
          <label htmlFor="reset-password">New password</label>
          <input
            id="reset-password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <div className="auth-field">
          <label htmlFor="reset-password-confirm">Confirm new password</label>
          <input
            id="reset-password-confirm"
            type="password"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </div>

        {error && <p className="auth-error">{error}</p>}

        <button className="auth-submit-btn" type="submit" disabled={submitting}>
          {submitting ? "Please wait…" : "Set new password"}
        </button>
      </form>
    </div>
  );
}
