import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def _load_check_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "check_architecture", ROOT / "scripts" / "check_architecture.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_architecture"] = module
    spec.loader.exec_module(module)
    return module


def test_forbidden_dependency_direction_is_rejected(tmp_path: Path) -> None:
    module = _load_check_module()
    package = tmp_path / "oncolab"
    package.mkdir()
    (package / "bad.py").write_text("from oncodex import agent\n", encoding="utf-8")

    errors = module.forbid_import_directions(tmp_path)

    assert any("oncolab" in error and "oncodex" in error for error in errors)


def test_source_adapter_leak_into_core_is_rejected(tmp_path: Path) -> None:
    module = _load_check_module()
    package = tmp_path / "oncolab"
    package.mkdir()
    (package / "bad.py").write_text(
        "from execution.gdc import GdcClient\n", encoding="utf-8"
    )

    errors = module.forbid_import_directions(tmp_path)

    assert any("execution.gdc" in error for error in errors)


def test_source_adapter_owners_may_import_their_adapter(tmp_path: Path) -> None:
    module = _load_check_module()
    package = tmp_path / "execution"
    package.mkdir()
    (package / "gdc.py").write_text(
        "from execution.ports import MeasuredResult\n", encoding="utf-8"
    )

    assert module.forbid_import_directions(tmp_path) == []
