import asyncio
import shutil
import tempfile
from pathlib import Path
import subprocess

from app.graph.state.code import CodeFile

SANDBOX_IMAGE = "ai-swe-team-sandbox:latest"
EXEC_TIMEOUT_SECONDS = 30
WAIT_TIMEOUT_SECONDS = 40  # margen extra sobre el timeout interno, por si Docker tarda en arrancar
MEMORY_LIMIT = "256m"
CPU_LIMIT = "0.5"


class DockerTestRunner:
    async def run_tests(self, files: list[CodeFile]) -> tuple[bool, int, str]:
        tmp_dir = Path(tempfile.mkdtemp(prefix="aiswe_sandbox_"))
        try:
            self._write_files(tmp_dir, files)
            return await self._execute(tmp_dir)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _write_files(self, tmp_dir: Path, files: list[CodeFile]) -> None:
        for f in files:
            path = tmp_dir / f.filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f.content, encoding="utf-8")

    async def _execute(self, tmp_dir: Path) -> tuple[bool, int, str]:
        cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", MEMORY_LIMIT,
            "--cpus", CPU_LIMIT,
            "--cap-drop", "ALL",
            "-v", f"{tmp_dir}:/app",
            "-w", "/app",
            SANDBOX_IMAGE,
            "timeout", str(EXEC_TIMEOUT_SECONDS), "python", "-m", "pytest", "-q", "--tb=short",
        ]

        def _run_blocking() -> tuple[bool, int, str]:
            try:
                result = subprocess.run(
                    cmd,  # <-- capturado del scope exterior, no se importa
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=WAIT_TIMEOUT_SECONDS,
                )
                output = (result.stdout + result.stderr)[-4000:]
                return result.returncode == 0, result.returncode, output
            except subprocess.TimeoutExpired:
                return False, -1, "Timeout: la ejecución de tests excedió el límite de tiempo."

        return await asyncio.to_thread(_run_blocking)