export type EventType =
  | "agent_started" | "agent_completed" | "agent_error"
  | "tool_used" | "retry" | "task_completed" | "task_failed";

export type AgentName =
  | "planner" | "researcher" | "architect" | "developer" | "tester" | "reviewer";

export interface TaskEvent {
  event_type: EventType;
  agent: AgentName | null;
  message: string;
  timestamp: string;
}

export const AGENT_ORDER: AgentName[] = [
  "planner", "researcher", "architect", "developer", "tester", "reviewer",
];

export type AgentStatus = "pending" | "running" | "completed" | "error";