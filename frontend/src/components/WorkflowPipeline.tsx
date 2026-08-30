import { AGENT_ORDER } from "../types/events";
import type { AgentName, AgentStatus } from "../types/events";
import { AgentNode } from "./AgentNode";

export function WorkflowPipeline({ agentStatuses, retryCounts }: {
  agentStatuses: Record<AgentName, AgentStatus>;
  retryCounts: Partial<Record<AgentName, number>>;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
      {AGENT_ORDER.map((agent, i) => (
        <div key={agent} style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <AgentNode agent={agent} status={agentStatuses[agent]} retryCount={retryCounts[agent]} />
          {i < AGENT_ORDER.length - 1 && <span style={{ color: "#9ca3af" }}>→</span>}
        </div>
      ))}
    </div>
  );
}