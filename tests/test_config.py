"""Tests for automatr.core.config — ConfigManager loading, saving, updating, and platform detection.

Covers: default config creation when no file exists, loading existing config.json,
saving config and verifying JSON output, update() with dotted keys (e.g. llm.model_path),
backward-compat behaviour with unknown top-level and nested JSON keys, and platform detection.
"""

import json
from pathlib import Path

from automatr.core.config import (
    Config,
    ConfigManager,
    LLMConfig,
    UIConfig,
    get_platform,
)

# ---------------------------------------------------------------------------
# 1. Default config creation when no file exists
# ---------------------------------------------------------------------------


def test_load_returns_defaults_when_no_file(tmp_path: Path) -> None:
    """ConfigManager.load() returns a Config with defaults when the file is missing."""
    mgr = ConfigManager(config_path=tmp_path / "nonexistent.json")
    config = mgr.load()

    assert isinstance(config, Config)
    assert isinstance(config.llm, LLMConfig)
    assert isinstance(config.ui, UIConfig)
    assert config.llm.server_port == 8080
    assert config.ui.theme == "dark"


# ---------------------------------------------------------------------------
# 2. Load existing config.json
# ---------------------------------------------------------------------------


def test_load_reads_existing_config_file(tmp_config_dir: Path) -> None:
    """ConfigManager.load() reads values from an existing config.json."""
    mgr = ConfigManager(config_path=tmp_config_dir / "config.json")
    config = mgr.load()

    assert config.llm.server_port == 8080
    assert config.ui.theme == "dark"
    assert config.ui.max_template_versions == 10


def test_load_with_partial_config_fills_defaults(tmp_path: Path) -> None:
    """load() fills in missing fields with defaults when config only has partial data."""
    partial = {"llm": {"server_port": 9090}}
    config_path = tmp_path / "partial.json"
    config_path.write_text(json.dumps(partial), encoding="utf-8")

    mgr = ConfigManager(config_path=config_path)
    config = mgr.load()

    assert config.llm.server_port == 9090
    assert config.ui.theme == "dark"   # default filled in


def test_load_corrupted_json_returns_defaults(tmp_path: Path) -> None:
    """load() returns defaults and does not raise when the JSON file is corrupt."""
    config_path = tmp_path / "corrupt.json"
    config_path.write_text("{not valid json", encoding="utf-8")

    mgr = ConfigManager(config_path=config_path)
    config = mgr.load()

    assert isinstance(config, Config)
    assert config.llm.server_port == 8080


# ---------------------------------------------------------------------------
# 3. Save config and verify JSON output
# ---------------------------------------------------------------------------


def test_save_writes_valid_json(tmp_path: Path) -> None:
    """ConfigManager.save() writes a valid JSON file to the config path."""
    config_path = tmp_path / "saved_config.json"
    mgr = ConfigManager(config_path=config_path)
    config = Config()
    config.ui.theme = "light"

    result = mgr.save(config)

    assert result is True
    assert config_path.exists()
    data = json.loads(config_path.read_text())
    assert data["ui"]["theme"] == "light"


def test_save_round_trips_llm_values(tmp_path: Path) -> None:
    """Saved LLM config values are preserved exactly when reloaded."""
    config_path = tmp_path / "roundtrip.json"
    mgr = ConfigManager(config_path=config_path)
    config = Config()
    config.llm.server_port = 7777
    config.llm.temperature = 0.3
    mgr.save(config)

    mgr2 = ConfigManager(config_path=config_path)
    loaded = mgr2.load()
    assert loaded.llm.server_port == 7777
    assert abs(loaded.llm.temperature - 0.3) < 1e-9


# ---------------------------------------------------------------------------
# 4. update() with dotted keys
# ---------------------------------------------------------------------------


def test_update_dotted_key_llm(tmp_path: Path) -> None:
    """update('llm.model_path', ...) correctly sets the nested llm attribute."""
    config_path = tmp_path / "update_test.json"
    mgr = ConfigManager(config_path=config_path)
    mgr.save(Config())   # create the file

    result = mgr.update(**{"llm.model_path": "/models/my.gguf"})
    assert result is True
    assert mgr.config.llm.model_path == "/models/my.gguf"


def test_update_dotted_key_ui(tmp_path: Path) -> None:
    """update('ui.theme', ...) correctly sets the nested ui attribute."""
    config_path = tmp_path / "update_ui.json"
    mgr = ConfigManager(config_path=config_path)
    mgr.save(Config())

    result = mgr.update(**{"ui.theme": "light"})
    assert result is True
    assert mgr.config.ui.theme == "light"


def test_update_unknown_dotted_key_is_silently_ignored(tmp_path: Path) -> None:
    """update() with a key that does not exist on the config object is ignored."""
    config_path = tmp_path / "update_unknown.json"
    mgr = ConfigManager(config_path=config_path)
    mgr.save(Config())

    # Should not raise — unknown keys are silently skipped
    result = mgr.update(**{"llm.nonexistent_field": "value"})
    assert result is True   # save still succeeds; unknown key is skipped


# ---------------------------------------------------------------------------
# 5. Unknown top-level keys in JSON are ignored (backward compat)
# ---------------------------------------------------------------------------


def test_load_config_with_unknown_top_level_keys(tmp_path: Path) -> None:
    """Config.from_dict() ignores unknown top-level keys in the JSON file."""
    data = {
        "llm": {"server_port": 8080},
        "ui": {"theme": "dark"},
        "future_section": {"new_key": "new_value"},
    }
    config_path = tmp_path / "future_config.json"
    config_path.write_text(json.dumps(data), encoding="utf-8")

    mgr = ConfigManager(config_path=config_path)
    config = mgr.load()
    assert config.llm.server_port == 8080
    assert config.ui.theme == "dark"


def test_from_dict_ignores_unknown_llm_nested_keys() -> None:
    """Config.from_dict() silently ignores unknown keys inside the 'llm' section."""
    data = {
        "llm": {"server_port": 9090, "future_llm_field": "oops"},
        "ui": {"theme": "dark"},
    }
    config = Config.from_dict(data)
    assert config.llm.server_port == 9090
    assert config.ui.theme == "dark"


def test_from_dict_ignores_unknown_ui_nested_keys() -> None:
    """Config.from_dict() silently ignores unknown keys inside the 'ui' section."""
    data = {
        "llm": {"server_port": 8080},
        "ui": {"theme": "light", "future_ui_widget": True},
    }
    config = Config.from_dict(data)
    assert config.llm.server_port == 8080
    assert config.ui.theme == "light"


# ---------------------------------------------------------------------------
# 6. Platform detection returns valid values
# ---------------------------------------------------------------------------


def test_get_platform_returns_known_value() -> None:
    """get_platform() returns one of the four known platform strings."""
    platform = get_platform()
    assert platform in {"windows", "linux", "wsl2", "macos", "unknown"}


def test_get_platform_returns_string() -> None:
    """get_platform() always returns a non-empty string."""
    platform = get_platform()
    assert isinstance(platform, str)
    assert len(platform) > 0
