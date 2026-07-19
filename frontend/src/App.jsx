import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar";
import Workspace from "./components/Workspace";
import PolicyDiff from "./components/PolicyDiff";
import CompareJurisdictions from "./components/CompareJurisdictions";
import AuditTrail from "./components/AuditTrail";
import ClauseGraphView from "./components/ClauseGraphView";
import Login from "./components/Login";
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
  };
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!getToken());
  const [activeTool, setActiveTool] = useState("workspace");
  const [workspaceResetKey, setWorkspaceResetKey] = useState(0);
  const [recentChats, setRecentChats] = useState([]);
  const [pendingFill, setPendingFill] = useState(null);
  const [indexedChunks, setIndexedChunks] = useState(null);
  const [regulators, setRegulators] = useState([]);

  // Any apiFetch() call anywhere in the app that gets a 401 back (expired
  // token, cleared token, tampered token) routes here — bounce to the login
  // screen instead of leaving the app sitting on a silently broken tool.
  useEffect(() => {
    onUnauthorized(() => setIsAuthenticated(false));
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
  }

  function handleNewCheck() {
    setWorkspaceResetKey((k) => k + 1);
  }

  function handleQuerySubmitted() {
    // check_compliance already wrote the recent-query row server-side (that's
    // the whole point of centralizing this) — just pull the fresh list.
    refreshRecentQueries();
  }

  function handleSelectRecent(fullQuery) {
    if (activeTool !== "workspace") setActiveTool("workspace");
    setPendingFill({ text: fullQuery, nonce: Date.now() });
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

  if (!isAuthenticated) {
    return <Login onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  return (
    <>
      <div className="ambient"></div>
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
            pendingFill={pendingFill}
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
