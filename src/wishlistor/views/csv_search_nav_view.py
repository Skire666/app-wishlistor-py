"""Search navigation of the CSV module (spec B.4.2): counter and wrap-around."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from PySide6.QtWidgets import QAbstractItemView, QTableView

from wishlistor.shared import i18n_fra
from wishlistor.views.csv_filter_bar_view import CsvFilterBarView
from wishlistor.views.csv_table_model_view import CsvTableModelView


class CsvSearchNavView:
    """Keeps the ordered match positions and drives the counter label."""

    def __init__(self, table: QTableView, model: CsvTableModelView, filter_bar: CsvFilterBarView) -> None:
        """Initialize the controller.

        Args:
            table: The CSV table view (focus and scrolling).
            model: Its adapter model (match positions).
            filter_bar: The bar owning the search field and its counter.
        """
        self._table = table
        self._model = model
        self._filter_bar = filter_bar
        self._positions: list[int] = []
        self._index: int = -1

    def reset(self) -> None:
        """Recompute the matches after a text or filter change."""
        text = self._filter_bar.search_text()
        self._positions = self._model.search_positions(text)
        self._index = -1
        if not text:
            self._filter_bar.set_search_counter("")
        elif not self._positions:
            self._filter_bar.set_search_counter(i18n_fra.CSV_SEARCH_NO_RESULT)
        else:
            counter = i18n_fra.CSV_SEARCH_COUNTER.format(index=0, total=len(self._positions))
            self._filter_bar.set_search_counter(counter)

    def navigate(self, delta: int) -> None:
        """Move to the next/previous match, wrapping around (spec B.4.2).

        Args:
            delta: +1 for next, -1 for previous.
        """
        if not self._positions:
            self.reset()
        if not self._positions:
            return
        self._index = (self._index + delta) % len(self._positions)
        index = self._model.index(self._positions[self._index], 1)
        self._table.setCurrentIndex(index)
        self._table.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)
        counter = i18n_fra.CSV_SEARCH_COUNTER.format(index=self._index + 1, total=len(self._positions))
        self._filter_bar.set_search_counter(counter)


# EOF
