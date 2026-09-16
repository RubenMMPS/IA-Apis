import { AGENT_ORDER } from "../types/events";
import type { AgentName, AgentStatus } from "../types/events";
import { AgentNode } from "./AgentNode";

export function WorkflowPipeline({ agentStatuses, retryCounts }: {
  agentStatuses: Record<AgentName, AgentStatus>;
  retryCounts: Partial<Record<AgentName, number>>;
}) {
  return (
    <div className="pipeline">
      {AGENT_ORDER.map((agent, i) => (
        <>
          <AgentNode key={agent} agent={agent} status={agentStatuses[agent]} retryCount={retryCounts[agent]} />
          {i < AGENT_ORDER.length - 1 && (
            <span className={`pipeline-connector ${agentStatuses[agent] === "completed" ? "filled" : ""}`} />
          )}
        </>
      ))}
    </div>
  );
}