import { useState } from "react";
import { createTask } from "../api/tasks";

export function TaskForm({ onCreated }: { onCreated: (taskId: string) => void }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    try {
      const task = await createTask({ original_request: text });
      onCreated(task.id);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="prompt-form">
      <span className="prompt-caret">&gt;</span>
      <textarea
        value={text} onChange={(e) => setText(e.target.value)}
        placeholder="describe la tarea de programación..."
        rows={2}
      />
      <button type="submit" className="btn btn-primary" disabled={loading}>
        {loading ? "..." : "run"}
      </button>
    </form>
  );
}