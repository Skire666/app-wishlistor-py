# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import math

from wishlistor.models.options_model import OptionsModel
from wishlistor.shared.errors.config_error import ErrorCodeConfig


def test_default_options_are_valid() -> None:
    assert not OptionsModel().validate().has_issues()


def test_default_tag_weights_match_the_spec() -> None:
    expected = {
        "A faire": 0.40,
        "En cours": 0.80,
        "Terminé": -0.50,
        "Abandonné": -0.75,
        "Archivé": -1.00,
        "Ignoré": -1.00,
    }
    weights = OptionsModel().default_tag_weights
    for tag, value in expected.items():
        assert math.isclose(weights[tag], value)


def test_validate_rejects_undo_out_of_bounds() -> None:
    options = OptionsModel()
    options.undo_max = 31
    assert options.validate().count_severities_by_code(ErrorCodeConfig.CFG_1003) == 1
    options.undo_max = 0
    assert options.validate().count_severities_by_code(ErrorCodeConfig.CFG_1003) == 1


def test_validate_tolerates_malformed_special_column() -> None:
    # Décision propriétaire : plus de contrôle de format sur special_display_columns.
    options = OptionsModel()
    options.special_display_columns = ["pas_speciale"]
    assert options.validate().count_severities_by_code(ErrorCodeConfig.CFG_1006) == 0


def test_default_shortcut_tags_match_the_spec() -> None:
    options = OptionsModel()
    assert options.shortcut_ctrl_o_tags == ["A faire"]
    assert options.shortcut_ctrl_n_tags == ["Archivé"]
    assert options.shortcut_ctrl_t_tags == ["Terminé"]


def test_validate_rejects_unknown_shortcut_tag() -> None:
    options = OptionsModel()
    options.shortcut_ctrl_o_tags = ["Bidule"]
    options.shortcut_ctrl_n_tags = ["Machin"]
    options.shortcut_ctrl_t_tags = ["Truc"]
    result = options.validate()
    assert result.count_severities_by_code(ErrorCodeConfig.CFG_1007) == 1
    assert result.count_severities_by_code(ErrorCodeConfig.CFG_1008) == 1
    assert result.count_severities_by_code(ErrorCodeConfig.CFG_1009) == 1


def test_shortcut_tags_round_trip_through_serialization() -> None:
    options = OptionsModel()
    options.shortcut_ctrl_o_tags = ["En cours"]
    options.shortcut_ctrl_n_tags = ["Ignoré"]
    options.shortcut_ctrl_t_tags = ["Abandonné"]
    clone = OptionsModel.from_dict(options.to_dict())
    assert clone.shortcut_ctrl_o_tags == ["En cours"]
    assert clone.shortcut_ctrl_n_tags == ["Ignoré"]
    assert clone.shortcut_ctrl_t_tags == ["Abandonné"]


def test_from_dict_tolerates_garbage_and_falls_back_to_defaults() -> None:
    options = OptionsModel.from_dict(
        {"undo_max": "beaucoup", "default_tag_weights": {"A faire": "zéro", "Inconnu": 1.0}, "font_size": None}
    )
    assert options.undo_max == 10
    assert options.font_size == 12
    assert math.isclose(options.default_tag_weights["A faire"], 0.40)
    assert "Inconnu" not in options.default_tag_weights


# EOF
