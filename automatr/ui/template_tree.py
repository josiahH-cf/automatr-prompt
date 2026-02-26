"""Template tree widget for browsing and managing templates."""

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from automatr.core.config import get_config
from automatr.core.templates import Template, get_template_manager


class TemplateTreeWidget(QWidget):
    """Widget displaying a tree of templates organized by folder.

    Emits signals for template actions. MainWindow wires these to handlers.
    """

    template_selected = pyqtSignal(object)
    folder_selected = pyqtSignal()
    edit_requested = pyqtSignal(object)
    improve_requested = pyqtSignal(object)
    version_history_requested = pyqtSignal(object)
    template_deleted = pyqtSignal(str)
    new_template_requested = pyqtSignal()
    status_message = pyqtSignal(str, int)

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the template tree widget."""
        super().__init__(parent)
        self._current_template: Optional[Template] = None
        self._setup_ui()

    def _setup_ui(self):
        """Build the tree layout with header buttons and action bar."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 5, 10)
        header = QHBoxLayout()
        config = get_config()
        label_size = config.ui.font_size + 1
        self._label = QLabel("Templates")
        self._label.setStyleSheet(
            f"font-weight: bold; font-size: {label_size}pt;"
        )
        header.addWidget(self._label)

        new_folder_btn = QPushButton("📁")
        new_folder_btn.setMaximumWidth(30)
        new_folder_btn.setToolTip("Create new folder")
        new_folder_btn.clicked.connect(self._new_folder)
        header.addWidget(new_folder_btn)

        new_btn = QPushButton("+")
        new_btn.setMaximumWidth(30)
        new_btn.setToolTip("Create new template")
        new_btn.clicked.connect(self.new_template_requested.emit)
        header.addWidget(new_btn)

        layout.addLayout(header)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.tree)

        actions = QHBoxLayout()
        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("secondary")
        edit_btn.clicked.connect(self._request_edit)
        actions.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self._delete_selected)
        actions.addWidget(delete_btn)
        layout.addLayout(actions)

    # Public API

    def load_templates(self):
        """Reload the template tree from the TemplateManager."""
        self.tree.clear()
        manager = get_template_manager()
        templates_by_folder: dict[str, list[Template]] = {"": []}
        for folder in manager.list_folders():
            templates_by_folder[folder] = []

        for template in manager.list_all():
            folder = manager.get_template_folder(template)
            if folder not in templates_by_folder:
                templates_by_folder[folder] = []
            templates_by_folder[folder].append(template)

        total_count = 0

        # Root-level (uncategorized) templates
        for template in sorted(
            templates_by_folder.get("", []), key=lambda t: t.name.lower()
        ):
            item = QTreeWidgetItem([template.name])
            item.setData(0, Qt.ItemDataRole.UserRole, ("template", template))
            if template.description:
                item.setToolTip(0, template.description)
            self.tree.addTopLevelItem(item)
            total_count += 1
        # Folders with their templates
        for folder in sorted(templates_by_folder.keys()):
            if folder == "":
                continue
            folder_item = QTreeWidgetItem([f"📁 {folder}"])
            folder_item.setData(0, Qt.ItemDataRole.UserRole, ("folder", folder))
            folder_item.setExpanded(True)
            folder_templates = templates_by_folder[folder]
            if not folder_templates:
                folder_item.setToolTip(0, "Empty folder")
            for template in sorted(folder_templates, key=lambda t: t.name.lower()):
                child = QTreeWidgetItem([template.name])
                child.setData(0, Qt.ItemDataRole.UserRole, ("template", template))
                if template.description:
                    child.setToolTip(0, template.description)
                folder_item.addChild(child)
                total_count += 1
            self.tree.addTopLevelItem(folder_item)

        self.status_message.emit(f"Loaded {total_count} templates", 3000)

    def refresh(self):
        """Refresh the template list (alias for load_templates)."""
        self.load_templates()

    def select_template_by_name(self, name: str):
        """Programmatically select a template in the tree by name."""
        def _find(item: QTreeWidgetItem) -> bool:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == "template" and data[1].name == name:
                self.tree.setCurrentItem(item)
                self._on_item_clicked(item, 0)
                return True
            for i in range(item.childCount()):
                if _find(item.child(i)):
                    return True
            return False
        for i in range(self.tree.topLevelItemCount()):
            if _find(self.tree.topLevelItem(i)):
                break

    def get_current_template(self) -> Optional[Template]:
        """Return the currently selected template, or None."""
        return self._current_template

    # Internal slots

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle single click on a tree item."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data[0] == "template":
            self._current_template = data[1]
            self.template_selected.emit(data[1])
        else:
            self._current_template = None
            self.folder_selected.emit()

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double click — request edit for templates."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data[0] == "template":
            self.edit_requested.emit(data[1])

    def _show_context_menu(self, position):
        """Show the right-click context menu."""
        item = self.tree.itemAt(position)
        if not item:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        menu = QMenu(self)

        if data[0] == "template":
            template = data[1]

            edit_action = menu.addAction("Edit Template")
            edit_action.triggered.connect(
                lambda: self.edit_requested.emit(template)
            )

            improve_action = menu.addAction("Improve Template...")
            improve_action.triggered.connect(
                lambda: self.improve_requested.emit(template)
            )

            manager = get_template_manager()
            versions = manager.list_versions(template)
            if versions:
                history_action = menu.addAction(
                    f"Version History ({len(versions)})..."
                )
                history_action.triggered.connect(
                    lambda: self.version_history_requested.emit(template)
                )

            menu.addSeparator()

            delete_action = menu.addAction("Delete Template")
            delete_action.triggered.connect(self._delete_current_template)

        elif data[0] == "folder":
            delete_action = menu.addAction("Delete Folder")
            delete_action.triggered.connect(self._delete_selected)

        menu.exec(self.tree.mapToGlobal(position))

    def _request_edit(self):
        """Emit edit_requested for the currently selected template."""
        if self._current_template:
            self.edit_requested.emit(self._current_template)

    def _new_folder(self):
        """Prompt user to create a new template folder."""
        name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and name.strip():
            manager = get_template_manager()
            if manager.create_folder(name.strip()):
                self.load_templates()
                self.status_message.emit(
                    f"Created folder '{name.strip()}'", 3000
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Could not create folder '{name.strip()}'. "
                    "It may already exist or contain invalid characters.",
                )

    def _delete_selected(self):
        """Delete the selected item (template or folder)."""
        item = self.tree.currentItem()
        if not item:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        if data[0] == "template":
            self._delete_current_template()
        elif data[0] == "folder":
            self._delete_folder(data[1])

    def _delete_current_template(self):
        """Delete the currently selected template after confirmation."""
        if not self._current_template:
            return

        reply = QMessageBox.question(
            self,
            "Delete Template",
            f"Are you sure you want to delete '{self._current_template.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            manager = get_template_manager()
            name = self._current_template.name
            if manager.delete(self._current_template):
                self._current_template = None
                self.load_templates()
                self.template_deleted.emit(name)
                self.status_message.emit("Template deleted", 3000)
            else:
                QMessageBox.warning(
                    self,
                    "Delete Failed",
                    f"Failed to delete template '{name}'.",
                )

    def _delete_folder(self, folder_name: str):
        """Delete a template folder."""
        manager = get_template_manager()
        success, error_msg = manager.delete_folder(folder_name)
        if success:
            self.load_templates()
            self.status_message.emit(
                f"Deleted folder '{folder_name}'", 3000
            )
        else:
            QMessageBox.warning(self, "Cannot Delete Folder", error_msg)
