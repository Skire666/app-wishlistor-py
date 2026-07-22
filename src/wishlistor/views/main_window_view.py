"""Main window: vertical sidebar (4 modules) and the content area (spec A.1)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from wishlistor.models.view_state_model import WindowGeometryState
from wishlistor.shared.constants_util import (
    C_ICON_PLACEHOLDER_PATH,
    C_ICON_SIZE_PX,
    C_WINDOW_MIN_HEIGHT,
    C_WINDOW_MIN_WIDTH,
)
from wishlistor.shared.enums.module_enum import ModuleEnum
from wishlistor.shared.i18n_fra import APP_TITLE, SIDEBAR_CSV, SIDEBAR_JOURNAL, SIDEBAR_OPTIONS, SIDEBAR_PROJECT
from wishlistor.shared.validation_result import ValidationResult

_SIDEBAR_WIDTH_PX: int = 96

_MODULE_LABELS: dict[ModuleEnum, str] = {
    ModuleEnum.E_PROJECT: SIDEBAR_PROJECT,
    ModuleEnum.E_CSV: SIDEBAR_CSV,
    ModuleEnum.E_JOURNAL: SIDEBAR_JOURNAL,
    ModuleEnum.E_OPTIONS: SIDEBAR_OPTIONS,
}


class MainWindowView(QMainWindow):
    """Application shell: sidebar navigation and stacked module panels."""

    def __init__(self) -> None:
        """Initialize the window skeleton."""
        super().__init__()
        self.setObjectName("main_window")
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(C_WINDOW_MIN_WIDTH, C_WINDOW_MIN_HEIGHT)
        self.is_dirty: bool = False
        self.is_busy: bool = False
        self.is_loading: bool = True
        self._on_module_selected: Callable[[ModuleEnum], None] | None = None
        self._on_close_requested: Callable[[], bool] | None = None
        self._buttons_var: dict[ModuleEnum, QToolButton] = {}
        self._panels_var: dict[ModuleEnum, int] = {}
        self._stack_var = QStackedWidget(self)
        self._build_skeleton()
        self.is_loading = False

    def _build_skeleton(self) -> None:
        """Assemble the sidebar and the content stack."""
        central = QWidget(self)
        central.setObjectName("central_widget")
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar(central), 0)
        layout.addWidget(self._stack_var, 1)
        self.setCentralWidget(central)

    def _build_sidebar(self, parent: QWidget) -> QWidget:
        """Build the vertical sidebar with one button per module."""
        sidebar = QFrame(parent)
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(_SIDEBAR_WIDTH_PX)
        sidebar.setAutoFillBackground(True)
        layout = QVBoxLayout(sidebar)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        icon = QIcon(C_ICON_PLACEHOLDER_PATH)  # placeholder, swap the path for final icons
        for module, label in _MODULE_LABELS.items():
            button = self._build_module_button(sidebar, module, label, icon)
            self._buttons_var[module] = button
            layout.addWidget(button)
        return sidebar

    def _build_module_button(self, parent: QWidget, module: ModuleEnum, label: str, icon: QIcon) -> QToolButton:
        """Build one checkable sidebar button."""
        button = QToolButton(parent)
        button.setObjectName(f"sidebar_button_{module.value.lower()}")
        button.setText(label)
        button.setIcon(icon)
        button.setIconSize(QSize(C_ICON_SIZE_PX, C_ICON_SIZE_PX))
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setCheckable(True)
        button.setAutoExclusive(True)
        button.setMinimumWidth(_SIDEBAR_WIDTH_PX - 16)
        button.clicked.connect(lambda _checked=False, m=module: self._emit_module(m))
        return button

    def _emit_module(self, module: ModuleEnum) -> None:
        """Forward a sidebar click to the presenter."""
        if self._on_module_selected is not None:
            self._on_module_selected(module)

    # -- presenter API ------------------------------------------------------------

    def add_panel(self, module: ModuleEnum, panel: QWidget) -> None:
        """Register a module panel in the content stack.

        Args:
            module: The module owning the panel.
            panel: The panel widget.
        """
        self._panels_var[module] = self._stack_var.addWidget(panel)

    def set_active_module(self, module: ModuleEnum) -> None:
        """Show the panel of *module* and check its sidebar button.

        Args:
            module: The module to activate.
        """
        index = self._panels_var.get(module)
        if index is not None:
            self._stack_var.setCurrentIndex(index)
        button = self._buttons_var.get(module)
        if button is not None:
            button.setChecked(True)

    def bind_module_selected(self, callback: Callable[[ModuleEnum], None]) -> None:
        """Register the sidebar navigation callback.

        Args:
            callback: Called with the clicked module.
        """
        self._on_module_selected = callback

    def bind_close_requested(self, callback: Callable[[], bool]) -> None:
        """Register the close interceptor.

        Args:
            callback: Called on closeEvent; returning False cancels the close.
        """
        self._on_close_requested = callback

    def restore_geometry(self, geometry: WindowGeometryState) -> None:
        """Apply a persisted window geometry.

        Args:
            geometry: Size and position to restore.
        """
        self.resize(max(C_WINDOW_MIN_WIDTH, geometry.width), max(C_WINDOW_MIN_HEIGHT, geometry.height))
        self.move(geometry.x, geometry.y)
        if geometry.is_maximized:
            self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)

    def apply_font_size(self, size: int) -> None:
        """Apply the application font size in real time.

        Args:
            size: Font size in points.
        """
        application = QApplication.instance()
        if isinstance(application, QApplication):
            font = application.font()
            font.setPointSize(size)
            application.setFont(font)

    def snapshot(self) -> WindowGeometryState:
        """Return the window geometry (normal frame plus the maximized flag)."""
        frame = self.normalGeometry()  # restore-size even while maximized
        return WindowGeometryState(
            width=frame.width(), height=frame.height(), x=frame.x(), y=frame.y(), is_maximized=self.isMaximized()
        )

    # -- base view contract ----------------------------------------------------------

    def set_enabled(self, enabled: bool) -> None:
        """Grey out or re-enable the whole window content.

        Args:
            enabled: The new enabled state.
        """
        self.centralWidget().setEnabled(enabled)

    def notify_error(self, rs: ValidationResult) -> None:
        """Show a blocking error popup (critical failures only).

        Args:
            rs: The issues to display.
        """
        QMessageBox.critical(self, APP_TITLE, rs.concat_issues_by_severity())

    def clear(self) -> None:
        """Reset the shell (nothing user-editable lives here)."""
        self.is_dirty = False

    def notify_refresh(self, context: object) -> None:
        """Refresh the shell according to *context* (unused).

        Args:
            context: Presenter-defined refresh payload.
        """
        _ = context

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt override
        """Intercept the window close to protect unsaved modifications."""
        if self._on_close_requested is not None and not self._on_close_requested():
            event.ignore()
            return
        event.accept()


# EOF
