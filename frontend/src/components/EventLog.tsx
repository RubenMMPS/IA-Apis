import type { TaskEvent } from "../types/events";

export function EventLog({ events }: { events: TaskEvent[] }) {
  return (
    <div className="event-log">
      {events.map((ev, i) => (
        <div key={i} className="event-line">
          <span className="ts">{new Date(ev.timestamp).toLocaleTimeString()}</span>
          <span className={`kind ${ev.event_type}`}>{ev.event_type}</span>
          {ev.agent && <span className="who">{ev.agent}</span>}
          <span>{ev.message}</span>
        </div>
      ))}
    </div>
  );
}