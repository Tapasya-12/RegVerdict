import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar";
import Workspace from "./components/Workspace";
import PolicyDiff from "./components/PolicyDiff";
import CompareJurisdictions from "./components/CompareJurisdictions";
import AuditTrail from "./components/AuditTrail";
import ClauseGraphView from "./components/ClauseGraphView";
import Login from "./components/Login";
import ResetPassword from "./components/ResetPassword";
import HomeScreen from "./components/HomeScreen";
import { apiFetch, clearToken, getToken, onUnauthorized } from "./api";

// The API returns snake_case rows straight from SQLite (display_title,
// full_query, pinned as 0/1) — normalized here once so Sidebar/RecentChatRow
// can keep using the same camelCase shape they always have.
function normalizeRecentQuery(row) {
  return {
    id: row.id,
    displayTitle: row.display_title,
    fullQuery: row.full_query,
    pinned: !!row.pinned,
    messages: row.messages || [],
  };
}

// No router in this app — /reset is the one URL-addressable screen (it has
// to be, since the reset link is a real link printed to the server console),
// so it's read directly off window.location rather than pulling in a router
// dependency for a single route.
function getResetToken() {
  if (window.location.pathname !== "/reset") return null;
  return new URLSearchParams(window.location.search).get("token");
}

export default function App() {
  const [resetToken, setResetToken] = useState(getResetToken);
  const [resetJustCompleted, setResetJustCompleted] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!getToken());
  // Landing page is the default pre-auth screen; showAuth flips to the
  // Login/Signup card once the visitor picks one from the landing page (or
  // a 401 elsewhere in the app forces a re-login — see onUnauthorized below).
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [activeTool, setActiveTool] = useState("workspace");
  const [workspaceResetKey, setWorkspaceResetKey] = useState(0);
  const [recentChats, setRecentChats] = useState([]);
  const [pendingSession, setPendingSession] = useState(null);
  const [indexedChunks, setIndexedChunks] = useState(null);
  const [regulators, setRegulators] = useState([]);

  // Any apiFetch() call anywhere in the app that gets a 401 back (expired
  // token, cleared token, tampered token) routes here — bounce to the login
  // screen instead of leaving the app sitting on a silently broken tool.
  useEffect(() => {
    // A 401 anywhere means an expired/invalid session, not a fresh visit —
    // goes straight to the login form, not back to the landing page.
    onUnauthorized(() => {
      setIsAuthenticated(false);
      setShowAuth(true);
    });
  }, []);

  function refreshRecentQueries() {
    apiFetch("/api/recent_queries")
      .then((res) => {
        if (!res.ok) throw new Error(`recent_queries returned ${res.status}`);
        return res.json();
      })
      .then((rows) => setRecentChats(rows.map(normalizeRecentQuery)))
      .catch((err) => console.error("recent_queries fetch failed:", err));
  }

  useEffect(() => {
    if (!isAuthenticated) return;

    refreshRecentQueries();

    apiFetch("/api/health")
      .then((res) => {
        if (!res.ok) throw new Error(`health check returned ${res.status}`);
        return res.json();
      })
      .then((data) => setIndexedChunks(data.indexed_chunks))
      .catch((err) => console.error("Backend health check failed:", err));

    // Derived from the real corpus rather than hardcoded, so a 3rd
    // regulator being ingested doesn't require a frontend change.
    apiFetch("/api/documents")
      .then((res) => {
        if (!res.ok) throw new Error(`api/documents returned ${res.status}`);
        return res.json();
      })
      .then((docs) => {
        const prefixes = new Set(docs.map((d) => d.split("_")[0].toUpperCase()));
        setRegulators([...prefixes].sort());
      })
      .catch((err) => console.error("api/documents fetch failed:", err));
  }, [isAuthenticated]);

  function handleLogout() {
    clearToken();
    setIsAuthenticated(false);
    setShowAuth(false); // back to the landing page, not straight to the login form
  }

  function handleNewCheck() {
    // Clears the in-progress session BEFORE the remount below — otherwise
    // Workspace would mount fresh (via the key change) but its restore
    // effect would immediately re-fire against the still-set pendingSession
    // from whatever was last opened, undoing the "new check" the user asked for.
    setPendingSession(null);
    setWorkspaceResetKey((k) => k + 1);
  }

  function handleQuerySubmitted() {
    // check_compliance already wrote/updated the session's row server-side
    // (that's the whole point of centralizing this) — just pull the fresh list.
    refreshRecentQueries();
  }

  function handleSelectRecent(entry) {
    if (activeTool !== "workspace") setActiveTool("workspace");
    setPendingSession({ sessionId: entry.id, messages: entry.messages, nonce: Date.now() });
  }

  function handlePinToggle(id) {
    apiFetch(`/api/recent_queries/${id}/pin`, { method: "PATCH" })
      .then((res) => {
        if (!res.ok) throw new Error(`pin toggle returned ${res.status}`);
        refreshRecentQueries();
      })
      .catch((err) => console.error("pin toggle failed:", err));
  }

  function handleRenameChat(id, newTitle) {
    apiFetch(`/api/recent_queries/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ display_title: newTitle }),
    })
      .then((res) => {
        if (!res.ok) throw new Error(`rename returned ${res.status}`);
        refreshRecentQueries();
      })
      .catch((err) => console.error("rename failed:", err));
  }

  function handleDeleteChat(id) {
    apiFetch(`/api/recent_queries/${id}`, { method: "DELETE" })
      .then((res) => {
        if (!res.ok) throw new Error(`delete returned ${res.status}`);
        refreshRecentQueries();
      })
      .catch((err) => console.error("delete failed:", err));
  }

  if (resetToken) {
    return (
      <ResetPassword
        token={resetToken}
        onDone={() => {
          // Clear /reset?token=... from the address bar so a refresh (or
          // sharing the URL) doesn't re-show the reset form with a token
          // that's now used up.
          window.history.replaceState({}, "", "/");
          setResetToken(null);
          setResetJustCompleted(true);
          setAuthMode("login");
          setShowAuth(true); // land on the login form (with the confirmation message), not back on the landing page
        }}
      />
    );
  }

  if (!isAuthenticated) {
    if (!showAuth) {
      return (
        <HomeScreen
          onEnter={(mode) => {
            setAuthMode(mode || "login");
            setShowAuth(true);
          }}
        />
      );
    }
    return (
      <Login
        onLoginSuccess={() => setIsAuthenticated(true)}
        justResetPassword={resetJustCompleted}
        initialMode={authMode}
      />
    );
  }

  return (
    <>
      <Sidebar
        activeTool={activeTool}
        onSelectTool={setActiveTool}
        onNewCheck={handleNewCheck}
        recentChats={recentChats}
        onSelectRecent={handleSelectRecent}
        onPinToggle={handlePinToggle}
        onRename={handleRenameChat}
        onDelete={handleDeleteChat}
        indexedChunks={indexedChunks}
        regulators={regulators}
        onLogout={handleLogout}
      />
      <div className="main">
        {activeTool === "workspace" && (
          <Workspace
            key={workspaceResetKey}
            indexedChunks={indexedChunks}
            regulators={regulators}
            pendingSession={pendingSession}
            onQuerySubmitted={handleQuerySubmitted}
          />
        )}
        {activeTool === "diff" && <PolicyDiff regulators={regulators} />}
        {activeTool === "compare" && <CompareJurisdictions regulators={regulators} />}
        {activeTool === "audit" && <AuditTrail />}
        {activeTool === "graph" && <ClauseGraphView />}
      </div>
    </>
  );
}
