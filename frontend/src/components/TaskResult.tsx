import { useEffect, useState } from "react";
import type { Task } from "../types/task";
import { getTask } from "../api/tasks";

export function TaskResult({ taskId, isFinished }: { taskId: string; isFinished: boolean }) {
  const [task, setTask] = useState<Task | null>(null);

  useEffect(() => {
    if (!isFinished) return;
    getTask(taskId).then(setTask).catch(() => setTask(null));
  }, [taskId, isFinished]);

  if (!isFinished || !task) return null;

  return (
    <div style={{ marginTop: 16, padding: 16, borderRadius: 8, background: task.status === "completed" ? "#f0fdf4" : "#fef2f2" }}>
      <strong>Estado final: {task.status}</strong>
      {task.result_summary && <p>{task.result_summary}</p>}
      {task.error_message && <p style={{ color: "#b91c1c" }}>{task.error_message}</p>}
    </div>
  );
}