import { useEffect, useState } from "react";
import { TaskForm } from "../components/TaskForm";
import { TaskLookup } from "../components/TaskLookup";
import { WorkflowPipeline } from "../components/WorkflowPipeline";
import { EventLog } from "../components/EventLog";
import { TaskResult } from "../components/TaskResult";
import { CodeViewer } from "../components/CodeViewer";
import { useTaskEvents } from "../hooks/useTaskEvents";
import { getTask } from "../api/tasks";
import type { Task } from "../types/task";
import { AGENT_ORDER } from "../types/events";
import type { AgentName, AgentStatus } from "../types/events";

function LiveTaskView({ taskId }: { taskId: string }) {
  const { events, agentStatuses, retryCounts, isFinished, connectionError } = useTaskEvents(taskId);

  return (
    <>
      <WorkflowPipeline agentStatuses={agentStatuses} retryCounts={retryCounts} />
      {connectionError && <p style={{ color: "#b91c1c" }}>{connectionError}</p>}
      <div style={{ marginTop: 16 }}>
        <EventLog events={events} />
      </div>
      <TaskResult taskId={taskId} isFinished={isFinished} />
      <CodeViewer taskId={taskId} isFinished={isFinished} />
    </>
  );
}

function FinishedTaskView({ taskId, task }: { taskId: string; task: Task }) {
  const allStatus: AgentStatus = task.status === "completed" ? "completed" : "error";
  const agentStatuses = {} as Record<AgentName, AgentStatus>;
  AGENT_ORDER.forEach((a) => (agentStatuses[a] = allStatus));

  return (
    <>
      <WorkflowPipeline agentStatuses={agentStatuses} retryCounts={{}} />
      <p style={{ fontSize: 13, color: "#6b7280", marginTop: 8 }}>
        Esta tarea ya finalizó — no hay eventos en vivo disponibles, mostrando resultado guardado.
      </p>
      <TaskResult taskId={taskId} isFinished={true} />
      <CodeViewer taskId={taskId} isFinished={true} />
    </>
  );
}

function TaskView({ taskId }: { taskId: string }) {
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTask(taskId)
      .then(setTask)
      .catch(() => setTask(null))
      .finally(() => setLoading(false));
  }, [taskId]);

  return (
    <div style={{ marginTop: 24 }}>
      <p style={{ fontSize: 13, color: "#6b7280" }}>Task ID: {taskId}</p>
      {loading && <p>Cargando...</p>}
      {!loading && !task && <p style={{ color: "#b91c1c" }}>Tarea no encontrada.</p>}
      {!loading && task && (task.status === "completed" || task.status === "failed")
        ? <FinishedTaskView taskId={taskId} task={task} />
        : !loading && task && <LiveTaskView taskId={taskId} />
      }
    </div>
  );
}

export function Dashboard() {
  const [taskId, setTaskId] = useState<string | null>(null);

  return (
    <div style={{ maxWidth: 800, margin: "40px auto", padding: 16 }}>
      <h1>AI Software Engineering Team</h1>
      <TaskForm onCreated={setTaskId} />
      <TaskLookup onFound={setTaskId} />
      {taskId && <TaskView key={taskId} taskId={taskId} />}
    </div>
  );
}