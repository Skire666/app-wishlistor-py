# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from wishlistor.models.project_model import ProjectModel
from wishlistor.shared.errors.project_error import ErrorCodeProject


def _valid_project() -> ProjectModel:
    project = ProjectModel()
    project.csv_path = "d:/quelque-part/data.csv"
    project.name = "Nom"
    project.website = "site"
    project.category = "cat"
    project.primary_column = "__primary_key__"
    project.released_column = "rel"
    project.popularity_column = "pop"
    project.scoring_column = "score"
    project.search_index_columns = ["__custom_tags__"]
    project.visible_columns = ["a", "b", "c"]
    project.column_default_values = [("a", "count_zero")]
    return project


def test_valid_project_has_no_issue() -> None:
    assert not _valid_project().validate().has_issues()


def test_validate_returns_error_when_name_is_empty() -> None:
    project = _valid_project()
    project.name = ""
    result = project.validate()
    assert result.count_severities_by_code(ErrorCodeProject.PRJ_1002) == 1


def test_validate_returns_error_when_name_is_too_long() -> None:
    project = _valid_project()
    project.name = "x" * 65
    assert project.validate().count_severities_by_code(ErrorCodeProject.PRJ_1002) == 1


def test_validate_returns_error_when_row_height_is_out_of_bounds() -> None:
    project = _valid_project()
    project.row_height = 300
    assert project.validate().count_severities_by_code(ErrorCodeProject.PRJ_1005) == 1


def test_validate_requires_at_least_one_indexed_column() -> None:
    project = _valid_project()
    project.search_index_columns = []
    assert project.validate().count_severities_by_code(ErrorCodeProject.PRJ_1007) == 1


def test_validate_requires_at_least_three_visible_columns() -> None:
    project = _valid_project()
    project.visible_columns = ["a", "b"]
    assert project.validate().count_severities_by_code(ErrorCodeProject.PRJ_1008) == 1


def test_validate_requires_the_three_rank_source_columns() -> None:
    project = _valid_project()
    project.released_column = ""
    project.popularity_column = " "
    project.scoring_column = ""
    result = project.validate()
    assert result.count_severities_by_code(ErrorCodeProject.PRJ_1011) == 1
    assert result.count_severities_by_code(ErrorCodeProject.PRJ_1012) == 1
    assert result.count_severities_by_code(ErrorCodeProject.PRJ_1013) == 1


def test_validate_rejects_out_of_bounds_tag_weight() -> None:
    project = _valid_project()
    project.tag_weights = {"Favoris": 2.0}
    assert project.validate().count_severities_by_code(ErrorCodeProject.PRJ_1009) == 1


def test_from_dict_round_trip_preserves_the_mapping() -> None:
    project = _valid_project()
    project.released_column = "rel"
    clone = ProjectModel.from_dict(project.to_dict())
    assert clone.released_column == "rel"
    assert clone.primary_column == "__primary_key__"
    assert clone.visible_columns == ["a", "b", "c"]


def test_validate_accepts_an_empty_column_default_values_table_with_a_warning() -> None:
    project = _valid_project()
    project.column_default_values = []
    result = project.validate()
    assert not result.has_errors_or_fatals()
    assert result.count_severities_by_code(ErrorCodeProject.PRJ_1016) == 1


def test_validate_rejects_a_duplicate_column_in_default_values() -> None:
    project = _valid_project()
    project.column_default_values = [("a", "count_zero"), ("a", "date_1900")]
    result = project.validate()
    assert result.count_severities_by_code(ErrorCodeProject.PRJ_1014) == 1
    assert result.has_errors_or_fatals()


def test_validate_rejects_an_incomplete_default_value_row() -> None:
    project = _valid_project()
    project.column_default_values = [("a", "")]
    result = project.validate()
    assert result.count_severities_by_code(ErrorCodeProject.PRJ_1015) == 1
    assert result.has_errors_or_fatals()


def test_from_dict_round_trip_preserves_column_default_values() -> None:
    project = _valid_project()
    project.column_default_values = [("a", "count_zero"), ("b", "date_today")]
    clone = ProjectModel.from_dict(project.to_dict())
    assert clone.column_default_values == [("a", "count_zero"), ("b", "date_today")]


def test_from_dict_round_trip_preserves_sort_order() -> None:
    project = _valid_project()
    project.sort_column = "b"
    project.sort_descending = True
    clone = ProjectModel.from_dict(project.to_dict())
    assert clone.sort_column == "b"
    assert clone.sort_descending is True


def test_new_project_has_no_sort_order() -> None:
    project = _valid_project()
    assert project.sort_column == ""
    assert project.sort_descending is False


# EOF
