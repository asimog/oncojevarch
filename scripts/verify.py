from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    run([sys.executable, "scripts/check_architecture.py"])
    run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            *[
                str(ROOT / p)
                for p in (
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
                )
            ],
        ]
    )
    run([sys.executable, "-m", "pytest"])
    if importlib.util.find_spec("ruff"):
        run([sys.executable, "-m", "ruff", "check", "."])
    else:
        print("ruff not found; skipped (install .[dev] for full verification)")
    if importlib.util.find_spec("mypy"):
        run([sys.executable, "-m", "mypy", "."])
    else:
        print("mypy not found; skipped (install .[dev] for full verification)")
    print("verification: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
