import { useEffect, useRef, useState } from "react";
import { classForCode } from "../jurisdiction";
import { getUsernameFromToken } from "../api";
import ProfilePanel from "./ProfilePanel";

const TOOLS = [
  { id: "workspace", label: "Compliance Workspace" },
  { id: "diff", label: "Policy Diff" },
  { id: "compare", label: "Compare Jurisdictions" },
  { id: "audit", label: "Audit Trail" },
  { id: "graph", label: "Clause Graph" },
];

function RecentChatRow({ entry, onSelect, onPinToggle, onRename, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(entry.displayTitle);
  const inputRef = useRef(null);
  // Distinguishes "blurred because Escape cancelled" from "blurred because
  // Enter/click-away should save" — both end up calling the same onBlur
  // handler, so a single flag avoids a double-fire (Escape reverting the
  // draft, then blur immediately re-committing it).
  const cancelledRef = useRef(false);

  useEffect(() => {
    if (editing) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [editing]);

  function startRename() {
    setDraftTitle(entry.displayTitle);
    cancelledRef.current = false;
    setEditing(true);
  }

  function handleInputKeyDown(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      inputRef.current?.blur();
    } else if (e.key === "Escape") {
      e.preventDefault();
      cancelledRef.current = true;
      setDraftTitle(entry.displayTitle);
      inputRef.current?.blur();
    }
  }

  function handleInputBlur() {
    setEditing(false);
    if (cancelledRef.current) {
      cancelledRef.current = false;
      return;
    }
    const trimmed = draftTitle.trim();
    if (trimmed && trimmed !== entry.displayTitle) {
      onRename(entry.id, trimmed);
    }
  }

  if (editing) {
    return (
      <div className="recent-row">
        <input
          ref={inputRef}
          className="recent-rename-input"
          value={draftTitle}
          onChange={(e) => setDraftTitle(e.target.value)}
          onKeyDown={handleInputKeyDown}
          onBlur={handleInputBlur}
        />
      </div>
    );
  }

  return (
    <div className="recent-row">
      <button className="recent-item" title={entry.fullQuery} onClick={() => onSelect(entry)}>
        {entry.displayTitle}
      </button>
      <div className="recent-actions">
        <button className="recent-action" onClick={() => onPinToggle(entry.id)}>
          {entry.pinned ? "Unpin" : "Pin"}
        </button>
        <button className="recent-action" onClick={startRename}>
          Rename
        </button>
        <button className="recent-action recent-action-delete" onClick={() => onDelete(entry.id)}>
          Delete
        </button>
      </div>
    </div>
  );
}

export default function Sidebar({
  activeTool,
  onSelectTool,
  onNewCheck,
  recentChats,
  onSelectRecent,
  onPinToggle,
  onRename,
  onDelete,
  indexedChunks,
  regulators,
  onLogout,
}) {
  const pinned = recentChats.filter((e) => e.pinned);
  const recent = recentChats.filter((e) => !e.pinned);
  const username = getUsernameFromToken() || "—";
  const [profileOpen, setProfileOpen] = useState(false);

  // Below ~800px the fixed-width sidebar becomes an off-canvas drawer —
  // closed by default, opened via the top bar's hamburger, closed via the
  // backdrop or the X. `inert` (not just the transform) removes its
  // contents from the tab order while closed on mobile — a transform-
  // hidden-but-still-tabbable drawer was a real bug found and fixed in an
  // earlier accessibility pass, worth carrying forward regardless of skin.
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isDesktop, setIsDesktop] = useState(
    () => typeof window !== "undefined" && window.matchMedia("(min-width: 801px)").matches
  );

  useEffect(() => {
    const mql = window.matchMedia("(min-width: 801px)");
    const handler = (e) => setIsDesktop(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  function selectAndClose(fn) {
    return (...args) => {
      fn(...args);
      setMobileOpen(false);
    };
  }

  return (
    <>
      <div className="mobile-topbar">
        <button className="mobile-topbar-hamburger" onClick={() => setMobileOpen(true)} aria-label="Open menu">
          ☰
        </button>
        <div className="wordmark">
          Reg<span>Verdict</span>
        </div>
      </div>

      {mobileOpen && (
        <div className="mobile-backdrop" onClick={() => setMobileOpen(false)} aria-hidden="true"></div>
      )}

      <div
        className={`sidebar${mobileOpen ? " open" : ""}`}
        inert={!isDesktop && !mobileOpen ? true : undefined}
      >
        <button className="sidebar-close-btn" onClick={() => setMobileOpen(false)} aria-label="Close menu">
          ✕
        </button>

        <div className="wordmark">
          Reg<span>Verdict</span>
        </div>
        <div className="side-sub">Compliance Copilot</div>

        <button className="new-check-btn" onClick={selectAndClose(onNewCheck)}>
          New compliance check
        </button>

        <div className="nav-label">Tools</div>
        {TOOLS.map((tool) => (
          <button
            key={tool.id}
            className={`nav-item${activeTool === tool.id ? " active" : ""}`}
            onClick={selectAndClose(() => onSelectTool(tool.id))}
          >
            {tool.label}
          </button>
        ))}

        <div className="sidebar-divider"></div>

        <div className="recent-list">
          {pinned.length > 0 && (
            <>
              <div className="nav-label">Pinned</div>
              {pinned.map((entry) => (
                <RecentChatRow
                  key={entry.id}
                  entry={entry}
                  onSelect={selectAndClose(onSelectRecent)}
                  onPinToggle={onPinToggle}
                  onRename={onRename}
                  onDelete={onDelete}
                />
              ))}
            </>
          )}

          <div className="nav-label">Recent</div>
          {recent.length === 0 ? (
            <div className="recent-empty">No recent checks yet</div>
          ) : (
            recent.map((entry) => (
              <RecentChatRow
                key={entry.id}
                entry={entry}
                onSelect={selectAndClose(onSelectRecent)}
                onPinToggle={onPinToggle}
                onRename={onRename}
                onDelete={onDelete}
              />
            ))
          )}
        </div>

        {/* Real jurisdiction key — one row per regulator actually present in
            the corpus (via /api/documents through App.jsx), colored with the
            exact same j1..j4 mapping used on the citation tags themselves. */}
        <div className="jurisdiction-key">
          {regulators.map((reg) => (
            <div className="key-row" key={reg}>
              <span className={`key-dot ${classForCode(reg, regulators)}`}></span>
              {reg} citations
            </div>
          ))}
          <div className="jurisdiction-key-count">{indexedChunks ?? "…"} clauses indexed</div>
          <button className="profile-trigger" onClick={() => setProfileOpen(true)}>
            <span className="profile-avatar">{username[0]?.toUpperCase()}</span>
            <span className="profile-username">{username}</span>
          </button>
        </div>
      </div>

      {profileOpen && <ProfilePanel onClose={() => setProfileOpen(false)} onLogout={onLogout} />}
    </>
  );
}
