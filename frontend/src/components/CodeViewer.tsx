import { useEffect, useState } from "react";
import type { CodeArtifacts } from "../types/task";
import { getTaskCode } from "../api/tasks";

export function CodeViewer({ taskId, isFinished }: { taskId: string; isFinished: boolean }) {
  const [code, setCode] = useState<CodeArtifacts | null>(null);
  const [activeFile, setActiveFile] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isFinished) return;
    getTaskCode(taskId).then(setCode).catch(() => setError("sin código disponible"));
  }, [taskId, isFinished]);

  if (!isFinished) return null;
  if (error) return <p style={{ color: "var(--text-faint)", fontSize: 12, fontFamily: "var(--font-mono)" }}>{error}</p>;
  if (!code) return null;

  return (
    <div className="code-viewer">
      <div className="code-tabs">
        {code.files.map((f, i) => (
          <button
            key={f.filename}
            onClick={() => setActiveFile(i)}
            className={`code-tab ${i === activeFile ? "active" : ""}`}
          >
            {f.filename}
          </button>
        ))}
      </div>
      <pre className="code-block"><code>{code.files[activeFile]?.content}</code></pre>
      <p className="code-notes">{code.notes}</p>
    </div>
  );
}