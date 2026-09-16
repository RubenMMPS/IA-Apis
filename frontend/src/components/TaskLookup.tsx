import { useState } from "react";

export function TaskLookup({ onFound }: { onFound: (taskId: string) => void }) {
  const [input, setInput] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    onFound(input.trim());
  }

  return (
    <form onSubmit={handleSubmit} className="lookup-form">
      <input
        value={input} onChange={(e) => setInput(e.target.value)}
        placeholder="task_id..."
      />
      <button type="submit" className="btn">buscar</button>
    </form>
  );
}