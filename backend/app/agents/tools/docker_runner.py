import asyncio
import shutil
import tempfile
from pathlib import Path

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
            "timeout", str(EXEC_TIMEOUT_SECONDS), "pytest", "-q", "--tb=short",
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=WAIT_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            process.kill()
            return False, -1, "Timeout: la ejecución de tests excedió el límite de tiempo."

        output = (stdout + stderr).decode("utf-8", errors="replace")
        return process.returncode == 0, process.returncode, output[-4000:]