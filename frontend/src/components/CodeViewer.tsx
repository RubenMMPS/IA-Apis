import { useEffect, useState } from "react";
import type { CodeArtifacts } from "../types/task";
import { getTaskCode } from "../api/tasks";

export function CodeViewer({ taskId, isFinished }: { taskId: string; isFinished: boolean }) {
  const [code, setCode] = useState<CodeArtifacts | null>(null);
  const [activeFile, setActiveFile] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isFinished) return;
    getTaskCode(taskId)
      .then(setCode)
      .catch(() => setError("No hay código disponible para esta tarea."));
  }, [taskId, isFinished]);

  if (!isFinished) return null;
  if (error) return <p style={{ color: "#b91c1c" }}>{error}</p>;
  if (!code) return null;

  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 8 }}>
        {code.files.map((f, i) => (
          <button
            key={f.filename}
            onClick={() => setActiveFile(i)}
            style={{
              padding: "6px 10px", fontSize: 12,
              background: i === activeFile ? "#3b82f6" : "#e5e7eb",
              color: i === activeFile ? "#fff" : "#111",
              border: "none", borderRadius: 4, cursor: "pointer",
            }}
          >
            {f.filename}
          </button>
        ))}
      </div>
      <pre style={{
        background: "#0f172a", color: "#e2e8f0", padding: 16, borderRadius: 8,
        overflowX: "auto", fontSize: 13, maxHeight: 400,
      }}>
        <code>{code.files[activeFile]?.content}</code>
      </pre>
      <p style={{ fontSize: 13, color: "#6b7280", marginTop: 8 }}>{code.notes}</p>
    </div>
  );
}