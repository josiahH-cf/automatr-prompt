"""Output pane widget for displaying generated text."""

from typing import Optional

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from automatr.core.config import get_config


class OutputPaneWidget(QWidget):
    """Widget for displaying LLM output with copy/stop/clear controls.

    Manages the output text area, animated "Generating..." indicator,
    and streaming text append. Emits signals for stop requests.
    """

    stop_requested = pyqtSignal()
    status_message = pyqtSignal(str, int)

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the output pane widget."""
        super().__init__(parent)
        self._gen_dot_count = 0
        self._waiting_for_server = False
        self._setup_ui()

    def _setup_ui(self):
        """Build the output pane layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 10, 10)

        header = QHBoxLayout()
        config = get_config()
        label_size = config.ui.font_size + 1
        self._label = QLabel("Output")
        self._label.setStyleSheet(
            f"font-weight: bold; font-size: {label_size}pt;"
        )
        header.addWidget(self._label)
        header.addStretch()

        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setObjectName("secondary")
        self._copy_btn.clicked.connect(self._copy_output)
        header.addWidget(self._copy_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setObjectName("secondary")
        self._stop_btn.clicked.connect(self.stop_requested.emit)
        self._stop_btn.setVisible(False)
        header.addWidget(self._stop_btn)

        self._generating_label = QLabel("Generating...")
        self._generating_label.setStyleSheet(
            "color: #808080; font-style: italic;"
        )
        self._generating_label.setVisible(False)
        header.addWidget(self._generating_label)

        self._gen_timer = QTimer()
        self._gen_timer.timeout.connect(self._update_generating_dots)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(self.clear)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        self._output_text = QTextEdit()
        self._output_text.setReadOnly(True)
        self._output_text.setPlaceholderText(
            "Generated output will appear here.\n\n"
            "1. Select a template from the left\n"
            "2. Fill in the variables\n"
            "3. Click Generate"
        )
        layout.addWidget(self._output_text)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append_text(self, token: str):
        """Append streaming text to the output, clearing any wait message."""
        if self._waiting_for_server:
            self._waiting_for_server = False
            self._generating_label.setText("Generating...")
        cursor = self._output_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(token)
        self._output_text.setTextCursor(cursor)
        self._output_text.ensureCursorVisible()

    def set_text(self, text: str):
        """Set the full output text (non-streaming)."""
        self._output_text.setPlainText(text)

    def get_text(self) -> str:
        """Return the current output text."""
        return self._output_text.toPlainText()

    def clear(self):
        """Clear the output text area."""
        self._output_text.clear()

    def set_streaming(self, streaming: bool):
        """Show or hide the stop button and generating indicator."""
        self._stop_btn.setVisible(streaming)
        self._generating_label.setVisible(streaming)
        if streaming:
            self._gen_dot_count = 0
            self._waiting_for_server = False
            self._gen_timer.start(500)
        else:
            self._gen_timer.stop()

    def set_waiting_message(self, attempt: int, max_attempts: int):
        """Update the generating label with a server wait message."""
        self._waiting_for_server = True
        self._generating_label.setText(
            f"Model starting... (attempt {attempt}/{max_attempts})"
        )

    # ------------------------------------------------------------------
    # Internal slots
    # ------------------------------------------------------------------

    def _copy_output(self):
        """Copy output text to clipboard."""
        text = self._output_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self._copy_btn.setText("Copied!")
            QTimer.singleShot(2000, lambda: self._copy_btn.setText("Copy"))

    def _update_generating_dots(self):
        """Animate the dots on the generating label."""
        self._gen_dot_count = (self._gen_dot_count + 1) % 4
        dots = "." * (self._gen_dot_count + 1)
        if not self._waiting_for_server:
            self._generating_label.setText(f"Generating{dots}")
