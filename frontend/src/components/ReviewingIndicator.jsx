export default function ReviewingIndicator({ active }) {
  return (
    <div className={`reviewing${active ? " active" : ""}`}>
      <span className="scan-box">
        <span className="scan-line"></span>
        <span className="scan-line"></span>
        <span className="scan-line"></span>
        <span className="scan-beam"></span>
      </span>
      Retrieving clauses, cross-checking evidence…
    </div>
  );
}
