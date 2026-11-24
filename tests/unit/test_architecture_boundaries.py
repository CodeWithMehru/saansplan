"""Architectural boundary tests enforcing unidirectional module dependencies via AST inspection."""

import ast
from pathlib import Path


def get_imports(file_path: Path) -> list[str]:
    """Parse a python source file and return all imported module paths."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def test_engine_never_imports_routers_or_services():
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


def test_schemas_never_import_engine_routers_or_services():
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


def test_core_never_imports_routers_or_engine():
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
