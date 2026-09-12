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
      {task.total_tokens != null && (
      <p style={{ fontSize: 12, color: "#6b7280", marginTop: 8 }}>
        Tokens usados: {task.total_tokens.toLocaleString()} · Coste estimado: ${task.estimated_cost_usd?.toFixed(6)}
      </p>
      )}
    </div>
  );
}