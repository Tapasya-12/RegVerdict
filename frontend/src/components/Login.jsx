import { useState } from "react";
import { API_BASE, setToken } from "../api";

export default function Login({ onLoginSuccess }) {
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Login/signup happen before a token exists, so they deliberately call
  // fetch() directly rather than apiFetch() — there's nothing to attach
  // yet, and a failed login attempt shouldn't trip the global 401 handler.
  async function doLogin(user, pass) {
    const body = new URLSearchParams();
    body.set("username", user);
    body.set("password", pass);
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || "Incorrect username or password.");
    }
    setToken(data.access_token);
    onLoginSuccess();
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (submitting) return;
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "signup") {
        const res = await fetch(`${API_BASE}/api/auth/signup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, email, password }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(data.detail || "Could not create account.");
        }
        // Sign-up succeeded — log straight in rather than making the user
        // re-type their credentials on a second screen.
        await doLogin(username, password);
      } else {
        await doLogin(username, password);
      }
    } catch (err) {
      setError(err.message || "Could not reach the compliance engine — check that the backend is running.");
    } finally {
      setSubmitting(false);
    }
  }

  function switchMode(next) {
    setMode(next);
    setError(null);
  }

  return (
    <div className="auth-screen">
      <div className="ambient"></div>
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="auth-wordmark">
          Reg<em>Verdict</em>
        </div>
        <div className="auth-sub">Compliance Copilot</div>

        <div className="auth-field">
          <label htmlFor="auth-username">Username</label>
          <input
            id="auth-username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>

        {mode === "signup" && (
          <div className="auth-field">
            <label htmlFor="auth-email">Email</label>
            <input
              id="auth-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
        )}

        <div className="auth-field">
          <label htmlFor="auth-password">Password</label>
          <input
            id="auth-password"
            type="password"
            autoComplete={mode === "signup" ? "new-password" : "current-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {error && <p className="auth-error">{error}</p>}

        <button className="auth-submit-btn" type="submit" disabled={submitting}>
          {submitting ? "Please wait…" : mode === "signup" ? "Create account" : "Log in"}
        </button>

        <div className="auth-switch">
          {mode === "login" ? (
            <>
              No account?{" "}
              <button type="button" className="auth-switch-link" onClick={() => switchMode("signup")}>
                Sign up
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button type="button" className="auth-switch-link" onClick={() => switchMode("login")}>
                Log in
              </button>
            </>
          )}
        </div>
      </form>
    </div>
  );
}
