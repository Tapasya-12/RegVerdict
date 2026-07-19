import { useEffect, useRef, useState } from "react";

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
      <button className="recent-item" title={entry.fullQuery} onClick={() => onSelect(entry.fullQuery)}>
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

  return (
    <div className="sidebar">
      <div className="side-wordmark">
        Reg<em>Verdict</em>
      </div>
      <div className="side-sub">Compliance Copilot</div>

      <button className="new-check-btn" onClick={onNewCheck}>
        New compliance check
      </button>

      <div className="nav-label">Tools</div>
      {TOOLS.map((tool) => (
        <button
          key={tool.id}
          className={`nav-item${activeTool === tool.id ? " active" : ""}`}
          onClick={() => onSelectTool(tool.id)}
        >
          {tool.label}
        </button>
      ))}

      <div className="sidebar-divider"></div>

      {pinned.length > 0 && (
        <>
          <div className="nav-label">Pinned</div>
          {pinned.map((entry) => (
            <RecentChatRow
              key={entry.id}
              entry={entry}
              onSelect={onSelectRecent}
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
            onSelect={onSelectRecent}
            onPinToggle={onPinToggle}
            onRename={onRename}
            onDelete={onDelete}
          />
        ))
      )}

      <div className="sidebar-footer">
        {indexedChunks ?? "…"} clauses indexed{regulators.length ? ` · ${regulators.join(" · ")}` : ""}
        <button className="nav-item" style={{ marginTop: 10, padding: "9px 10px 9px 0" }} onClick={onLogout}>
          Log out
        </button>
      </div>
    </div>
  );
}
