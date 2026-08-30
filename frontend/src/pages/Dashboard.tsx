import { useState } from "react";
import { TaskForm } from "../components/TaskForm";
import { WorkflowPipeline } from "../components/WorkflowPipeline";
import { EventLog } from "../components/EventLog";
import { TaskResult } from "../components/TaskResult";
import { useTaskEvents } from "../hooks/useTaskEvents";

function TaskView({ taskId }: { taskId: string }) {
  const { events, agentStatuses, retryCounts, isFinished, connectionError } = useTaskEvents(taskId);

  return (
    <div style={{ marginTop: 24 }}>
      <p style={{ fontSize: 13, color: "#6b7280" }}>Task ID: {taskId}</p>
      <WorkflowPipeline agentStatuses={agentStatuses} retryCounts={retryCounts} />
      {connectionError && <p style={{ color: "#b91c1c" }}>{connectionError}</p>}
      <div style={{ marginTop: 16 }}>
        <EventLog events={events} />
      </div>
      <TaskResult taskId={taskId} isFinished={isFinished} />
    </div>
  );
}

export function Dashboard() {
  const [taskId, setTaskId] = useState<string | null>(null);

  return (
    <div style={{ maxWidth: 800, margin: "40px auto", padding: 16 }}>
      <h1>AI Software Engineering Team</h1>
      <TaskForm onCreated={setTaskId} />
      {taskId && <TaskView key={taskId} taskId={taskId} />}
    </div>
  );
}