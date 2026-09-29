from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_PACKAGES = {
    "oncodex",
    "oncolab",
    "research",
    "evidence",
    "discovery",
    "execution",
    "jev",
    "oncox",
    "evaluation",
    "store",
    "observatory",
    "experiments",
}
FORBIDDEN: dict[str, set[str]] = {
    "evidence": {"oncodex", "oncox", "discovery", "observatory"},
    "execution": {"oncodex", "oncox", "discovery", "observatory", "jev"},
    "store": {"oncodex", "oncox", "discovery", "execution", "jev", "evidence", "research"},
    "oncox": {"oncodex"},
    "oncolab": {"oncodex", "oncox", "discovery", "observatory"},
}
SOURCE_ADAPTERS = {"execution.gdc"}
SOURCE_ADAPTER_OWNERS = {"execution", "experiments"}
REQUIRED_DOCS = {
    "AGENTS.md",
    "THESIS.md",
    "ARCHITECTURE.md",
    "docs/EPISTEMIC_CONSTITUTION.md",
    "docs/CONCEPT_BOOK.md",
    "docs/CAPABILITY_EVOLUTION.md",
    "docs/EVALUATION.md",
    "docs/LEARNING_CURRICULUM.md",
    "docs/EXPERIMENT_CATALOG.md",
    "docs/SOURCES.md",
}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def imported_roots(path: Path) -> set[str]:
    return {module.split(".")[0] for module in imported_modules(path)} & PROJECT_PACKAGES


def forbid_import_directions(root: Path) -> list[str]:
    errors: list[str] = []
    for package, forbidden in FORBIDDEN.items():
        for path in (root / package).rglob("*.py"):
            bad = imported_roots(path) & forbidden
            if bad:
                errors.append(
                    f"{path.relative_to(root)} imports forbidden package(s): {sorted(bad)}"
                )

    for package in sorted(PROJECT_PACKAGES - SOURCE_ADAPTER_OWNERS):
        for path in (root / package).rglob("*.py"):
            leaked = imported_modules(path) & SOURCE_ADAPTERS
            if leaked:
                errors.append(
                    f"{path.relative_to(root)} imports source adapter(s) {sorted(leaked)}; "
                    "source-specific code is confined to execution/ and experiments/"
                )
    return errors


def main() -> int:
    errors: list[str] = []

    if (ROOT / "harness").exists():
        errors.append("forbidden generic harness/ directory: oncodex/ is the harness boundary")
    if (ROOT / "oncojev").exists() and (ROOT / "oncojev" / "oncojev").exists():
        errors.append("forbidden nested oncojev/oncojev topology")

    for doc in REQUIRED_DOCS:
        if not (ROOT / doc).exists():
            errors.append(f"missing required knowledge file: {doc}")

    agents = ROOT / "AGENTS.md"
    if agents.exists():
        line_count = len(agents.read_text(encoding="utf-8").splitlines())
        if line_count > 130:
            errors.append(f"AGENTS.md is {line_count} lines; keep it navigation-oriented (<=130)")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for required in (".prompts/", ".env.local", ".oncojev/"):
        if required not in gitignore:
            errors.append(f".gitignore must contain {required}")

    errors.extend(forbid_import_directions(ROOT))

    if errors:
        print("ARCHITECTURE CHECK FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("architecture checks: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
