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
    <div className={`result-panel ${task.status}`}>
      <span className="status-word">{task.status}</span>
      {task.result_summary && <p>{task.result_summary}</p>}
      {task.error_message && <p style={{ color: "var(--state-error)" }}>{task.error_message}</p>}
      {task.total_tokens != null && (
        <div className="cost-line">
          {task.total_tokens.toLocaleString()} tokens · ${task.estimated_cost_usd?.toFixed(6)}
        </div>
      )}
    </div>
  );
}