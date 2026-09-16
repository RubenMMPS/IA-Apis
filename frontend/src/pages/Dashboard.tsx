import { useEffect, useState } from "react";
import { TaskForm } from "../components/TaskForm";
import { TaskLookup } from "../components/TaskLookup";
import { WorkflowPipeline } from "../components/WorkflowPipeline";
import { EventLog } from "../components/EventLog";
import { TaskResult } from "../components/TaskResult";
import { CodeViewer } from "../components/CodeViewer";
import { useTaskEvents } from "../hooks/useTaskEvents";
import { getTask, getTaskEventsHistory } from "../api/tasks";
import { deriveAgentStatuses } from "../hooks/deriveAgentStatuses";
import type { Task } from "../types/task";
import type { TaskEvent } from "../types/events";

function LiveTaskView({ taskId }: { taskId: string }) {
  const { events, agentStatuses, retryCounts, isFinished, connectionError } = useTaskEvents(taskId);

  return (
    <>
      <WorkflowPipeline agentStatuses={agentStatuses} retryCounts={retryCounts} />
      {connectionError && <p style={{ color: "var(--state-error)", fontSize: 12 }}>{connectionError}</p>}
      <EventLog events={events} />
      <TaskResult taskId={taskId} isFinished={isFinished} />
      <CodeViewer taskId={taskId} isFinished={isFinished} />
    </>
  );
}

function FinishedTaskView({ taskId }: { taskId: string }) {
  const [events, setEvents] = useState<TaskEvent[] | null>(null);

  useEffect(() => {
    getTaskEventsHistory(taskId).then(setEvents).catch(() => setEvents([]));
  }, [taskId]);

  if (events === null) return <p style={{ color: "var(--text-faint)", fontSize: 12 }}>cargando historial...</p>;

  const { agentStatuses, retryCounts } = deriveAgentStatuses(events);

  return (
    <>
      <WorkflowPipeline agentStatuses={agentStatuses} retryCounts={retryCounts} />
      <EventLog events={events} />
      <TaskResult taskId={taskId} isFinished={true} />
      <CodeViewer taskId={taskId} isFinished={true} />
    </>
  );
}

function TaskView({ taskId }: { taskId: string }) {
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTask(taskId).then(setTask).catch(() => setTask(null)).finally(() => setLoading(false));
  }, [taskId]);

  return (
    <div>
      <div className="task-meta">{taskId}</div>
      {loading && <p style={{ color: "var(--text-faint)", fontSize: 12 }}>cargando...</p>}
      {!loading && !task && <p style={{ color: "var(--state-error)", fontSize: 12 }}>tarea no encontrada</p>}
      {!loading && task && (task.status === "completed" || task.status === "failed")
        ? <FinishedTaskView taskId={taskId} />
        : !loading && task && <LiveTaskView taskId={taskId} />
      }
    </div>
  );
}

export function Dashboard() {
  const [taskId, setTaskId] = useState<string | null>(null);

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>ai-swe-team</h1>
        <span className="tagline">planner · researcher · architect · developer · tester · reviewer</span>
      </header>
      <TaskForm onCreated={setTaskId} />
      <TaskLookup onFound={setTaskId} />
      {taskId && <TaskView key={taskId} taskId={taskId} />}
    </div>
  );
}