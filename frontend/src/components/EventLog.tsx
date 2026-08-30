import type { TaskEvent } from "../types/events";

export function EventLog({ events }: { events: TaskEvent[] }) {
  return (
    <div style={{ maxHeight: 300, overflowY: "auto", fontFamily: "monospace", fontSize: 13 }}>
      {events.map((ev, i) => (
        <div key={i} style={{ padding: "4px 0", borderBottom: "1px solid #eee" }}>
          <span style={{ color: "#6b7280" }}>{new Date(ev.timestamp).toLocaleTimeString()}</span>{" "}
          <strong>[{ev.event_type}]</strong>{" "}
          {ev.agent && <span style={{ color: "#3b82f6" }}>{ev.agent}:</span>}{" "}
          {ev.message}
        </div>
      ))}
    </div>
  );
}