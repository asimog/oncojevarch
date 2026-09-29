import subprocess
import sys


def test_architecture_script_passes() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/check_architecture.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
