// Central fetch wrapper — every authenticated call in the app should go
// through apiFetch() so the Authorization header and the 401 -> logout
// redirect are never missed at an individual call site.

export const API_BASE = "http://localhost:8000";

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
