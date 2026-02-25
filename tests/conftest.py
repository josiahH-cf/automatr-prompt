"""Shared pytest fixtures for the automatr-prompt test suite.

Provides reusable test infrastructure: isolated config dirs, template dirs,
and pre-built Template objects. All fixtures use tmp_path for isolation.
"""

import json
from pathlib import Path

import pytest

from automatr.core.templates import Template, Variable


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    """Temporary config directory pre-populated with a default config.json.

    Returns:
        Path to a directory containing a valid config.json.
    """
    config = {
        "llm": {
            "model_path": "",
            "model_dir": "",
            "server_port": 8080,
            "context_size": 4096,
            "gpu_layers": 0,
            "server_binary": "",
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1.0,
            "top_k": 40,
            "repeat_penalty": 1.1,
        },
        "ui": {
            "theme": "dark",
            "window_width": 900,
            "window_height": 700,
            "font_size": 13,
            "window_x": -1,
            "window_y": -1,
            "window_maximized": False,
            "window_geometry": "",
            "splitter_sizes": [200, 300, 400],
            "last_template": "",
            "expanded_folders": [],
            "last_editor_folder": "",
            "max_template_versions": 10,
        },
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return tmp_path


@pytest.fixture
def tmp_templates_dir(tmp_path: Path) -> Path:
    """Temporary templates directory pre-populated with 3 sample template JSON files.

    Returns:
        Path to a directory containing sample template JSON files.
    """
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    templates = [
        {
            "name": "Code Review",
            "content": "Review this code:\n\n{{code}}\n\nFocus on: {{focus_area}}",
            "description": "Reviews code for quality issues",
            "trigger": ":review",
            "variables": [
                {"name": "code", "label": "Code", "multiline": True},
                {"name": "focus_area", "label": "Focus Area", "default": "correctness"},
            ],
        },
        {
            "name": "Summarize Text",
            "content": "Summarize the following in {{num_sentences}} sentences:\n\n{{text}}",
            "description": "Summarizes a block of text",
            "variables": [
                {"name": "text", "label": "Text to Summarize", "multiline": True},
                {"name": "num_sentences", "label": "Sentence Count", "default": "3"},
            ],
        },
        {
            "name": "Simple Greeting",
            "content": "Hello, {{name}}! How can I help you today?",
            "description": "A simple greeting template",
            "variables": [
                {"name": "name", "label": "Name", "default": "World"},
            ],
        },
    ]

    for t in templates:
        filename = t["name"].lower().replace(" ", "_") + ".json"
        path = templates_dir / filename
        path.write_text(json.dumps(t, indent=2), encoding="utf-8")

    return templates_dir


@pytest.fixture
def sample_template() -> Template:
    """A pre-built Template object with variables for use in tests.

    Returns:
        Template with two variables and a trigger field.
    """
    return Template(
        name="Test Template",
        content="Hello {{recipient}}, this is a {{message_type}} message.",
        description="A template for testing",
        trigger=":test",
        variables=[
            Variable(name="recipient", label="Recipient", default="World"),
            Variable(name="message_type", label="Message Type", default="test"),
        ],
    )
