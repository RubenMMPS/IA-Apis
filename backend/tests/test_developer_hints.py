from app.agents.developer import DeveloperAgent


class DummyLLM:
    pass


agent = DeveloperAgent(DummyLLM())


def test_detects_import_error():
    output = "ImportError while importing test module...\ncannot import name 'foo'"
    hint = agent._detect_import_issue_hint(output)
    assert hint is not None
    assert "nombres" in hint.lower() or "importación" in hint.lower()


def test_detects_module_not_found():
    output = "ModuleNotFoundError: No module named 'src'"
    hint = agent._detect_import_issue_hint(output)
    assert hint is not None


def test_detects_syntax_error():
    output = "SyntaxError: unterminated string literal (detected at line 42)"
    hint = agent._detect_import_issue_hint(output)
    assert hint is not None
    assert "sintaxis" in hint.lower()


def test_no_hint_for_assertion_error():
    output = "AssertionError: False is not true : should be valid"
    hint = agent._detect_import_issue_hint(output)
    assert hint is None


def test_no_hint_for_passing_output():
    output = "4 passed in 0.13s"
    hint = agent._detect_import_issue_hint(output)
    assert hint is None