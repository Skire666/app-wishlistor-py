"""Modal dialogs of the CSV module (spec F / D.5): save guards and prompts."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QWidget

from wishlistor.shared import i18n_fra
from wishlistor.shared.enums.save_choice_enum import SaveChoiceEnum


def ask_unsaved_choice(parent: QWidget) -> SaveChoiceEnum:
    """Ask what to do with unsaved modifications (spec F).

    Args:
        parent: The owning widget.

    Returns:
        The user decision (E_CANCEL when the dialog is dismissed).
    """
    box = QMessageBox(parent)
    box.setWindowTitle(i18n_fra.CSV_UNSAVED_TITLE)
    box.setText(i18n_fra.CSV_UNSAVED_MESSAGE)
    save = box.addButton(i18n_fra.COMMON_SAVE, QMessageBox.ButtonRole.AcceptRole)
    save_as = box.addButton(i18n_fra.COMMON_SAVE_AS, QMessageBox.ButtonRole.ActionRole)
    discard = box.addButton(i18n_fra.COMMON_QUIT_WITHOUT_SAVING, QMessageBox.ButtonRole.DestructiveRole)
    box.addButton(i18n_fra.COMMON_CANCEL, QMessageBox.ButtonRole.RejectRole)
    box.exec()
    clicked = box.clickedButton()
    if clicked is save:
        return SaveChoiceEnum.E_SAVE
    if clicked is save_as:
        return SaveChoiceEnum.E_SAVE_AS
    if clicked is discard:
        return SaveChoiceEnum.E_DISCARD
    return SaveChoiceEnum.E_CANCEL


def ask_conflict_choice(parent: QWidget) -> SaveChoiceEnum:
    """Ask what to do when the file changed externally (spec D.5).

    Args:
        parent: The owning widget.

    Returns:
        The user decision (E_CANCEL when the dialog is dismissed).
    """
    box = QMessageBox(parent)
    box.setWindowTitle(i18n_fra.CSV_CONFLICT_TITLE)
    box.setText(i18n_fra.CSV_CONFLICT_MESSAGE)
    overwrite = box.addButton(i18n_fra.COMMON_OVERWRITE, QMessageBox.ButtonRole.AcceptRole)
    save_as = box.addButton(i18n_fra.COMMON_SAVE_AS, QMessageBox.ButtonRole.ActionRole)
    box.addButton(i18n_fra.COMMON_CANCEL, QMessageBox.ButtonRole.RejectRole)
    box.exec()
    clicked = box.clickedButton()
    if clicked is overwrite:
        return SaveChoiceEnum.E_OVERWRITE
    if clicked is save_as:
        return SaveChoiceEnum.E_SAVE_AS
    return SaveChoiceEnum.E_CANCEL


def ask_save_as_path(parent: QWidget, current_path: str) -> str:
    """Open the native save dialog.

    Args:
        parent: The owning widget.
        current_path: Initial location.

    Returns:
        The chosen path, or an empty string on cancel.
    """
    path, _selected = QFileDialog.getSaveFileName(
        parent, i18n_fra.CSV_SAVE_DIALOG_TITLE, current_path, i18n_fra.CSV_FILE_DIALOG_FILTER
    )
    return path


def ask_mass_comment(parent: QWidget) -> str | None:
    """Ask the comment to apply to the selected rows.

    Args:
        parent: The owning widget.

    Returns:
        The typed comment, or None on cancel.
    """
    text, accepted = QInputDialog.getText(parent, i18n_fra.CSV_EDIT_COMMENT_BUTTON, i18n_fra.CSV_COMMENT_PROMPT)
    return text if accepted else None


# EOF
