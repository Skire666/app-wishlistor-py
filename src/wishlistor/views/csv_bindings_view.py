"""ICsvView callback-registration hooks for CsvView.

Mixed into CsvView — extracted from csv_view.py to keep it maintainable
(Furripe MIR121: low maintainability index on the full view).
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QLabel

from wishlistor.shared import i18n_fra
from wishlistor.views.csv_header_state_view import CsvHeaderStateView
from wishlistor.views.csv_table_model_view import CsvTableModelView


class CsvBindingsMixin:
    """ICsvView callback-registration hooks for CsvView, split out to keep it maintainable.

    Declares the host attributes it relies on (set by ``CsvView.__init__``/`_build_*`);
    it is never instantiated on its own.
    """

    _callbacks: dict[str, Callable[..., None]]
    _model_var: CsvTableModelView
    _header_state_var: CsvHeaderStateView
    _selected_label_var: QLabel

    def bind_project_selected(self, callback: Callable[[str], None]) -> None:
        """Register the project combo callback (receives the project id)."""
        self._callbacks["project_selected"] = callback

    def bind_open_folder_clicked(self, callback: Callable[[], None]) -> None:
        """Register the 'Ouvrir dossier' hyperlink callback."""
        self._callbacks["open_folder"] = callback

    def bind_project_options_clicked(self, callback: Callable[[], None]) -> None:
        """Register the 'Options du projet' button callback."""
        self._callbacks["project_options"] = callback

    def bind_url_submitted(self, callback: Callable[[str], None]) -> None:
        """Register the URL submission callback."""
        self._callbacks["url_submitted"] = callback

    def bind_mass_tags_clicked(self, callback: Callable[[], None]) -> None:
        """Register the 'Modifier les tags' button callback."""
        self._callbacks["mass_tags"] = callback

    def bind_mass_comment_clicked(self, callback: Callable[[], None]) -> None:
        """Register the 'Modifier le commentaire' button callback."""
        self._callbacks["mass_comment"] = callback

    def bind_delete_rows_clicked(self, callback: Callable[[], None]) -> None:
        """Register the 'Supprimer la ligne' button callback."""
        self._callbacks["delete_rows"] = callback

    def bind_selection_changed(self, callback: Callable[[int], None]) -> None:
        """Register the checked-row-count callback."""
        self._model_var.bind_check_changed(self._make_selection_relay(callback))

    def _make_selection_relay(self, callback: Callable[[int], None]) -> Callable[[int], None]:
        """Wrap the presenter callback to refresh the selection labels first."""

        def _relay(count: int) -> None:
            self._selected_label_var.setText(i18n_fra.CSV_SELECTED_COUNT.format(count=count))
            callback(count)

        return _relay

    def bind_cell_edited(self, callback: Callable[[int, str, str], None]) -> None:
        """Register the cell edit callback (doc row, column name, new value)."""
        self._model_var.bind_cell_edited(callback)

    def bind_row_tags_edited(self, callback: Callable[[int, frozenset[str]], None]) -> None:
        """Register the tag selector callback (doc row, final tag labels)."""
        self._callbacks["row_tags_edited"] = callback

    def bind_link_activated(self, callback: Callable[[str], None]) -> None:
        """Register the link-cell click callback (receives the cell value)."""
        self._callbacks["link_activated"] = callback

    def bind_save_clicked(self, callback: Callable[[], None]) -> None:
        """Register the save button / Ctrl+S callback."""
        self._callbacks["save"] = callback

    def bind_undo(self, callback: Callable[[], None]) -> None:
        """Register the Ctrl+Z callback."""
        self._callbacks["undo"] = callback

    def bind_redo(self, callback: Callable[[], None]) -> None:
        """Register the Ctrl+Y callback."""
        self._callbacks["redo"] = callback

    def bind_shortcut_tags(self, callback: Callable[[str], None]) -> None:
        """Register the Ctrl+O / Ctrl+N / Ctrl+T callback (receives the shortcut id)."""
        self._callbacks["shortcut_tags"] = callback

    def bind_visible_columns_changed(self, callback: Callable[[list[str]], None]) -> None:
        """Register the column-management callback (new visible order)."""
        self._callbacks["visible_columns_changed"] = callback

    def bind_column_nicknames_changed(self, callback: Callable[[dict[str, str]], None]) -> None:
        """Register the column-nickname edition callback ('Gestion des colonnes')."""
        self._callbacks["column_nicknames_changed"] = callback

    def bind_column_widths_changed(self, callback: Callable[[dict[str, int]], None]) -> None:
        """Register the user column-resize callback (debounced, persisted)."""
        self._header_state_var.bind_column_widths_changed(callback)

    def bind_sort_order_changed(self, callback: Callable[[str, bool], None]) -> None:
        """Register the user sort-order callback (column name, descending)."""
        self._header_state_var.bind_sort_order_changed(callback)

    def bind_row_delete_requested(self, callback: Callable[[int], None]) -> None:
        """Register the per-row 'X' delete callback (receives the doc row)."""
        self._callbacks["row_delete_requested"] = callback


# EOF
