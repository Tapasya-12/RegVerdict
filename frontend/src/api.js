// Central fetch wrapper — every authenticated call in the app should go
// through apiFetch() so the Authorization header and the 401 -> logout
// redirect are never missed at an individual call site.

// 127.0.0.1, not "localhost" — on machines with Docker Desktop's WSL2
// backend running, its wslrelay process binds the IPv6 loopback ([::1]) on
// common dev ports (8000 among them), and "localhost" can resolve to
// either address. That produces intermittent connection failures having
// nothing to do with this app — 127.0.0.1 is unambiguous IPv4 and never
// collides with it (confirmed via netstat: only this API's own uvicorn
// process binds 127.0.0.1:8000, wslrelay only takes the IPv6 side).
export const API_BASE = "http://127.0.0.1:8000";

const TOKEN_KEY = "regverdict_token";

// localStorage is fine for this project's local-dev scope. An httpOnly
// cookie would be more secure against XSS token theft for a production
// deployment, but that's out of scope here.
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

let unauthorizedHandler = () => {};

// App.jsx registers its "kick back to login" callback here once, at mount.
export function onUnauthorized(fn) {
  unauthorizedHandler = fn;
}

export async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    unauthorizedHandler();
  }

  return res;
}

// Re-runs the compliance report fresh server-side (POST /api/export_report)
// and triggers a browser download of the resulting .docx — used by the
// "Export as Word" button wherever a verdict renders.
export async function exportReportDocx(policyText) {
  const res = await apiFetch("/api/export_report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ policy_text: policyText }),
  });
  if (!res.ok) {
    let detail = `export_report returned ${res.status}`;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch {
      // response wasn't JSON (e.g. a network-level error page) — keep the generic message
    }
    throw new Error(detail);
  }

  const disposition = res.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : `regverdict_report_${Date.now()}.docx`;

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
