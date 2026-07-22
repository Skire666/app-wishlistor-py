# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from wishlistor.interfaces.i_base_view import IBaseView
from wishlistor.models.view_state_model import WindowGeometryState
from wishlistor.shared.enums.module_enum import ModuleEnum


class IMainWindowView(IBaseView, Protocol):
    """Main window shell: sidebar, module container, geometry, close handling."""

    def snapshot(self) -> WindowGeometryState:
        """Return the current window geometry."""
        ...

    def bind_module_selected(self, callback: Callable[[ModuleEnum], None]) -> None:
        """Register the sidebar navigation callback.

        Args:
            callback: Called with the clicked module.
        """
        ...

    def bind_close_requested(self, callback: Callable[[], bool]) -> None:
        """Register the close interceptor.

        Args:
            callback: Called on closeEvent; returning False cancels the close.
        """
        ...

    def set_active_module(self, module: ModuleEnum) -> None:
        """Show the panel of *module* and highlight its sidebar button.

        Args:
            module: The module to activate.
        """
        ...

    def restore_geometry(self, geometry: WindowGeometryState) -> None:
        """Apply a persisted window geometry.

        Args:
            geometry: Size and position to restore.
        """
        ...

    def apply_font_size(self, size: int) -> None:
        """Apply the application font size in real time.

        Args:
            size: Font size in points.
        """
        ...


# EOF
