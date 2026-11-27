"""Documentation consistency checker.

Verifies that all file paths, markdown links, and Makefile targets
referenced across the documentation suite exist and are valid.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

PATH_PATTERN = re.compile(r"`((?:app|tests|scripts|docs|\.github)/[a-zA-Z0-9_\-\./]+)`")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
MAKE_PATTERN = re.compile(r"(?:`|^\s*|<br>)make\s+([a-zA-Z0-9_-]+)", re.MULTILINE)
ALLOWED_MAKE_FLAGS = {"-j", "-k", "-v", "-n", "-s"}
EXCLUDED_LINK_PREFIXES = ("http://", "https://", "#", "mailto:", "javascript:")


def get_makefile_targets(root: Path) -> set[str]:
    """Extract all declared target names from the Makefile."""
    makefile = root / "Makefile"
    if not makefile.exists():
        return set()
    return set(re.findall(r"^([a-zA-Z0-9_-]+):", makefile.read_text(), re.MULTILINE))


def _check_targets(content: str, filename: str, targets: set[str]) -> list[str]:
    """Validate Makefile target invocations in markdown content."""
    return [
        f"{filename}: unknown Makefile target 'make {target}'"
        for target in MAKE_PATTERN.findall(content)
        if target not in targets and target not in ALLOWED_MAKE_FLAGS
    ]


def _check_links(content: str, filename: str, root: Path, md_path: Path) -> list[str]:
    """Validate relative markdown file links."""
    errors: list[str] = []
    for text, link in LINK_PATTERN.findall(content):
        if any(link.startswith(p) for p in EXCLUDED_LINK_PREFIXES):
            continue
        clean_link = link.split("#")[0]
        if not clean_link:
            continue
        if not (root / clean_link).exists() and not (md_path.parent / clean_link).exists():
            errors.append(f"{filename}: broken link [{text}]({link})")
    return errors


def _check_paths(content: str, filename: str, root: Path) -> list[str]:
    """Validate backticked filesystem paths."""
    errors: list[str] = []
    for match in PATH_PATTERN.findall(content):
        clean_path = match.rstrip(".,:;")
        if "*" in clean_path:
            if not list(root.glob(clean_path)):
                errors.append(f"{filename}: broken glob `{clean_path}`")
        elif not (root / clean_path).exists():
            errors.append(f"{filename}: broken file path `{clean_path}`")
    return errors


def check_markdown_files(root: Path) -> list[str]:
    """Check all markdown files for valid paths, targets, and links."""
    errors: list[str] = []
    targets = get_makefile_targets(root)
    md_files = sorted(
        [md for md in root.glob("*.md") if not md.name.startswith(".")]
        + [md for md in (root / "docs").glob("**/*.md") if not md.name.startswith(".")]
    )

    for md in md_files:
        content = md.read_text(encoding="utf-8")
        errors.extend(_check_targets(content, md.name, targets))
        errors.extend(_check_links(content, md.name, root, md))
        errors.extend(_check_paths(content, md.name, root))

    return errors


def main() -> int:
    """Run the consistency check and report findings."""
    errors = check_markdown_files(PROJECT_ROOT)
    if errors:
        print(f"Documentation consistency check FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("Documentation consistency check PASSED: all paths, targets, and links valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
