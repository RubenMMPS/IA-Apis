import re

from app.graph.state.code import CodeFile

# Palabras clave que, si aparecen en el texto de una constraint, activan la
# verificación de que ciertos imports NO estén presentes en el código.
_KEYWORD_TO_FORBIDDEN_IMPORTS = {
    "sqlalchemy": ["sqlalchemy"],
    "base de datos": ["sqlalchemy", "pymongo", "psycopg", "asyncpg", "pymysql"],
    "bases de datos": ["sqlalchemy", "pymongo", "psycopg", "asyncpg", "pymysql"],
    "sin dependencias externas": [],  # demasiado genérico para verificar por import; se deja solo al LLM
    "en memoria": ["sqlalchemy", "pymongo", "psycopg", "asyncpg", "pymysql"],
}


def _extract_imports(content: str) -> set[str]:
    modules = set()
    for line in content.splitlines():
        match = re.match(r"^\s*(?:from|import)\s+([a-zA-Z0-9_\.]+)", line)
        if match:
            modules.add(match.group(1).split(".")[0].lower())
    return modules


def check_constraints_violations(constraints: list[str], files: list[CodeFile]) -> list[str]:
    if not constraints:
        return []

    all_imports: set[str] = set()
    for f in files:
        all_imports |= _extract_imports(f.content)

    violations = []
    for constraint in constraints:
        constraint_lower = constraint.lower()
        for keyword, forbidden_modules in _KEYWORD_TO_FORBIDDEN_IMPORTS.items():
            if keyword in constraint_lower:
                found = all_imports & set(forbidden_modules)
                if found:
                    violations.append(
                        f"[verificación automática] La restricción '{constraint}' prohíbe "
                        f"esta tecnología, pero el código importa: {', '.join(sorted(found))}"
                    )

    return violations