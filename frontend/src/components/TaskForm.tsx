import { useRef, useState } from "react";
import { createTask } from "../api/tasks";

export function TaskForm({ onCreated }: { onCreated: (taskId: string) => void }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setText(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${el.scrollHeight}px`;
    }
  }

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
        ref={textareaRef}
        value={text}
        onChange={handleChange}
        placeholder="describe la tarea de programación..."
        rows={2}
        disabled={loading}
      />
      <button type="submit" className="btn btn-primary" disabled={loading}>
        {loading ? "..." : "run"}
      </button>
    </form>
  );
}