import type { AgentName, AgentStatus } from "../types/events";

const LABELS: Record<AgentName, string> = {
  planner: "Planner", researcher: "Researcher", architect: "Architect",
  developer: "Developer", tester: "Tester", reviewer: "Reviewer",
};

const COLORS: Record<AgentStatus, string> = {
  pending: "#9ca3af", running: "#3b82f6", completed: "#22c55e", error: "#ef4444",
};

export function AgentNode({ agent, status, retryCount }: {
  agent: AgentName; status: AgentStatus; retryCount?: number;
}) {
  return (
    <div style={{
      padding: "12px 16px", borderRadius: 8, minWidth: 110, textAlign: "center",
      border: `2px solid ${COLORS[status]}`,
      background: status === "running" ? "#eff6ff" : "#fff",
    }}>
      <div style={{ fontWeight: 600 }}>{LABELS[agent]}</div>
      <div style={{ fontSize: 12, color: COLORS[status] }}>{status}</div>
      {retryCount ? <div style={{ fontSize: 11, color: "#f59e0b" }}>retry ×{retryCount}</div> : null}
    </div>
  );
}