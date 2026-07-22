"""Repository for `./config-wishlistor.json` (atomic writes, in-memory cache)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import json
import logging
from pathlib import Path

from wishlistor.models.app_config_model import AppConfigModel
from wishlistor.shared.constants_util import C_CONFIG_FILE_PATH
from wishlistor.shared.enums.severity_enum import SeverityEnum
from wishlistor.shared.errors.config_error import ErrorCodeConfig
from wishlistor.shared.exceptions.file_access_error import FileAccessError
from wishlistor.shared.typing.json_util import as_str_object_dict
from wishlistor.shared.validation_result import ValidationResult

_ENCODING: str = "utf-8"


class ConfigRepository:
    """Reads and writes the application configuration file."""

    def __init__(self, config_path: str = C_CONFIG_FILE_PATH) -> None:
        """Initialize the repository.

        Args:
            config_path: Path of the configuration JSON file.
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config_path = Path(config_path)
        self._cache: AppConfigModel | None = None

    def load(self) -> tuple[AppConfigModel, ValidationResult]:
        """Load the configuration, falling back to defaults when corrupt.

        Returns:
            The configuration and the issues met while reading it.
        """
        result = ValidationResult()
        if self._cache is not None:
            return self._cache, result
        raw = self._read_raw(result)
        config = AppConfigModel.get_default() if raw is None else AppConfigModel.from_dict(raw)
        self._cache = config
        return config, result

    def _read_raw(self, result: ValidationResult) -> dict[str, object] | None:
        """Read and parse the JSON file, reporting corruption as a warning."""
        if not self._config_path.is_file():
            self._logger.debug("Fichier de configuration absent : %s", self._config_path)
            return None
        try:
            payload: object = json.loads(self._config_path.read_text(encoding=_ENCODING))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as excp:
            self._logger.warning("Configuration corrompue (%s) : valeurs par défaut restaurées.", excp)
            result.append(ErrorCodeConfig.CFG_1001, SeverityEnum.E_WARNING)
            return None
        typed = as_str_object_dict(payload)
        if typed is None:
            self._logger.warning("Configuration invalide (racine non-objet) : valeurs par défaut.")
            result.append(ErrorCodeConfig.CFG_1001, SeverityEnum.E_WARNING)
        return typed

    def save(self, config: AppConfigModel) -> ValidationResult:
        """Persist the configuration atomically (temp file + replace).

        Args:
            config: The configuration to write.

        Returns:
            The issues met while writing (empty on success).
        """
        result = ValidationResult()
        payload = json.dumps(config.to_dict(), indent=2, ensure_ascii=False)
        temp_path = self._config_path.with_suffix(".json.tmp")
        try:
            temp_path.write_text(payload, encoding=_ENCODING)
            Path(temp_path).replace(self._config_path)
        except OSError as excp:
            self._logger.exception("Échec d'écriture de la configuration.")
            result.append(ErrorCodeConfig.CFG_1002, SeverityEnum.E_ERROR, {"path": str(self._config_path)})
            raise FileAccessError(str(self._config_path), str(excp)) from excp
        self._cache = config
        self._logger.debug("Configuration écrite : %s", self._config_path)
        return result

    def invalidate_cache(self) -> None:
        """Drop the in-memory cache so the next load re-reads the file."""
        self._cache = None


# EOF
