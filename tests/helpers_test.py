"""Shared helpers for the test suite (real files only under tmp_path)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path

from wishlistor.models.project_model import ProjectModel
from wishlistor.repositories.csv_repository import CsvRepository
from wishlistor.services.csv_service import CsvService
from wishlistor.services.rank_service import RankService
from wishlistor.services.undo_service import UndoService
from wishlistor.shared.constants_util import C_COL_CUSTOM_COMMENTS, C_COL_CUSTOM_TAGS


def write_csv(path: Path, lines: list[str]) -> None:
    """Write raw CSV lines (';' delimiter) as UTF-8 without BOM."""
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_project(csv_path: Path) -> ProjectModel:
    """Build a minimal valid project mapping the standard test columns."""
    project = ProjectModel()
    project.id_project = "test-project"
    project.name = "Test"
    project.website = "example.org"
    project.category = "test"
    project.csv_path = str(csv_path)
    project.primary_column = "__primary_key__"
    project.released_column = "rel"
    project.popularity_column = "pop"
    project.scoring_column = "score"
    project.search_index_columns = ["__primary_key__", C_COL_CUSTOM_TAGS, C_COL_CUSTOM_COMMENTS]
    project.visible_columns = ["__primary_key__", C_COL_CUSTOM_TAGS, C_COL_CUSTOM_COMMENTS]
    project.column_order = list(project.visible_columns)
    return project


def make_csv_service() -> CsvService:
    """Assemble a CsvService with real collaborators."""
    return CsvService(CsvRepository(), RankService(), UndoService())


# EOF
