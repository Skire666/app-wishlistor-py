# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path

from wishlistor.models.app_config_model import AppConfigModel
from wishlistor.models.project_model import ProjectModel
from wishlistor.repositories.config_repository import ConfigRepository
from wishlistor.shared.errors.config_error import ErrorCodeConfig


def test_save_then_load_round_trip(tmp_path: Path) -> None:
    config_path = tmp_path / "config-wishlistor.json"
    repository = ConfigRepository(str(config_path))
    config = AppConfigModel.get_default()
    project = ProjectModel.get_default()
    project.id_project = "p1"
    project.name = "Projet"
    config.projects.create(project)
    repository.save(config)
    repository.invalidate_cache()
    loaded, result = repository.load()
    assert not result.has_issues()
    assert loaded.projects.read("p1") is not None
    assert loaded.projects.read("p1").name == "Projet"


def test_project_sort_order_round_trip(tmp_path: Path) -> None:
    config_path = tmp_path / "config-wishlistor.json"
    repository = ConfigRepository(str(config_path))
    config = AppConfigModel.get_default()
    project = ProjectModel.get_default()
    project.id_project = "p1"
    project.name = "Projet"
    project.sort_column = "popularite"
    project.sort_descending = True
    config.projects.create(project)
    repository.save(config)
    repository.invalidate_cache()
    loaded, result = repository.load()
    assert not result.has_issues()
    reloaded = loaded.projects.read("p1")
    assert reloaded is not None
    assert reloaded.sort_column == "popularite"
    assert reloaded.sort_descending is True


def test_project_table_column_widths_round_trip(tmp_path: Path) -> None:
    config_path = tmp_path / "config-wishlistor.json"
    repository = ConfigRepository(str(config_path))
    config = AppConfigModel.get_default()
    config.project_table_column_widths = {"name": 240, "website": 120}
    repository.save(config)
    repository.invalidate_cache()
    loaded, result = repository.load()
    assert not result.has_issues()
    assert loaded.project_table_column_widths == {"name": 240, "website": 120}


def test_missing_file_returns_defaults_without_warning(tmp_path: Path) -> None:
    repository = ConfigRepository(str(tmp_path / "absent.json"))
    config, result = repository.load()
    assert config.options.undo_max == 10
    assert not result.has_issues()


def test_corrupted_file_returns_defaults_with_warning(tmp_path: Path) -> None:
    config_path = tmp_path / "config-wishlistor.json"
    config_path.write_text("{ pas du json", encoding="utf-8")
    repository = ConfigRepository(str(config_path))
    config, result = repository.load()
    assert config.options.undo_max == 10
    assert result.count_severities_by_code(ErrorCodeConfig.CFG_1001) == 1


def test_load_uses_the_cache_until_invalidated(tmp_path: Path) -> None:
    config_path = tmp_path / "config-wishlistor.json"
    repository = ConfigRepository(str(config_path))
    config = AppConfigModel.get_default()
    repository.save(config)
    first, _result = repository.load()
    second, _result = repository.load()
    assert first is second


def test_atomic_write_leaves_no_temp_file(tmp_path: Path) -> None:
    config_path = tmp_path / "config-wishlistor.json"
    repository = ConfigRepository(str(config_path))
    repository.save(AppConfigModel.get_default())
    leftovers = [p.name for p in tmp_path.iterdir() if p.suffix == ".tmp"]
    assert leftovers == []
    assert config_path.is_file()


# EOF
