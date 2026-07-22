"""Footer of the CSV module (spec B.4.4): counters, inline banner, save box."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from wishlistor.shared import i18n_fra
from wishlistor.shared.constants_util import C_BANNER_VISIBLE_LINES
from wishlistor.shared.validation_result import ValidationResult


class CsvFooterView(QWidget):
    """Three footer frames: row counters, warnings banner, save button."""

    def __init__(self, parent: QWidget) -> None:
        """Initialize the footer.

        Args:
            parent: The owning widget.
        """
        super().__init__(parent)
        self.setObjectName("csv_footer")
        self._on_save: Callable[[], None] | None = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._build_counters(), 0)
        layout.addWidget(self._build_banner(), 1)
        layout.addLayout(self._build_save_box(), 0)

    def _build_counters(self) -> QVBoxLayout:
        """Frame 1: total rows, shown rows, on-disk mtime."""
        self._total_label_var = QLabel(i18n_fra.CSV_TOTAL_ROWS.format(count=0), self)
        self._shown_label_var = QLabel(i18n_fra.CSV_SHOWN_ROWS.format(count=0), self)
        self._mtime_label_var = QLabel("", self)
        counters = QVBoxLayout()
        counters.addWidget(self._total_label_var)
        counters.addWidget(self._shown_label_var)
        counters.addWidget(self._mtime_label_var)
        return counters

    def _build_banner(self) -> QPlainTextEdit:
        """Frame 2: the 3-line inline WARNING/ERROR banner."""
        self._banner_var = QPlainTextEdit(self)
        self._banner_var.setObjectName("csv_banner")
        self._banner_var.setReadOnly(True)
        line_height = self._banner_var.fontMetrics().lineSpacing()
        self._banner_var.setFixedHeight(line_height * C_BANNER_VISIBLE_LINES + 30)
        return self._banner_var

    def _build_save_box(self) -> QVBoxLayout:
        """Frame 3: save button and last-save label."""
        self._save_button_var = QPushButton(i18n_fra.COMMON_SAVE, self)
        self._save_button_var.setObjectName("csv_save_button")
        self._save_button_var.setEnabled(False)
        self._save_button_var.clicked.connect(self._emit_save)
        self._last_save_label_var = QLabel(f"{i18n_fra.CSV_LAST_SAVE} : {i18n_fra.COMMON_EMPTY_VALUE}", self)
        box = QVBoxLayout()
        box.addWidget(self._save_button_var)
        box.addWidget(self._last_save_label_var)
        return box

    # -- api --------------------------------------------------------------------------

    def set_counts(self, total: int, shown: int) -> None:
        """Refresh the total and displayed row counters.

        Args:
            total: Number of rows in the document.
            shown: Number of rows after filters.
        """
        self._total_label_var.setText(i18n_fra.CSV_TOTAL_ROWS.format(count=total))
        self._shown_label_var.setText(i18n_fra.CSV_SHOWN_ROWS.format(count=shown))

    def set_mtime_label(self, label: str) -> None:
        """Refresh the on-disk mtime label.

        Args:
            label: Display text.
        """
        self._mtime_label_var.setText(label)

    def append_issues(self, rs: ValidationResult) -> None:
        """Append warnings and errors to the inline banner.

        Args:
            rs: Issues to list.
        """
        for issue in rs.issues:
            self._banner_var.appendPlainText(f"{issue.severity.value} : {issue.message}")

    def clear_banner(self) -> None:
        """Empty the inline banner."""
        self._banner_var.clear()

    def set_save_enabled(self, enabled: bool) -> None:
        """Enable or grey out the save button.

        Args:
            enabled: True when unsaved modifications exist.
        """
        self._save_button_var.setEnabled(enabled)

    def set_last_save_label(self, label: str) -> None:
        """Refresh the 'Dernière sauvegarde' label.

        Args:
            label: Display text.
        """
        self._last_save_label_var.setText(f"{i18n_fra.CSV_LAST_SAVE} : {label}")

    def bind_save_clicked(self, callback: Callable[[], None]) -> None:
        """Register the save button callback.

        Args:
            callback: Called on click.
        """
        self._on_save = callback

    def _emit_save(self) -> None:
        """Forward the save click."""
        if self._on_save is not None:
            self._on_save()


# EOF
