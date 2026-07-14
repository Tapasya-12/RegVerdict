import { useEffect, useState } from "react";
import { STAMP_CLASS_BY_VERDICT } from "./ExhibitCard";

const API_BASE = "http://localhost:8000";
const VERDICTS = ["Compliant", "Non-Compliant", "Requires Legal Review", "Conflicting Regulations"];

function formatTimestamp(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function truncate(text, max = 80) {
  if (!text) return "";
  return text.length > max ? text.slice(0, max).trimEnd() + "…" : text;
}

const CSV_COLUMNS = ["timestamp", "policy_text", "verdict", "confidence", "document_name", "clause_number", "grounding_verified"];

function toCSV(rows) {
  const escape = (value) => {
    const s = value === null || value === undefined ? "" : String(value);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines = [CSV_COLUMNS.join(",")];
  for (const row of rows) {
    lines.push(CSV_COLUMNS.map((col) => escape(row[col])).join(","));
  }
  return lines.join("\n");
}

function downloadCSV(rows) {
  const csv = toCSV(rows);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `regverdict_audit_trail_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export default function AuditTrail() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [verdict, setVerdict] = useState("");
  const [search, setSearch] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  useEffect(() => {
    // Light debounce so the search field doesn't fire a request per
    // keystroke — filtering itself still happens server-side, this just
    // batches rapid typing into one fetch.
    const handle = setTimeout(() => {
      const params = new URLSearchParams();
      if (verdict) params.set("verdict", verdict);
      if (search) params.set("search", search);
      if (startDate) params.set("start_date", startDate);
      if (endDate) params.set("end_date", endDate);

      setLoading(true);
      setError(null);
      fetch(`${API_BASE}/api/audit_trail?${params.toString()}`)
        .then((res) => {
          if (!res.ok) throw new Error(`audit_trail returned ${res.status}`);
          return res.json();
        })
        .then((data) => setRecords(data))
        .catch((err) => {
          console.error("audit_trail fetch failed:", err);
          setError("Could not reach the compliance engine — check that the backend is running.");
          setRecords([]);
        })
        .finally(() => setLoading(false));
    }, 300);

    return () => clearTimeout(handle);
  }, [verdict, search, startDate, endDate]);

  return (
    <div className="audit-trail">
      <div className="audit-filters">
        <label>
          Verdict
          <select value={verdict} onChange={(e) => setVerdict(e.target.value)}>
            <option value="">All verdicts</option>
            {VERDICTS.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </label>

        <label>
          Search
          <input
            type="text"
            placeholder="Search policy text…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>

        <label>
          From
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </label>

        <label>
          To
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        </label>

        <button
          className="audit-export-btn"
          onClick={() => downloadCSV(records)}
          disabled={records.length === 0}
        >
          Export CSV
        </button>
      </div>

      {error && <p className="audit-error">{error}</p>}

      {!error && !loading && records.length === 0 && (
        <p className="audit-empty">No audit records match these filters.</p>
      )}

      {!error && records.length > 0 && (
        <div className="audit-table-wrap">
          <table className="audit-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Policy</th>
                <th>Verdict</th>
                <th>Clause</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.id}>
                  <td className="audit-mono">{formatTimestamp(r.timestamp)}</td>
                  <td title={r.policy_text}>{truncate(r.policy_text)}</td>
                  <td>
                    <span className={`verdict-badge ${STAMP_CLASS_BY_VERDICT[r.verdict] || "review"}`}>
                      {r.verdict}
                    </span>
                  </td>
                  <td className="audit-mono">
                    {r.document_name ? `${r.document_name} §${r.clause_number}` : "—"}
                  </td>
                  <td className="audit-mono">
                    {typeof r.confidence === "number" ? r.confidence.toFixed(2) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
