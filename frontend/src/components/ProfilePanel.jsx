import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { fetchMe, changePassword } from "../api";

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
}

// The one "account stuff" surface — profile identity, real usage stats, and
// the only Change-password/Log-out actions in the app, so there's never a
// second, inconsistent settings surface to keep in sync with this one.
// Rendered via a portal because the sidebar has a CSS `transform` (for the
// mobile drawer), which makes it the containing block for any descendant
// `position:fixed` element — without the portal this modal would render
// pinned to the sidebar's own bounds instead of centered in the viewport
// (a real bug hit and fixed the same way earlier in this project).
export default function ProfilePanel({ onClose, onLogout }) {
  const [me, setMe] = useState(null);
  const [meError, setMeError] = useState(null);

  useEffect(() => {
    fetchMe()
      .then(setMe)
      .catch((err) => setMeError(err.message));
  }, []);

  useEffect(() => {
    function handleEscape(e) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [passwordSubmitting, setPasswordSubmitting] = useState(false);

  function handlePasswordSubmit(e) {
    e.preventDefault();
    setPasswordError(null);
    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords do not match.");
      return;
    }
    setPasswordSubmitting(true);
    changePassword(currentPassword, newPassword)
      .then(() => {
        setPasswordSuccess(true);
        setShowPasswordForm(false);
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
      })
      .catch((err) => setPasswordError(err.message))
      .finally(() => setPasswordSubmitting(false));
  }

  return createPortal(
    <div className="profile-modal-backdrop" onClick={onClose} role="presentation">
      <div
        className="profile-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Profile"
      >
        <div className="profile-modal-header">
          <span className="profile-modal-title">Profile</span>
          <button className="profile-modal-close" onClick={onClose} aria-label="Close profile">
            ✕
          </button>
        </div>

        {meError && <p className="auth-error">{meError}</p>}

        {me && (
          <>
            <div className="profile-identity">
              <span className="profile-avatar-lg">{me.username[0].toUpperCase()}</span>
              <div className="profile-identity-text">
                <p className="profile-username-lg">{me.username}</p>
                <p className="profile-email">{me.email}</p>
              </div>
            </div>

            <div className="profile-stats">
              <div className="profile-stat">
                <span className="profile-stat-label">Member since</span>
                <span className="profile-stat-value">{formatDate(me.created_at)}</span>
              </div>
              <div className="profile-stat">
                <span className="profile-stat-label">Compliance checks run</span>
                <span className="profile-stat-value">{me.total_checks}</span>
              </div>
            </div>

            <div className="profile-divider"></div>

            {!showPasswordForm ? (
              <button
                className="profile-link-btn"
                onClick={() => {
                  setShowPasswordForm(true);
                  setPasswordSuccess(false);
                }}
              >
                Change password
              </button>
            ) : (
              <form className="profile-password-form" onSubmit={handlePasswordSubmit}>
                <input
                  type="password"
                  required
                  placeholder="Current password"
                  className="profile-input"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                />
                <input
                  type="password"
                  required
                  minLength={8}
                  placeholder="New password (min 8 characters)"
                  className="profile-input"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
                <input
                  type="password"
                  required
                  placeholder="Confirm new password"
                  className="profile-input"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
                {passwordError && <p className="auth-error">{passwordError}</p>}
                <div className="profile-password-actions">
                  <button type="submit" className="profile-submit-btn" disabled={passwordSubmitting}>
                    {passwordSubmitting ? "Updating…" : "Update password"}
                  </button>
                  <button
                    type="button"
                    className="profile-link-btn"
                    onClick={() => {
                      setShowPasswordForm(false);
                      setPasswordError(null);
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
            {passwordSuccess && <p className="profile-success">Password updated.</p>}

            <div className="profile-divider"></div>

            <button className="profile-logout-btn" onClick={onLogout}>
              Log out
            </button>
          </>
        )}
      </div>
    </div>,
    document.body
  );
}
