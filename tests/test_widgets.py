"""Widget-level tests for extracted UI components.

Tests the four extracted widgets (TemplateTreeWidget, VariableFormWidget,
OutputPaneWidget, LLMToolbar) using pytest-qt to verify signal emission,
public API behaviour, and initial state.
"""

from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt

from automatr.core.templates import Template, Variable
from automatr.ui.llm_toolbar import LLMToolbar
from automatr.ui.output_pane import OutputPaneWidget
from automatr.ui.template_tree import TemplateTreeWidget
from automatr.ui.variable_form import VariableFormWidget


@pytest.fixture
def sample_template():
    """A simple template fixture for widget tests."""
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


def _make_templates():
    """Create two test templates."""
    return [
        Template(name="Alpha", content="A: {{var1}}", description="Alpha",
                 variables=[Variable(name="var1", label="V1")]),
        Template(name="Beta", content="B: {{var1}}", description="Beta",
                 variables=[Variable(name="var1", label="V1")]),
    ]


# -- TemplateTreeWidget tests -----------------------------------------------

def test_tree_populates_and_emits_template_selected(qtbot):
    """Tree widget loads templates and emits template_selected on click."""
    templates = _make_templates()

    with patch("automatr.ui.template_tree.get_template_manager") as mock_mgr:
        manager = MagicMock()
        manager.list_all.return_value = templates
        manager.list_folders.return_value = []
        manager.get_template_folder.return_value = ""
        mock_mgr.return_value = manager

        widget = TemplateTreeWidget()
        qtbot.addWidget(widget)
        widget.load_templates()

        assert widget.tree.topLevelItemCount() == 2

        first_item = widget.tree.topLevelItem(0)
        with qtbot.waitSignal(widget.template_selected, timeout=1000):
            widget.tree.setCurrentItem(first_item)
            widget._on_item_clicked(first_item, 0)


def test_tree_emits_folder_selected(qtbot):
    """Tree widget emits folder_selected when a folder item is clicked."""
    t = Template(name="InFolder", content="test", description="",
                 variables=[])

    with patch("automatr.ui.template_tree.get_template_manager") as mock_mgr:
        manager = MagicMock()
        manager.list_all.return_value = [t]
        manager.list_folders.return_value = ["MyFolder"]
        manager.get_template_folder.return_value = "MyFolder"
        mock_mgr.return_value = manager

        widget = TemplateTreeWidget()
        qtbot.addWidget(widget)
        widget.load_templates()

        folder_item = None
        for i in range(widget.tree.topLevelItemCount()):
            item = widget.tree.topLevelItem(i)
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == "folder":
                folder_item = item
                break

        assert folder_item is not None
        with qtbot.waitSignal(widget.folder_selected, timeout=1000):
            widget.tree.setCurrentItem(folder_item)
            widget._on_item_clicked(folder_item, 0)


# -- VariableFormWidget tests ------------------------------------------------

def test_form_generates_fields_and_get_values(qtbot, sample_template):
    """Form creates input fields for template variables and returns values."""
    widget = VariableFormWidget()
    qtbot.addWidget(widget)
    widget.set_template(sample_template)

    values = widget.get_values()
    assert "recipient" in values
    assert "message_type" in values
    assert values["recipient"] == "World"
    assert values["message_type"] == "test"


def test_form_emits_generate_requested(qtbot, sample_template):
    """Clicking the generate button emits generate_requested signal."""
    widget = VariableFormWidget()
    qtbot.addWidget(widget)
    widget.set_template(sample_template)
    widget.set_buttons_enabled(True)

    with qtbot.waitSignal(widget.generate_requested, timeout=1000):
        widget.generate_btn.click()


def test_form_clear_resets_values(qtbot, sample_template):
    """Clearing the form resets all variable field values."""
    widget = VariableFormWidget()
    qtbot.addWidget(widget)
    widget.set_template(sample_template)

    assert widget.get_values()["recipient"] == "World"
    widget.clear()
    values = widget.get_values()
    # After clear, fields still exist but contain empty strings
    assert values.get("recipient", "") == ""
    assert values.get("message_type", "") == ""


# -- OutputPaneWidget tests --------------------------------------------------

def test_output_pane_append_and_get_text(qtbot):
    """Output pane appends tokens and returns accumulated text."""
    widget = OutputPaneWidget()
    qtbot.addWidget(widget)

    widget.append_text("Hello ")
    widget.append_text("World")

    text = widget.get_text()
    assert "Hello " in text
    assert "World" in text


def test_output_pane_emits_stop_requested(qtbot):
    """Stop button emits stop_requested signal."""
    widget = OutputPaneWidget()
    qtbot.addWidget(widget)
    widget.set_streaming(True)

    with qtbot.waitSignal(widget.stop_requested, timeout=1000):
        widget._stop_btn.click()


# -- LLMToolbar tests -------------------------------------------------------

def test_toolbar_emits_server_running_changed(qtbot):
    """LLMToolbar emits server_running_changed on check_status."""
    widget = LLMToolbar()
    qtbot.addWidget(widget)

    with patch("automatr.ui.llm_toolbar.get_llm_server") as mock_srv:
        server = MagicMock()
        server.is_running.return_value = True
        mock_srv.return_value = server

        with qtbot.waitSignal(widget.server_running_changed, timeout=1000):
            widget.check_status()

    assert widget.server_btn.text() == "Open Server"


def test_toolbar_check_status_updates_ui(qtbot):
    """check_status updates button text and label based on server state."""
    widget = LLMToolbar()
    qtbot.addWidget(widget)

    with patch("automatr.ui.llm_toolbar.get_llm_server") as mock_srv:
        server = MagicMock()
        server.is_running.return_value = False
        mock_srv.return_value = server
        widget.check_status()

        assert widget.server_btn.text() == "Start Server"
        assert "Not Running" in widget.llm_status_label.text()
        assert not widget.stop_server_btn.isEnabled()

        server.is_running.return_value = True
        widget.check_status()

        assert widget.server_btn.text() == "Open Server"
        assert "Connected" in widget.llm_status_label.text()
        assert widget.stop_server_btn.isEnabled()
