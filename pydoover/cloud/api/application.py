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

    .. note::

        While not generally relevant, a `staging_config` field (dictionary) in `doover_config.json` can be used to
        override the main configuration when deploying the app to a staging environment. This is useful for testing.


    Attributes:
    """

    def __init__(
        self,
        id: str,
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
        lambda_arn: str,
        lambda_config: dict[str, Any],
        config_schema: dict[str, Any],
        staging_config: dict[str, Any],
        app_base: Path,
    ):
        self.id = id

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

        self.owner_org = owner_org or Object(id=None)
        self.code_repo = code_repo or Object(id=None)
        self.repo_branch = repo_branch or "main"

        self.container_registry_profile = container_registry_profile or Object(id=None)
        self.image_name = image_name
        self.build_args = build_args

        self.lambda_arn = lambda_arn
        self.lambda_config = lambda_config

        self.config_schema = config_schema or {}
        self.staging_config = staging_config

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
            data.get("id"),
            data.get("name"),
            data.get("display_name"),
            data.get("type"),
            data.get("visibility"),
            data.get("allow_many", False),
            data.get("description"),
            data.get("long_description"),
            [Object(id=d) for d in data.get("depends_on", [])],
            Object(id=data.get("owner_org") or data.get("owner_org_id")),
            Object(id=data.get("code_repo") or data.get("code_repo_id")),
            data.get("repo_branch"),
            data.get("image_name"),
            data.get("build_args"),
            Object(
                id=data.get("container_registry_profile")
                or data.get("container_registry_profile_id")
            ),
            data.get("lambda_arn"),
            data.get("lambda_config"),
            data.get("config_schema"),
            data.get("staging_config", {}),
            app_base,
        )

    def to_dict(
        self, include_deployment_data: bool = False, is_staging: bool = False
    ) -> dict[str, Any]:
        data = {
            "name": self.name,
            "id": self.id,
            "display_name": self.display_name,
            "type": self.type,
            "visibility": self.visibility,
            "allow_many": self.allow_many,
            "description": self.description,
            "long_description": self.long_description,
            "depends_on": [dep.id for dep in self.depends_on],
            "owner_org_id": self.owner_org.id,
            "code_repo_id": self.code_repo.id,
            "container_registry_profile_id": self.container_registry_profile.id,
            "repo_branch": self.repo_branch,
            "image_name": self.image_name,
            "lambda_arn": self.lambda_arn,
            "lambda_config": self.lambda_config,
            "config_schema": self.config_schema,
        }

        if include_deployment_data:
            if is_staging:
                # allow staging config to override the main config
                data.update(**self.staging_config)

            deployment_fp = self.base_path / "deployment"
            if deployment_fp.exists():
                tmp_fp = Path(f"/tmp/{self.name}_deployment_data.zip")
                shutil.make_archive(str(tmp_fp.with_suffix("")), "zip", deployment_fp)
                data["deployment_data"] = base64.b64encode(tmp_fp.read_bytes()).decode(
                    "utf-8"
                )
            else:
                data["deployment_data"] = None
        else:
            data["staging_config"] = self.staging_config

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

        upstream = self.to_dict()
        upstream.pop("long_description", None)
        # upstream.pop("owner_org_id", None)
        # upstream.pop("code_repo_id", None)
        # upstream.pop("container_registry_profile_id", None)

        data[self.name].update(**upstream)
        config_path.write_text(json.dumps(data, indent=4))
        log.info(f"Configuration saved to {config_path}")
