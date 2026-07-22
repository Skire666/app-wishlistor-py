"""Shell presenter: sidebar navigation, geometry persistence, close guard."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from wishlistor.interfaces.i_main_window_view import IMainWindowView
from wishlistor.interfaces.i_options_service import IOptionsService
from wishlistor.models.app_config_model import AppConfigModel
from wishlistor.models.app_state_model import AppStateModel
from wishlistor.shared.enums.module_enum import ModuleEnum


class MainPresenter:
    """Wires the main window shell: navigation, close event, geometry."""

    def __init__(
        self,
        view: IMainWindowView,
        options_service: IOptionsService,
        config: AppConfigModel,
        app_state: AppStateModel,
        can_close: Callable[[], bool],
    ) -> None:
        """Initialize the presenter.

        Args:
            view: The main window view.
            options_service: Persistence of the window geometry.
            config: The shared configuration model.
            app_state: The global application state.
            can_close: Guard returning False to keep the window open (spec F).
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._view = view
        self._options_service = options_service
        self._config = config
        self._app_state = app_state
        self._can_close = can_close

    def start(self) -> None:
        """Restore the geometry, bind navigation, show the default module."""
        self._view.bind_module_selected(self.show_module)
        self._view.bind_close_requested(self._handle_close_requested)
        self._view.restore_geometry(self._config.window)
        self._view.apply_font_size(self._config.options.font_size)
        self.show_module(ModuleEnum.E_PROJECT)

    def show_module(self, module: ModuleEnum) -> None:
        """Activate a module panel.

        Args:
            module: The module to show.
        """
        started = time.perf_counter()
        self._app_state.active_module = module
        self._view.set_active_module(module)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._logger.info("Action 'ouvrir le module %s' terminée en %s ms", module.value, elapsed_ms)

    def _handle_close_requested(self) -> bool:
        """Protect unsaved data, then persist the window geometry."""
        try:
            if not self._can_close():
                return False
            self._options_service.save_window_geometry(self._view.snapshot())
        except Exception:
            self._logger.exception("Erreur lors de la fermeture de l'application.")
        return True


# EOF
