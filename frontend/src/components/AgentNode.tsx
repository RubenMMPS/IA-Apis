import type { AgentName, AgentStatus } from "../types/events";

const LABELS: Record<AgentName, string> = {
  planner: "planner", researcher: "researcher", architect: "architect",
  developer: "developer", tester: "tester", reviewer: "reviewer",
};

export function AgentNode({ agent, status, retryCount }: {
  agent: AgentName; status: AgentStatus; retryCount?: number;
}) {
  return (
    <div className="pipeline-node">
      <span className={`pipeline-dot ${status}`} />
      <span className="pipeline-label">{LABELS[agent]}</span>
      {retryCount ? <span className="pipeline-retry">×{retryCount}</span> : null}
    </div>
  );
}