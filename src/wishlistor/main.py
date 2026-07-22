"""Application entry point and composition root (AGENTS §9)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtGui import QColor, QIcon, QPainter, QPalette, QPen
from PySide6.QtWidgets import QApplication, QProxyStyle, QStyle, QStyleFactory, QStyleOption, QWidget

from wishlistor.models.app_config_model import AppConfigModel
from wishlistor.models.app_state_model import AppStateModel
from wishlistor.presenters.csv_presenter import CsvPresenter
from wishlistor.presenters.journal_presenter import JournalPresenter
from wishlistor.presenters.main_presenter import MainPresenter
from wishlistor.presenters.options_presenter import OptionsPresenter
from wishlistor.presenters.project_presenter import ProjectPresenter
from wishlistor.repositories.config_repository import ConfigRepository
from wishlistor.repositories.csv_repository import CsvRepository
from wishlistor.repositories.image_repository import ImageRepository
from wishlistor.services.csv_service import CsvService
from wishlistor.services.options_service import OptionsService
from wishlistor.services.project_service import ProjectService
from wishlistor.services.rank_service import RankService
from wishlistor.services.undo_service import UndoService
from wishlistor.shared import constants_util as const
from wishlistor.shared.enums.module_enum import ModuleEnum
from wishlistor.shared.path_util import make_all_folders_if_not_exists
from wishlistor.views.csv_view import CsvView
from wishlistor.views.journal_view import JournalView
from wishlistor.views.log_bridge_view import LogBridgeView
from wishlistor.views.main_window_view import MainWindowView
from wishlistor.views.options_view import OptionsView
from wishlistor.views.project_view import ProjectView
from wishlistor.views.task_runner_view import TaskRunnerView

_APP_ICON_PATH: str = "./ress/icon.png"
_LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(log_bridge: LogBridgeView) -> None:
    """Configure the rotating file logging and the journal bridge.

    Args:
        log_bridge: Handler feeding the Journal module.
    """
    make_all_folders_if_not_exists(const.C_LOG_FOLDER_PATH)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    file_handler = RotatingFileHandler(
        Path(const.C_LOG_FOLDER_PATH) / const.C_LOG_FILE_NAME,
        maxBytes=const.C_LOG_MAX_BYTES,
        backupCount=const.C_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(file_handler)
    log_bridge.setLevel(logging.DEBUG)
    root.addHandler(log_bridge)


class CheckBoxIndicatorStyle(QProxyStyle):
    """Proxy over the base style enlarging the QCheckBox indicator (no global QSS, see AGENTS UI note)."""

    def pixelMetric(  # noqa: N802 - Qt override
        self, metric: QStyle.PixelMetric, option: QStyleOption | None = None, widget: QWidget | None = None
    ) -> int:
        """Return the enlarged indicator size for checkboxes, delegate everything else."""
        if metric in {QStyle.PixelMetric.PM_IndicatorWidth, QStyle.PixelMetric.PM_IndicatorHeight}:
            return const.C_CHECKBOX_INDICATOR_SIZE_PX
        return super().pixelMetric(metric, option, widget)

    def drawPrimitive(  # noqa: N802 - Qt override
        self,
        element: QStyle.PrimitiveElement,
        option: QStyleOption,
        painter: QPainter,
        widget: QWidget | None = None,
    ) -> None:
        """Draw the QGroupBox frame with C_COLOR_BORDER.

        Fusion's Window.darker(130) is unreadable on this dark palette: Window is already
        near-black, so darkening it barely changes it.
        """
        if element == QStyle.PrimitiveElement.PE_FrameGroupBox:
            pen = QPen(QColor(const.C_COLOR_BORDER))
            pen.setCosmetic(True)
            painter.save()
            painter.setPen(pen)
            painter.drawRect(option.rect.adjusted(1, 1, -1, -1))
            painter.restore()
            return
        super().drawPrimitive(element, option, painter, widget)


def build_dark_palette() -> QPalette:
    """Build the dark Fusion palette from the specified colors (spec A.2)."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(const.C_COLOR_BACKGROUND_MAIN))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(const.C_COLOR_TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(const.C_COLOR_INPUT_BACKGROUND))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(const.C_COLOR_SURFACE))
    palette.setColor(QPalette.ColorRole.Text, QColor(const.C_COLOR_TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(const.C_COLOR_TEXT_SECONDARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(const.C_COLOR_SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(const.C_COLOR_TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(const.C_COLOR_SELECTION))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(const.C_COLOR_TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Link, QColor(const.C_COLOR_LINK))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(const.C_COLOR_SURFACE))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(const.C_COLOR_TEXT_PRIMARY))
    disabled = QPalette.ColorGroup.Disabled
    palette.setColor(disabled, QPalette.ColorRole.Text, QColor(const.C_COLOR_TEXT_DISABLED))
    palette.setColor(disabled, QPalette.ColorRole.WindowText, QColor(const.C_COLOR_TEXT_DISABLED))
    palette.setColor(disabled, QPalette.ColorRole.ButtonText, QColor(const.C_COLOR_TEXT_DISABLED))
    palette.setColor(disabled, QPalette.ColorRole.Button, QColor(const.C_COLOR_BUTTON_DISABLED))
    return palette


def main() -> int:  # foqa: EPI025, HAS111
    """Assemble every object exactly once and run the application."""
    application = QApplication(sys.argv)
    application.setStyle(CheckBoxIndicatorStyle(QStyleFactory.create("Fusion")))
    application.setPalette(build_dark_palette())
    application.setWindowIcon(QIcon(_APP_ICON_PATH))

    log_bridge = LogBridgeView()
    setup_logging(log_bridge)
    logger = logging.getLogger("main")
    logger.info("Démarrage de l'application Wishlistor.")

    # Repositories and shared state -------------------------------------------------
    config_repository = ConfigRepository()
    csv_repository = CsvRepository()
    image_repository = ImageRepository()
    config, config_issues = config_repository.load()
    AppConfigModel.set_instance(config)
    app_state = AppStateModel()

    # Services ------------------------------------------------------------------------
    undo_service = UndoService()
    rank_service = RankService()
    csv_service = CsvService(csv_repository, rank_service, undo_service)
    project_service = ProjectService(config_repository, csv_repository, config)
    options_service = OptionsService(config_repository, config)

    # Views ---------------------------------------------------------------------------
    main_window = MainWindowView()
    project_view = ProjectView(main_window)
    csv_view = CsvView(image_repository, main_window)
    journal_view = JournalView(main_window)
    options_view = OptionsView(main_window)
    task_runner = TaskRunnerView(main_window)
    main_window.add_panel(ModuleEnum.E_PROJECT, project_view)
    main_window.add_panel(ModuleEnum.E_CSV, csv_view)
    main_window.add_panel(ModuleEnum.E_JOURNAL, journal_view)
    main_window.add_panel(ModuleEnum.E_OPTIONS, options_view)

    # Cross-presenter callbacks (late-bound closures) -----------------------------------
    def open_project_in_csv(id_project: str) -> None:
        main_presenter.show_module(ModuleEnum.E_CSV)
        csv_presenter.open_project(id_project)

    def edit_project(id_project: str) -> None:
        main_presenter.show_module(ModuleEnum.E_PROJECT)
        project_presenter.open_edit_form(id_project)

    def project_updated(id_project: str) -> None:
        csv_presenter.refresh_project_settings(id_project)
        main_presenter.show_module(ModuleEnum.E_CSV)

    def row_height_preview(row_height: int) -> None:
        csv_presenter.preview_row_height(row_height)

    def edit_cancelled() -> None:
        main_presenter.show_module(ModuleEnum.E_CSV)

    def can_leave_csv() -> bool:
        return csv_presenter.can_close()

    def open_created_project(id_project: str) -> None:
        main_presenter.show_module(ModuleEnum.E_CSV)
        csv_presenter.open_project(id_project, check_unsaved=False)

    def factory_reset_applied() -> None:
        csv_presenter.handle_factory_reset()
        project_presenter.refresh_list()

    def can_close() -> bool:
        return csv_presenter.can_close()

    # Presenters --------------------------------------------------------------------------
    csv_presenter = CsvPresenter(
        csv_view, csv_service, project_service, task_runner, config, app_state, edit_project
    )
    project_presenter = ProjectPresenter(
        project_view,
        project_service,
        open_project_in_csv,
        project_updated,
        row_height_preview,
        edit_cancelled,
        can_leave_csv,
        open_created_project,
    )
    journal_presenter = JournalPresenter(journal_view, log_bridge)
    options_presenter = OptionsPresenter(options_view, options_service, main_window, factory_reset_applied)
    main_presenter = MainPresenter(main_window, options_service, config, app_state, can_close)

    journal_presenter.start()
    if config_issues.has_issues():
        logger.warning("Anomalies de configuration : %s", config_issues.concat_issues_by_severity())
    csv_presenter.start()
    project_presenter.start()
    options_presenter.start()
    main_presenter.start()

    main_window.show()
    exit_code = application.exec()

    # Teardown (AGENTS §9): disconnect the bridge, then drop references.
    logging.getLogger().removeHandler(log_bridge)
    logger.info("Fermeture de l'application (code %s).", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

# EOF
