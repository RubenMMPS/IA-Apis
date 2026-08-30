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
    <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8 }}>
      <textarea
        value={text} onChange={(e) => setText(e.target.value)}
        placeholder="Describe la tarea de programación..."
        rows={3} style={{ flex: 1, padding: 8 }}
      />
      <button type="submit" disabled={loading}>{loading ? "Creando..." : "Crear tarea"}</button>
    </form>
  );
}