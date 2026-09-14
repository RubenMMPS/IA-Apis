from app.agents.constraint_checks import check_constraints_violations
from app.graph.state.code import CodeFile


def test_detects_sqlalchemy_import_when_forbidden():
    files = [CodeFile(filename="models.py", content="from sqlalchemy import Column\n")]
    violations = check_constraints_violations(["no utilizar SQLAlchemy"], files)
    assert len(violations) == 1
    assert "sqlalchemy" in violations[0]


def test_no_violation_when_constraint_respected():
    files = [CodeFile(filename="store.py", content="items_db = {}\n")]
    violations = check_constraints_violations(["persistencia en memoria mediante un diccionario"], files)
    assert violations == []


def test_no_constraints_means_no_checks():
    files = [CodeFile(filename="models.py", content="from sqlalchemy import Column\n")]
    violations = check_constraints_violations([], files)
    assert violations == []


def test_generic_database_constraint_catches_other_orms():
    files = [CodeFile(filename="db.py", content="import pymongo\n")]
    violations = check_constraints_violations(["no utilizar bases de datos"], files)
    assert len(violations) == 1
    assert "pymongo" in violations[0]


def test_unrelated_constraint_does_not_flag_unrelated_import():
    files = [CodeFile(filename="app.py", content="from fastapi import FastAPI\n")]
    violations = check_constraints_violations(["no utilizar SQLAlchemy"], files)
    assert violations == []