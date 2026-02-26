"""Mixin providing window state persistence for MainWindow."""

import base64

from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QCloseEvent, QGuiApplication

from automatr.core.config import get_config, save_config


class WindowStateMixin:
    """Window geometry, state save/restore, and about dialog.

    Mixed into MainWindow. Expects the host class to provide:
    template_tree (tree widget), current_template, splitter.
    """

    def _is_geometry_visible(self, geometry_data: QByteArray) -> bool:
        """Check if restored geometry would be visible on any connected screen.

        Uses a 50% overlap threshold.
        """
        current_geo = self.saveGeometry()
        self.restoreGeometry(geometry_data)
        window_rect = self.frameGeometry()
        self.restoreGeometry(current_geo)

        for screen in QGuiApplication.screens():
            screen_rect = screen.availableGeometry()
            intersection = window_rect.intersected(screen_rect)
            if not intersection.isEmpty():
                window_area = window_rect.width() * window_rect.height()
                if window_area > 0:
                    overlap_area = intersection.width() * intersection.height()
                    if overlap_area / window_area >= 0.5:
                        return True
        return False

    def _restore_state(self):
        """Restore window and app state from config."""
        config = get_config()
        geometry_valid = False

        if config.ui.window_geometry:
            try:
                geometry_bytes = base64.b64decode(config.ui.window_geometry)
                geometry_data = QByteArray(geometry_bytes)
                if self._is_geometry_visible(geometry_data):
                    self.restoreGeometry(geometry_data)
                    geometry_valid = True
                else:
                    config.ui.window_geometry = ""
                    config.ui.window_maximized = False
                    save_config(config)
            except Exception:
                config.ui.window_geometry = ""
                save_config(config)

        if geometry_valid and config.ui.window_maximized:
            self.setWindowState(Qt.WindowState.WindowMaximized)

        if config.ui.expanded_folders:
            for i in range(self.template_tree.topLevelItemCount()):
                item = self.template_tree.topLevelItem(i)
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data and data[0] == "folder" and data[1] in config.ui.expanded_folders:
                    item.setExpanded(True)

        if config.ui.last_template:
            self._select_template_in_tree(config.ui.last_template)

    def closeEvent(self, event: QCloseEvent):
        """Save window and app state when closing."""
        config = get_config()

        geometry_bytes = bytes(self.saveGeometry())
        config.ui.window_geometry = base64.b64encode(geometry_bytes).decode("ascii")
        config.ui.window_maximized = self.isMaximized()

        if not self.isMaximized():
            config.ui.window_width = self.width()
            config.ui.window_height = self.height()

        config.ui.splitter_sizes = self.splitter.sizes()

        if self.current_template:
            config.ui.last_template = self.current_template.name

        expanded = []
        for i in range(self.template_tree.topLevelItemCount()):
            item = self.template_tree.topLevelItem(i)
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == "folder" and item.isExpanded():
                expanded.append(data[1])
        config.ui.expanded_folders = expanded

        save_config(config)
        event.accept()
