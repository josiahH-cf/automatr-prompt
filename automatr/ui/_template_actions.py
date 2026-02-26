"""Mixin providing template CRUD orchestration for MainWindow."""

from typing import Optional

from PyQt6.QtWidgets import QInputDialog, QMessageBox

from automatr.core.config import get_config, save_config
from automatr.core.templates import Template, get_template_manager
from automatr.integrations.llm import get_llm_server
from automatr.ui.template_editor import TemplateEditor
from automatr.ui.template_generate import (
    GenerationPromptEditor,
    ImprovementPromptEditor,
)
from automatr.ui.template_improve import TemplateImproveDialog


class TemplateActionsMixin:
    """Template CRUD, version history, and AI instruction editing.

    Mixed into MainWindow. Expects the host class to provide:
    current_template, variable_form, template_tree_widget,
    status_bar, llm_toolbar.
    """

    def _new_template(self):
        """Create a new template."""
        config = get_config()
        dialog = TemplateEditor(parent=self, last_folder=config.ui.last_editor_folder)
        dialog.template_saved.connect(self._on_template_saved)
        dialog.exec()
        config.ui.last_editor_folder = dialog.folder_combo.currentData() or ""
        save_config(config)

    def _edit_template(self, template: Optional[Template] = None):
        """Edit the given or currently selected template."""
        target = template or self.current_template
        if not target:
            return
        dialog = TemplateEditor(target, parent=self)
        dialog.template_saved.connect(self._on_template_saved)
        dialog.exec()

    def _improve_template(self, template: Optional[Template] = None):
        """Improve the selected template using AI based on user feedback."""
        target = template or self.current_template
        if not target:
            return

        feedback, ok = QInputDialog.getMultiLineText(
            self,
            "Improve Template",
            "How could this template be better?\n"
            "(What isn't working or should be different?)",
            "",
        )
        if not ok:
            return

        server = get_llm_server()
        if not server.is_running():
            reply = QMessageBox.question(
                self,
                "LLM Not Running",
                "The LLM server is not running. Would you like to start it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                success, message = server.start()
                if not success:
                    QMessageBox.critical(self, "Error", message)
                    return
                self.llm_toolbar.check_status()
            else:
                return

        dialog = TemplateImproveDialog(
            target,
            initial_feedback=feedback.strip() if feedback else "",
            parent=self,
        )
        dialog.changes_applied.connect(self._on_improvement_applied)
        dialog.exec()

    def _on_improvement_applied(self, new_content: str):
        """Handle improved template content (creates version snapshot first)."""
        if not self.current_template:
            return

        manager = get_template_manager()
        manager.create_version(self.current_template, note="Before AI improvement")

        self.current_template.content = new_content
        self.current_template.refinements = []

        folder = manager.get_template_folder(self.current_template)
        if manager.save_to_folder(self.current_template, folder):
            self.status_bar.showMessage("Template improved and saved", 3000)
            self.template_tree_widget.refresh()
            self.variable_form.set_template(self.current_template)
        else:
            QMessageBox.critical(self, "Error", "Failed to save improved template")

    def _show_version_history(self, template: Optional[Template] = None):
        """Show version history dialog for the given or current template."""
        target = template or self.current_template
        if not target:
            return

        manager = get_template_manager()
        versions = manager.list_versions(target)

        if not versions:
            QMessageBox.information(
                self, "No Version History",
                "This template has no version history to revert to.",
            )
            return

        items = []
        for v in reversed(versions):
            timestamp = v.timestamp[:19].replace("T", " ") if v.timestamp else "Unknown"
            label = f"v{v.version}"
            if v.version == 1:
                label += " (Original)"
            if v.note:
                label += f" - {v.note}"
            label += f" [{timestamp}]"
            items.append(label)

        item, ok = QInputDialog.getItem(
            self, "Revert Template",
            f"Select a version to revert '{target.name}' to:",
            items, 0, False,
        )
        if not ok or not item:
            return

        selected_idx = items.index(item)
        selected_version = versions[-(selected_idx + 1)]

        reply = QMessageBox.question(
            self, "Confirm Revert",
            f"Revert to version {selected_version.version}?\n\n"
            "This will replace the current template content with the "
            "selected version.\nA backup of the current state will be saved.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        restored = manager.restore_version(
            target, selected_version.version, create_backup=True,
        )
        if restored:
            self.current_template = restored
            self.template_tree_widget.refresh()
            self.variable_form.set_template(self.current_template)
            self.status_bar.showMessage(
                f"Reverted to version {selected_version.version}", 3000,
            )
        else:
            QMessageBox.critical(self, "Error", "Failed to revert template")

    def _on_template_saved(self, template: Template):
        """Handle template saved signal."""
        self.template_tree_widget.load_templates()
        self.template_tree_widget.select_template_by_name(template.name)

    def _edit_generate_instructions(self):
        """Edit the AI instructions for template generation."""
        reply = QMessageBox.question(
            self, "Edit Generation Instructions?",
            "Editing these instructions will affect how all future "
            "template generation works.\n\nAre you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            GenerationPromptEditor(self).exec()

    def _edit_improve_instructions(self):
        """Edit the AI instructions for template improvement."""
        reply = QMessageBox.question(
            self, "Edit Improvement Instructions?",
            "Editing these instructions will affect how all future template "
            "improvements are generated.\n\nAre you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            ImprovementPromptEditor(self).exec()
