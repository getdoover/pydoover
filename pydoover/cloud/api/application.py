import base64
import json
import logging
import shutil
from pathlib import Path
from typing import Any

from .object import Object

log = logging.getLogger(__name__)


class Type:
    device = "DEV"
    processor = "PRO"
    task = "TAS"
    integration = "INT"


class Visibility:
    core = "COR"
    public = "PUB"
    private = "PRI"
    internal = "INT"


class Application:
    """Represents the application configuration for a Doover application.

    This generally resides in the `doover_config.json` file in the application directory.

    Attributes:
    """

    def __init__(
        self,
        key: str,
        name: str,
        display_name: str,
        app_type: Type,
        visibility: Visibility,
        allow_many: bool,
        description: str,
        long_description: str | Path,
        depends_on: list[Object],
        owner_org: Object,
        code_repo: Object,
        repo_branch: str,
        image_name: str,
        build_args: str,
        container_registry_profile: Object,
        config_schema: dict[str, Any],
        app_base: Path,
    ):
        self.key = key

        self.name = name  # mandatory field
        self.display_name = display_name  # mandatory field

        self.type = app_type or Type.device
        self.visibility = visibility or Visibility.private

        self.allow_many = allow_many or False
        self.depends_on = depends_on or []

        self.description = description or ""

        path = app_base and long_description and app_base / long_description
        if path and path.exists():
            self.long_description = path.read_text()
        else:
            self.long_description = long_description or ""

        self.owner_org = owner_org or Object(key=None)
        self.code_repo = code_repo or Object(key=None)
        self.repo_branch = repo_branch or "main"

        self.container_registry_profile = container_registry_profile or Object(key=None)
        self.image_name = image_name
        self.build_args = build_args

        self.config_schema = config_schema or {}

        self.base_path = app_base

    @property
    def src_directory(self):
        return self.base_path / "src" / self.name.replace("-", "_")

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "Application":
        pass

    @classmethod
    def from_config(cls, data: dict, app_base: Path) -> "Application":
        return cls(
            data.get("key"),
            data.get("name"),
            data.get("display_name"),
            data.get("type"),
            data.get("visibility"),
            data.get("allow_many", False),
            data.get("description"),
            data.get("long_description"),
            [Object(key=d) for d in data.get("depends_on", [])],
            Object(key=data.get("owner_org")),
            Object(key=data.get("code_repo")),
            data.get("repo_branch"),
            data.get("image_name"),
            data.get("build_args"),
            Object(key=data.get("container_registry_profile")),
            data.get("config_schema"),
            app_base,
        )

    def to_dict(self, include_deployment_data: bool = False) -> dict[str, Any]:
        data = {
            "key": self.key,
            "name": self.name,
            "display_name": self.display_name,
            "type": self.type,
            "visibility": self.visibility,
            "allow_many": self.allow_many,
            "description": self.description,
            "long_description": self.long_description,
            "depends_on": [dep.key for dep in self.depends_on],
            "owner_org_key": self.owner_org.key,
            "code_repo_key": self.code_repo.key,
            "container_registry_profile_key": self.container_registry_profile.key,
            "repo_branch": self.repo_branch,
            "image_name": self.image_name,
            "config_schema": self.config_schema,
        }
        if include_deployment_data:
            tmp_fp = Path(f"/tmp/{self.name}_deployment_data.zip")
            shutil.make_archive(
                str(tmp_fp.with_suffix("")), "zip", self.base_path / "deployment"
            )
            data["deployment_data"] = base64.b64encode(tmp_fp.read_bytes()).decode(
                "utf-8"
            )

        return data

    def save_to_disk(self):
        """Saves the application configuration to the disk."""
        if not self.base_path:
            raise ValueError("Application base path is not set.")

        config_path = self.base_path / "doover_config.json"
        data: dict[str, dict[str, Any]] = (
            json.loads(config_path.read_text())
            if config_path.exists()
            else {self.name: {}}
        )
        data[self.name].update(**self.to_dict())
        config_path.write_text(json.dumps(data, indent=4))
        log.info(f"Configuration saved to {config_path}")
