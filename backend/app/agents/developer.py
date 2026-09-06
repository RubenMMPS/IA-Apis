from app.agents.base import BaseAgent
from app.graph.state.graph_state import GraphState
from app.graph.state.code import CodeArtifacts
from app.core.events import event_bus, TaskEvent
import re

IMPORT_ERROR_PATTERNS = [
    r"ImportError",
    r"ModuleNotFoundError",
    r"cannot import name",
    r"No module named",
]

COLLECTION_ERROR_PATTERNS = [
    r"ImportError",
    r"ModuleNotFoundError",
    r"cannot import name",
    r"No module named",
    r"SyntaxError",
]

class DeveloperAgent(BaseAgent):
    name = "developer"
    max_output_tokens = 4096

    async def run(self, state: GraphState) -> dict:
        counts = dict(state.get("iteration_counts", {}))
        counts["developer"] = counts.get("developer", 0) + 1

        if counts["developer"] > 1:
            event_bus.publish(state["task_id"], TaskEvent(
                event_type="retry", agent=self.name,
                message=f"Reintento #{counts['developer']} de Developer",
            ))

        delta = await super().run(state)
        delta["iteration_counts"] = counts
        delta["developer_last_run_failed"] = "code_artifacts" not in delta
        return delta
    
    @property
    def system_prompt(self) -> str:
        return (
            "Eres el Developer de un equipo de ingeniería de software formado por IA. "
            "Implementa el código Python siguiendo exactamente la especificación técnica "
            "del Architect: los mismos nombres de componentes, la misma estructura de "
            "archivos. Escribe código completo, funcional y con type hints, sin marcadores "
            "de posición ni TODOs. Si recibes feedback de una iteración anterior "
            "(tests fallidos o revisión con cambios solicitados), corrígelo mostrando "
            "el archivo completo actualizado, no solo el fragmento cambiado. "
            "Si escribes tests asíncronos (async def con pytest), incluye siempre un "
            "archivo pytest.ini con 'asyncio_mode = auto' en la sección [pytest]; si no "
            "es estrictamente necesario usar tests async, prefiere tests síncronos con "
            "TestClient para mantener la ejecución simple. "
            "Para probar una app FastAPI con httpx.AsyncClient, usa la sintaxis actual: "
            "httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=\"http://test\") "
            "— el parámetro 'app=' directo en AsyncClient fue eliminado en versiones "
            "recientes de httpx y ya no es válido."
            "Respeta estrictamente cualquier restricción técnica explícita en la petición "
            "original del usuario (por ejemplo: 'en memoria', 'sin base de datos', 'sin "
            "dependencias externas'). No introduzcas librerías ni tecnologías no solicitadas "
            "para resolver un problema — si tienes dudas sobre cómo cumplir la restricción, "
            "prioriza la solución más simple que la respete, incluso si es menos robusta."
        )

    def _detect_import_issue_hint(self, test_output: str) -> str | None:
        if re.search(r"SyntaxError", test_output):
            return (
                "El fallo es un SyntaxError: el archivo de test o de implementación no es "
                "Python válido y ni siquiera se pudo cargar. Presta especial atención a los "
                "literales de string que contienen comillas o backslashes (por ejemplo, "
                "casos de prueba con caracteres especiales): usa raw strings (r\"...\") o "
                "escapa correctamente cada carácter. Corrige la sintaxis antes que cualquier "
                "otra cosa; ningún test se ejecutará mientras el archivo no sea válido."
            )
        if any(re.search(p, test_output) for p in IMPORT_ERROR_PATTERNS):
            return (
                "El fallo parece ser un error de importación, no un error de lógica. "
                "Antes de reescribir la implementación, revisa específicamente: "
                "(1) que los nombres de funciones/clases que los tests importan coincidan "
                "exactamente con los que tu implementación exporta (mismo nombre, misma "
                "ubicación); (2) que la firma y el tipo de retorno de cada función usada en "
                "los tests coincidan con cómo la defines; (3) si usas una librería externa, "
                "que la API que invocas (nombres de funciones, excepciones que lanza) sea la "
                "real de esa librería y no una que hayas asumido. "
                "Corrige el desajuste de nombres/API antes que cualquier otra cosa."
            )
        return None

    def build_user_message(self, state: GraphState) -> str:
        spec = state.get("architecture_spec")
        if spec is None:
            return (
                "No se recibió una especificación técnica válida del Architect "
                "(posible fallo previo). Genera una implementación mínima y razonable "
                f"para la petición original del usuario:\n{state['original_request']}"
            )

        decisions_text = "\n".join(f"- {d.component}: {d.description}" for d in spec.decisions)
        files_text = ", ".join(spec.files_to_create)

        parts = [
            f"Especificación técnica:\n{spec.summary}\n\nDecisiones:\n{decisions_text}",
            f"\nArchivos a crear: {files_text}",
        ]

        test_results = state.get("test_results")
        if test_results and not test_results.passed:
            parts.append(f"\nLos tests fallaron en el intento anterior:\n{test_results.output}")
            hint = self._detect_import_issue_hint(test_results.output)
            if hint:
                parts.append(f"\nPista de diagnóstico:\n{hint}")

        review_feedback = state.get("review_feedback")
        if review_feedback and review_feedback.decision == "changes_requested":
            parts.append(f"\nEl Reviewer pidió cambios:\n{review_feedback.comments}")

        return "\n".join(parts)

    def output_schema(self) -> type[CodeArtifacts]:
        return CodeArtifacts

    def apply_output(self, state: GraphState, output: CodeArtifacts) -> dict:
        return {"code_artifacts": output}