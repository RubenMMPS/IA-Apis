from pydantic import BaseModel

from app.llm.base import LLMProvider
from app.llm.models import LLMRequest, LLMMessage
from app.graph.state.code import CodeArtifacts
from app.graph.state.architecture import ArchitectureSpec


class JudgeScore(BaseModel):
    correctness: int
    readability: int
    plan_adherence: int
    constraints_compliance: int
    comment: str


JUDGE_SYSTEM_PROMPT = (
    "Eres un evaluador de calidad de código, independiente del equipo que lo generó. "
    "Evalúa el código según cuatro dimensiones, cada una en una escala de 1 (muy deficiente) "
    "a 5 (excelente):\n"
    "- correctness: ¿el código resuelve correctamente la tarea pedida? No asumas que "
    "pasar los tests basta — evalúa si los propios tests son suficientes y si la lógica "
    "es correcta.\n"
    "- readability: nombres claros, estructura razonable, documentación adecuada.\n"
    "- plan_adherence: ¿el código sigue la especificación técnica proporcionada?\n"
    "- constraints_compliance: evalúa ÚNICAMENTE si el código respeta las restricciones "
    "técnicas EXPLÍCITAS listadas más abajo bajo 'Restricciones técnicas explícitas' — "
    "nada más. Si esa lista está vacía o dice '(ninguna)', puntúa 5 sin excepción, "
    "independientemente de cualquier otro problema que detectes en el código (esos "
    "problemas van en 'comment' y pueden afectar a 'correctness', pero NUNCA a esta "
    "puntuación). No inventes restricciones implícitas a partir de metadata del código "
    "(como requires-python, versión de librerías, o convenciones no mencionadas por el "
    "usuario).\n"
    "Responde solo con el JSON pedido, sin texto adicional. Sé estricto y específico "
    "en el comentario, señalando problemas concretos si los hay — incluso si no afectan "
    "a constraints_compliance."
)


async def judge_code(
    llm: LLMProvider,
    original_request: str,
    architecture_spec: ArchitectureSpec | None,
    code: CodeArtifacts,
    constraints: list[str],
) -> JudgeScore:
    files_text = "\n\n".join(f"--- {f.filename} ---\n{f.content}" for f in code.files)
    spec_text = architecture_spec.summary if architecture_spec else "(sin especificación disponible)"
    constraints_text = "\n".join(f"- {c}" for c in constraints) if constraints else "(ninguna)"

    user_message = (
        f"Petición original del usuario:\n{original_request}\n\n"
        f"Especificación técnica que debía seguir:\n{spec_text}\n\n"
        f"Restricciones técnicas explícitas:\n{constraints_text}\n\n"
        f"Código generado:\n{files_text}"
    )

    schema_hint = (
        '{"correctness": int, "readability": int, "plan_adherence": int, '
        '"constraints_compliance": int, "comment": str}'
    )

    response = await llm.generate(LLMRequest(messages=[
        LLMMessage(role="system", content=f"{JUDGE_SYSTEM_PROMPT}\n\nSchema:\n{schema_hint}"),
        LLMMessage(role="user", content=user_message),
    ], max_tokens=1024))

    import json
    import re
    match = re.search(r"\{.*\}", response.content, re.DOTALL)
    data = json.loads(match.group(0) if match else response.content)
    return JudgeScore.model_validate(data)