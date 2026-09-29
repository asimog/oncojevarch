from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

from oncodex.config import Settings


def test_local_configuration_loads_aliases_without_overriding_process_env(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    for name in ("OPENROUTER_API_KEY", "TYPESAFE_API_KEY", "JEV_MODEL"):
        monkeypatch.delenv(name, raising=False)
    (tmp_path / ".env.local").write_text(
        "OPENROUTER_API_KEY=local-key\n"
        "TYPESAFE_API_KEY=typesafe-key\n"
        "LLM_MODEL=local-model\n"
        "JEV_MODEL=jev-local\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("LLM_MODEL", "process-model")

    settings = Settings.from_env(tmp_path)

    assert settings.agent_model == "process-model"
    assert settings.jev_model == "jev-local"
    assert settings.openrouter_api_key == "local-key"
    assert settings.typesafe_api_key == "typesafe-key"
