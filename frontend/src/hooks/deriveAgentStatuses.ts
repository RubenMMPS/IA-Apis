import type { TaskEvent, AgentName, AgentStatus } from "../types/events";
import { AGENT_ORDER } from "../types/events";

export function deriveAgentStatuses(events: TaskEvent[]) {
  const agentStatuses = {} as Record<AgentName, AgentStatus>;
  AGENT_ORDER.forEach((a) => (agentStatuses[a] = "pending"));
  const retryCounts: Partial<Record<AgentName, number>> = {};

  for (const ev of events) {
    if (!ev.agent) continue;
    if (ev.event_type === "agent_started") agentStatuses[ev.agent] = "running";
    if (ev.event_type === "agent_completed") agentStatuses[ev.agent] = "completed";
    if (ev.event_type === "agent_error") agentStatuses[ev.agent] = "error";
    if (ev.event_type === "retry") {
      retryCounts[ev.agent] = (retryCounts[ev.agent] ?? 1) + 1;
      agentStatuses[ev.agent] = "pending";
    }
  }

  return { agentStatuses, retryCounts };
}