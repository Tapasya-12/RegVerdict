import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

const API_BASE = "http://localhost:8000";
const CANVAS_WIDTH = 900;
const CANVAS_HEIGHT = 600;
const NODE_RADIUS = 15;

export default function ClauseGraphView() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState("");
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  const svgRef = useRef(null);
  const simulationRef = useRef(null);

  // Populate the document dropdown from the corpus itself, not a hardcoded
  // list — a 5th document appearing shouldn't require a frontend change.
  useEffect(() => {
    fetch(`${API_BASE}/api/documents`)
      .then((res) => {
        if (!res.ok) throw new Error(`api/documents returned ${res.status}`);
        return res.json();
      })
      .then((docs) => {
        setDocuments(docs);
        if (docs.length > 0) setSelectedDocument(docs[0]);
      })
      .catch((err) => {
        console.error("api/documents fetch failed:", err);
        setError("Could not reach the compliance engine — check that the backend is running.");
      });
  }, []);

  useEffect(() => {
    if (!selectedDocument) return;
    setLoading(true);
    setError(null);
    setSelectedNode(null);
    setGraph(null);
    fetch(`${API_BASE}/api/clause_graph/${encodeURIComponent(selectedDocument)}`)
      .then((res) => {
        if (!res.ok) throw new Error(`clause_graph returned ${res.status}`);
        return res.json();
      })
      .then((data) => setGraph(data))
      .catch((err) => {
        console.error("clause_graph fetch failed:", err);
        setError("Could not reach the compliance engine — check that the backend is running.");
      })
      .finally(() => setLoading(false));
  }, [selectedDocument]);

  useEffect(() => {
    if (!graph || graph.edges.length === 0) return;

    const nodes = graph.nodes.map((n) => ({ ...n }));
    const edges = graph.edges.map((e) => ({ ...e }));

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const zoomLayer = svg.append("g");
    svg.call(
      d3.zoom().scaleExtent([0.3, 3]).on("zoom", (event) => {
        zoomLayer.attr("transform", event.transform);
      })
    );

    const link = zoomLayer
      .append("g")
      .attr("stroke", "var(--gazette-gold, #d4941a)")
      .attr("stroke-opacity", 0.45)
      .selectAll("line")
      .data(edges)
      .join("line")
      .attr("stroke-width", 1.4);

    const node = zoomLayer
      .append("g")
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", NODE_RADIUS)
      .attr("fill", "var(--kraft, #fbf3e1)")
      .attr("stroke", "var(--ink-navy, #17264d)")
      .attr("stroke-width", 1.5)
      .style("cursor", "pointer")
      .on("click", (_event, d) => setSelectedNode(d));

    const label = zoomLayer
      .append("g")
      .selectAll("text")
      .data(nodes)
      .join("text")
      .text((d) => d.clause_number)
      .attr("text-anchor", "middle")
      .attr("dy", "0.32em")
      .attr("font-family", "IBM Plex Mono, monospace")
      .attr("font-size", 9.5)
      .attr("fill", "var(--ink-text, #1e2440)")
      .style("pointer-events", "none");

    node.call(
      d3
        .drag()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
    );

    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink(edges)
          .id((d) => d.id)
          .distance(85)
      )
      .force("charge", d3.forceManyBody().strength(-180))
      .force("center", d3.forceCenter(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2))
      .force("collide", d3.forceCollide(NODE_RADIUS + 6))
      // Weak centering pull so clauses with NO cross-references (common —
      // most RBI documents are sparse) don't get flung off-canvas by pure
      // charge repulsion with nothing else anchoring them.
      .force("x", d3.forceX(CANVAS_WIDTH / 2).strength(0.025))
      .force("y", d3.forceY(CANVAS_HEIGHT / 2).strength(0.025))
      .on("tick", () => {
        link
          .attr("x1", (d) => d.source.x)
          .attr("y1", (d) => d.source.y)
          .attr("x2", (d) => d.target.x)
          .attr("y2", (d) => d.target.y);
        node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);
        label.attr("x", (d) => d.x).attr("y", (d) => d.y);
      });

    simulationRef.current = simulation;
    return () => simulation.stop();
  }, [graph]);

  return (
    <div>
      <div className="clause-graph-controls">
        <label className="clause-graph-select-label">
          Document
          <select
            value={selectedDocument}
            onChange={(e) => setSelectedDocument(e.target.value)}
            disabled={documents.length === 0}
          >
            {documents.map((doc) => (
              <option key={doc} value={doc}>
                {doc}
              </option>
            ))}
          </select>
        </label>
        {graph && (
          <span className="intake-hint">
            {graph.nodes.length} clauses · {graph.edges.length} cross-references
          </span>
        )}
      </div>

      {error && (
        <p className="intake-hint" style={{ color: "var(--seal-red)", marginTop: 24 }}>
          {error}
        </p>
      )}

      {loading && <p className="intake-hint" style={{ marginTop: 24 }}>Loading graph…</p>}

      {!loading && graph && (
        <div className="clause-graph-layout">
          <div className="clause-graph-canvas">
            {graph.edges.length === 0 ? (
              <div className="clause-graph-empty">
                No cross-references detected in this document. It has {graph.nodes.length} indexed
                clauses, but none of them cite another clause by number in a way this extractor
                recognizes.
              </div>
            ) : (
              <svg
                ref={svgRef}
                viewBox={`0 0 ${CANVAS_WIDTH} ${CANVAS_HEIGHT}`}
                width="100%"
                height={CANVAS_HEIGHT}
              />
            )}
          </div>

          {selectedNode && (
            <div className="clause-detail">
              <span className="exhibit-tab">
                CLAUSE {selectedNode.clause_number}
              </span>
              <div className="clause-detail-body">
                <p className="clause-detail-section">
                  {selectedNode.parent_section || "— no parent section recorded —"}
                </p>
                <p className="clause-detail-text">
                  {selectedNode.text || "— no clause text available —"}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
