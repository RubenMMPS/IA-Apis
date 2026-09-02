import { useState } from "react";

export function TaskLookup({ onFound }: { onFound: (taskId: string) => void }) {
  const [input, setInput] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    onFound(input.trim());
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8, marginTop: 24 }}>
      <input
        value={input} onChange={(e) => setInput(e.target.value)}
        placeholder="Consultar tarea existente por task_id..."
        style={{ flex: 1, padding: 8, fontSize: 13 }}
      />
      <button type="submit">Buscar</button>
    </form>
  );
}