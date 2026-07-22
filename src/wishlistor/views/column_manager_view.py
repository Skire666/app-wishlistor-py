"""'Gestion des colonnes' dialog: show/hide and reorder the CSV columns."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QWidget

from wishlistor.shared.i18n_fra import CSV_MANAGE_COLUMNS
from wishlistor.views.column_nickname_table_view import ColumnNicknameTableView

_DIALOG_MIN_WIDTH_PX: int = 500
_DIALOG_MIN_HEIGHT_PX: int = 450


def ask_visible_columns(
    parent: QWidget, available: list[str], visible: list[str], nicknames: dict[str, str] | None = None
) -> tuple[list[str], dict[str, str]] | None:
    """Open the column manager and return the new visible order and nicknames.

    Args:
        parent: The owning widget.
        available: Every column of the document, in current display order first.
        visible: Currently visible columns, in display order.
        nicknames: Current column name to display nickname mapping.

    Returns:
        The checked columns in their new order plus the edited nickname
        mapping, or None on cancel.
    """
    dialog = QDialog(parent)
    dialog.setObjectName("column_manager_dialog")
    dialog.setWindowTitle(CSV_MANAGE_COLUMNS)
    dialog.setMinimumSize(_DIALOG_MIN_WIDTH_PX, _DIALOG_MIN_HEIGHT_PX)
    checklist = ColumnNicknameTableView(dialog)
    ordered = [name for name in visible if name in available]
    ordered.extend(name for name in available if name not in ordered)
    checklist.set_items([(name, name in visible) for name in ordered], nicknames)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout = QVBoxLayout(dialog)
    layout.addWidget(checklist)
    layout.addWidget(buttons)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return checklist.checked_labels(), checklist.nicknames()
    return None


# EOF
