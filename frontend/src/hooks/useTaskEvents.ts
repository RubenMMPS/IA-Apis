import { useEffect, useRef, useState } from "react";
import type { TaskEvent, AgentName, AgentStatus, EventType } from "../types/events";
import { AGENT_ORDER } from "../types/events";
import { sseUrl } from "../api/client";

interface UseTaskEventsResult {
  events: TaskEvent[];
  agentStatuses: Record<AgentName, AgentStatus>;
  retryCounts: Partial<Record<AgentName, number>>;
  isFinished: boolean;
  connectionError: string | null;
}

const FINISHED_TYPES: EventType[] = ["task_completed", "task_failed"];

export function useTaskEvents(taskId: string | null): UseTaskEventsResult {
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

useEffect(() => {
    if (!taskId) return;

    const es = new EventSource(sseUrl(`/tasks/${taskId}/events`));
    esRef.current = es;

    const eventTypes: EventType[] = [
      "agent_started", "agent_completed", "agent_error",
      "tool_used", "retry", "task_completed", "task_failed",
    ];

    eventTypes.forEach((type) => {
      es.addEventListener(type, (e) => {
        const parsed: TaskEvent = JSON.parse((e as MessageEvent).data);
        setEvents((prev) => [...prev, parsed]);
        if (FINISHED_TYPES.includes(parsed.event_type)) {
          es.close();
        }
      });
    });

    es.onerror = () => {
      // EventSource ya cerrado (fin normal) -> no es un error real
      if (es.readyState === EventSource.CLOSED) return;
      setConnectionError("Conexión con el stream de eventos perdida.");
      es.close();
    };

    return () => es.close();
  }, [taskId]);

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
      agentStatuses[ev.agent] = "pending"; // vuelve a esperar su turno
    }
  }

  const isFinished = events.some((e) => FINISHED_TYPES.includes(e.event_type));

  return { events, agentStatuses, retryCounts, isFinished, connectionError };
}