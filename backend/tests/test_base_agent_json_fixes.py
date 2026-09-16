from app.agents.base import _fix_double_escaped_newlines
from app.graph.state.code import CodeArtifacts, CodeFile


def test_fixes_double_escaped_newlines():
    broken = CodeArtifacts(
        files=[CodeFile(filename="a.py", content='"""doc"""\\n\\nimport os\\n\\ndef f():\\n    pass')],
        notes="x",
    )
    fixed = _fix_double_escaped_newlines(broken)
    assert "\n" in fixed.files[0].content
    assert "\\n" not in fixed.files[0].content


def test_leaves_normal_content_untouched():
    normal = CodeArtifacts(
        files=[CodeFile(filename="a.py", content="def f():\n    return 1\n")],
        notes="x",
    )
    fixed = _fix_double_escaped_newlines(normal)
    assert fixed.files[0].content == "def f():\n    return 1\n"


def test_non_code_output_passthrough():
    class Dummy:
        pass
    d = Dummy()
    assert _fix_double_escaped_newlines(d) is d