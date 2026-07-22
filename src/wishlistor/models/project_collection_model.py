"""Collection of projects with recency ordering (config `projects` section)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Iterator
from typing import Self

from wishlistor.models.project_model import ProjectModel
from wishlistor.shared.enums.copy_mode_enum import CopyModeEnum
from wishlistor.shared.typing.datetime_util import get_datetime_now_yyyy_mm_dd_hh_mm_ss
from wishlistor.shared.typing.json_util import as_str_list, as_str_object_dict
from wishlistor.shared.validation_result import ValidationResult


class ProjectCollectionModel:
    """CRUD container for ProjectModel instances, ordered by recency."""

    def __init__(self) -> None:
        """Initialize an empty collection."""
        self._id_collection: str = "projects"
        self._projects: dict[str, ProjectModel] = {}
        self._recent_ids: list[str] = []
        self._created_at: str = ""
        self._modified_at: str = ""

    # -- container protocol ------------------------------------------------------

    def __iter__(self) -> Iterator[ProjectModel]:
        """Iterate over the projects, most recently opened first."""
        return iter([self._projects[key] for key in self.ordered_ids()])

    def __len__(self) -> int:
        """Return the number of projects."""
        return len(self._projects)

    def __getitem__(self, id_project: str) -> ProjectModel:
        """Return the project with the given identifier.

        Args:
            id_project: The project identifier.

        Returns:
            The matching project.
        """
        return self._projects[id_project]

    # -- properties ---------------------------------------------------------------

    @property
    def id_collection(self) -> str:
        """Unique identifier of the collection."""
        return self._id_collection

    @property
    def projects(self) -> dict[str, ProjectModel]:
        """Underlying projects, keyed by identifier."""
        return self._projects

    @property
    def recent_ids(self) -> list[str]:
        """Identifiers ordered from most to least recently opened."""
        return self._recent_ids

    @recent_ids.setter
    def recent_ids(self, value: list[str]) -> None:
        """Set the recency ordering."""
        self._recent_ids = list(value)

    # -- CRUD ----------------------------------------------------------------------

    def create(self, project: ProjectModel) -> None:
        """Add a project and promote it to the top of the recency list.

        Args:
            project: The project to add (its id must be set).
        """
        self._projects[project.id_project] = project
        self.touch(project.id_project)

    def read(self, id_project: str) -> ProjectModel | None:
        """Return the project with the given id, or None.

        Args:
            id_project: The project identifier.

        Returns:
            The matching project, or None when absent.
        """
        return self._projects.get(id_project)

    def update(self, project: ProjectModel) -> None:
        """Replace an existing project (same id) with the given instance.

        Args:
            project: The updated project.
        """
        self._projects[project.id_project] = project
        self.mark_as_modified()

    def delete(self, id_project: str) -> None:
        """Remove a project from the collection and the recency list.

        Args:
            id_project: The project identifier.
        """
        self._projects.pop(id_project, None)
        self._recent_ids = [key for key in self._recent_ids if key != id_project]
        self.mark_as_modified()

    def touch(self, id_project: str) -> None:
        """Move a project to the top of the recency list and stamp it.

        Args:
            id_project: The project identifier.
        """
        self._recent_ids = [id_project, *[key for key in self._recent_ids if key != id_project]]
        project = self._projects.get(id_project)
        if project is not None:
            project.last_opened = get_datetime_now_yyyy_mm_dd_hh_mm_ss()
        self.mark_as_modified()

    def ordered_ids(self) -> list[str]:
        """Return every project id, recency first, then unlisted ones."""
        known = [key for key in self._recent_ids if key in self._projects]
        rest = [key for key in self._projects if key not in known]
        return [*known, *rest]

    def search(self, text: str) -> list[ProjectModel]:
        """Return the projects whose name or path contains *text* (case-insensitive).

        Args:
            text: Substring to look for.

        Returns:
            The matching projects, recency first.
        """
        needle = text.lower()
        return [p for p in self if needle in p.name.lower() or needle in p.csv_path.lower()]

    def delete_many(self, ids: list[str]) -> None:
        """Batch removal of several projects.

        Args:
            ids: Identifiers of the projects to remove.
        """
        for id_project in ids:
            self.delete(id_project)

    # -- contract methods ------------------------------------------------------------

    @property
    def fieldnames(self) -> list[str]:
        """All serialized attribute names."""
        return ["projects", "recent_projects"]

    def validate(self, context: object | None = None) -> ValidationResult:
        """Validate every project in the collection.

        Args:
            context: Forwarded to each project's validate().

        Returns:
            The accumulated validation issues.
        """
        result = ValidationResult()
        for project in self._projects.values():
            result.extend(project.validate(context))
        return result

    def serialize(self) -> dict[str, object]:
        """Serialize the collection to JSON-compatible dictionaries."""
        return {
            "projects": {key: project.to_dict() for key, project in self._projects.items()},
            "recent_projects": [key for key in self._recent_ids if key in self._projects],
        }

    @classmethod
    def deserialize(cls, data: dict[str, object]) -> Self:
        """Build a collection from raw JSON data, skipping malformed entries.

        Args:
            data: Raw dictionary read from the configuration file.

        Returns:
            The rebuilt collection.
        """
        instance = cls()
        raw_projects = as_str_object_dict(data.get("projects"))
        if raw_projects is not None:
            for key, value in raw_projects.items():
                typed = as_str_object_dict(value)
                if typed is not None:
                    project = ProjectModel.from_dict(typed)
                    project.id_project = key
                    instance.projects[key] = project
        instance.recent_ids = as_str_list(data.get("recent_projects"))
        return instance

    @classmethod
    def get_default(cls) -> Self:
        """Return a fully initialized empty collection."""
        instance = cls()
        instance.mark_as_created()
        return instance

    def mark_as_created(self) -> None:
        """Stamp the creation and modification timestamps."""
        self._created_at = get_datetime_now_yyyy_mm_dd_hh_mm_ss()
        self._modified_at = self._created_at

    def mark_as_modified(self) -> None:
        """Stamp the modification timestamp."""
        self._modified_at = get_datetime_now_yyyy_mm_dd_hh_mm_ss()

    def copy(self, mode: CopyModeEnum) -> Self:
        """Duplicate the collection (projects are copied with the same mode).

        Args:
            mode: Copy semantics forwarded to each project.

        Returns:
            The duplicated collection.
        """
        clone = type(self)()
        for key, project in self._projects.items():
            copied = project.copy(mode)
            clone.projects[copied.id_project or key] = copied
        clone.recent_ids = list(self._recent_ids)
        return clone

    def clear(self) -> None:
        """Remove every project and reset the recency list."""
        self._projects.clear()
        self._recent_ids.clear()
        self.mark_as_modified()


# EOF
