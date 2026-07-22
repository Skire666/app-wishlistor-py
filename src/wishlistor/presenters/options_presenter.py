"""Options presenter: validated auto-save, factory reset, live font size (B.6)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from wishlistor.interfaces.i_main_window_view import IMainWindowView
from wishlistor.interfaces.i_options_service import IOptionsService
from wishlistor.interfaces.i_options_view import IOptionsView
from wishlistor.shared.i18n_fra import OPTIONS_FACTORY_RESET_MESSAGE, OPTIONS_FACTORY_RESET_TITLE


class OptionsPresenter:
    """Wires the options view to the options service."""

    def __init__(
        self,
        view: IOptionsView,
        options_service: IOptionsService,
        main_window: IMainWindowView,
        on_factory_reset: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the presenter.

        Args:
            view: The options view.
            options_service: The options business logic.
            main_window: The shell view (live font size application).
            on_factory_reset: Called after a factory reset so other modules refresh.
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._view = view
        self._options_service = options_service
        self._main_window = main_window
        self._on_factory_reset = on_factory_reset

    def start(self) -> None:
        """Bind the view callbacks and populate the form."""
        self._view.bind_options_edited(self._handle_edited)
        self._view.bind_factory_reset_clicked(self._handle_factory_reset)
        self._refresh_view()

    def _refresh_view(self) -> None:
        """Repopulate the form from the current options."""
        self._view.show_state(self._options_service.current_state(), self._options_service.last_saved_label())

    def _handle_edited(self) -> None:
        """Validate and auto-save the options after each edit."""
        started = time.perf_counter()
        try:
            state = self._view.snapshot()
            result, field_errors = self._options_service.update(state)
            self._view.show_field_errors(field_errors)
            if not result.has_errors_or_fatals():
                self._view.set_last_save_label(self._options_service.last_saved_label())
                self._main_window.apply_font_size(state.font_size)
        except Exception:
            self._logger.exception("Échec de la sauvegarde des options.")
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._logger.info("Action 'sauvegarder les options' terminée en %s ms", elapsed_ms)

    def _handle_factory_reset(self) -> None:
        """Reset the whole configuration after a modal confirmation."""
        started = time.perf_counter()
        if not self._view.confirm(OPTIONS_FACTORY_RESET_TITLE, OPTIONS_FACTORY_RESET_MESSAGE):
            return
        try:
            self._options_service.factory_reset()
            self._refresh_view()
            self._main_window.apply_font_size(self._options_service.current_state().font_size)
            if self._on_factory_reset is not None:
                self._on_factory_reset()
        except Exception:
            self._logger.exception("Échec de la remise aux réglages d'usine.")
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._logger.info("Action 'réglages d'usine' terminée en %s ms", elapsed_ms)


# EOF
