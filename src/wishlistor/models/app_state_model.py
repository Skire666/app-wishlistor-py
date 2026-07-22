"""Global application lifecycle state (AGENTS.md §10)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from wishlistor.shared.enums.module_enum import ModuleEnum


class AppStateModel:
    """Aggregates per-view busy/loading/dirty flags into global flags.

    A view flag going True propagates to the global flag; the global flag
    returns to False only when no view holds it anymore.
    """

    def __init__(self) -> None:
        """Initialize the state with no active view and all flags off."""
        self._active_module: ModuleEnum = ModuleEnum.E_UNSET
        self._busy_owners: set[str] = set()
        self._loading_owners: set[str] = set()
        self._dirty_owners: set[str] = set()

    @property
    def active_module(self) -> ModuleEnum:
        """Module currently shown in the main content area."""
        return self._active_module

    @active_module.setter
    def active_module(self, value: ModuleEnum) -> None:
        """Set the module currently shown."""
        self._active_module = value

    @property
    def is_busy(self) -> bool:
        """True while at least one view runs a background operation."""
        return bool(self._busy_owners)

    @property
    def is_loading(self) -> bool:
        """True while at least one view is building or loading itself."""
        return bool(self._loading_owners)

    @property
    def is_dirty(self) -> bool:
        """True while at least one view holds unsaved user changes."""
        return bool(self._dirty_owners)

    def set_busy(self, owner: str, value: bool) -> None:
        """Propagate a per-view busy flag.

        Args:
            owner: Name of the view owning the flag.
            value: The new flag value for that view.
        """
        self._toggle(self._busy_owners, owner, value)

    def set_loading(self, owner: str, value: bool) -> None:
        """Propagate a per-view loading flag.

        Args:
            owner: Name of the view owning the flag.
            value: The new flag value for that view.
        """
        self._toggle(self._loading_owners, owner, value)

    def set_dirty(self, owner: str, value: bool) -> None:
        """Propagate a per-view dirty flag.

        Args:
            owner: Name of the view owning the flag.
            value: The new flag value for that view.
        """
        self._toggle(self._dirty_owners, owner, value)

    @staticmethod
    def _toggle(owners: set[str], owner: str, value: bool) -> None:
        """Add or remove *owner* from the flag owner set."""
        if value:
            owners.add(owner)
        else:
            owners.discard(owner)


# EOF
