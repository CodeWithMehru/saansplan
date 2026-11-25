"""Architectural boundary tests enforcing unidirectional module dependencies via AST inspection."""

from __future__ import annotations

import ast
import re
from pathlib import Path


def get_imports(file_path: Path) -> list[str]:
    """Parse a python source file and return all imported module paths."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def test_engine_never_imports_routers_or_services() -> None:
    """Engine modules must be pure calculation and never depend on routers, services, or main."""
    engine_dir = Path("app/engine")
    forbidden_prefixes = ("app.routers", "app.services", "app.main")

    for py_file in engine_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        imports = get_imports(py_file)
        for imp in imports:
            for forbidden in forbidden_prefixes:
                assert not imp.startswith(forbidden), (
                    f"Boundary violation: {py_file} imports forbidden module {imp}"
                )


def test_services_never_import_routers() -> None:
    """Service layer must never depend on HTTP routers or main application."""
    services_dir = Path("app/services")
    forbidden_prefixes = ("app.routers", "app.main")

    for py_file in services_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        imports = get_imports(py_file)
        for imp in imports:
            for forbidden in forbidden_prefixes:
                assert not imp.startswith(forbidden), (
                    f"Boundary violation: {py_file} imports forbidden module {imp}"
                )


def test_schemas_never_import_engine_routers_or_services() -> None:
    """Data schemas must never depend on engine logic, routers, services, or main."""
    schemas_dir = Path("app/schemas")
    forbidden_prefixes = ("app.engine", "app.routers", "app.services", "app.main")

    for py_file in schemas_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        imports = get_imports(py_file)
        for imp in imports:
            for forbidden in forbidden_prefixes:
                assert not imp.startswith(forbidden), (
                    f"Boundary violation: {py_file} imports forbidden module {imp}"
                )


def test_core_never_imports_routers_or_engine() -> None:
    """Core settings and utilities must never depend on routers or engine."""
    core_dir = Path("app/core")
    forbidden_prefixes = ("app.routers", "app.engine", "app.services")

    for py_file in core_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        imports = get_imports(py_file)
        for imp in imports:
            for forbidden in forbidden_prefixes:
                assert not imp.startswith(forbidden), (
                    f"Boundary violation: {py_file} imports forbidden module {imp}"
                )


def test_environment_reads_only_in_settings_module() -> None:
    """All os.getenv and os.environ calls must strictly reside within app/core/settings.py."""
    app_dir = Path("app")
    allowed_file = Path("app/core/settings.py").resolve()

    for py_file in app_dir.rglob("*.py"):
        if py_file.resolve() == allowed_file:
            continue
        content = py_file.read_text(encoding="utf-8")
        assert not re.search(r"\bos\.(getenv|environ)\b", content), (
            f"Unauthorized environment access found in {py_file}; "
            "must use app.core.settings.get_settings()"
        )


def test_router_handlers_at_most_15_lines() -> None:
    """FastAPI route handler functions must be thin adapters of at most 15 lines."""
    routers_dir = Path("app/routers")
    for py_file in routers_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                # Detect route handlers by decorator presence (@router.get / @router.post)
                is_route = any(
                    isinstance(dec, ast.Call)
                    and isinstance(dec.func, ast.Attribute)
                    and dec.func.attr in ("get", "post", "put", "delete", "patch")
                    for dec in node.decorator_list
                )
                if is_route:
                    lines = (node.end_lineno or 0) - node.lineno + 1
                    assert lines <= 15, (
                        f"Handler {node.name} in {py_file.name} is {lines} lines (max allowed: 15)"
                    )
