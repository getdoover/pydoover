import base64
import json
import logging
import shutil
from pathlib import Path
from typing import Any

from .object import Object

log = logging.getLogger(__name__)


def get_id_or_key(data: dict[str, Any], key: str) -> Any:
    """Small helper function to allow a user to set `None` for the key_id field."""
    try:
        return data[f"{key}_id"]
    except KeyError:
        return data.get(key)


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
        id: str | None,
        key: str | None,
        name: str | None,
        display_name: str | None,
        app_type: str | None,
        visibility: str | None,
        allow_many: bool,
        description: str | None,
        long_description: str | Path | None,
        depends_on: list[Object],
        owner_org: Object | None,
        code_repo: Object | None,
        repo_branch: str | None,
        image_name: str | None,
        build_args: str | None,
        container_registry_profile: Object | None,
        lambda_arn: str | None,
        lambda_config: dict[str, Any] | None,
        export_config_command: str | None,
        run_command: str | None,
        config_schema: dict[str, Any] | None,
        staging_config: dict[str, Any] | None,
        icon_url: str | None,
        banner_url: str | None,
        app_base: Path,
    ):
        self.id = id
        self.key = key

        self.name = name  # mandatory field
        self.display_name = display_name  # mandatory field

        self.type = app_type or Type.device
        self.visibility = visibility or Visibility.private

        self.allow_many = allow_many or False
        self.depends_on = depends_on or []

        self.description = description or ""

        path = (
            app_base / long_description
            if isinstance(long_description, str)
            else long_description
        )
        if isinstance(path, Path) and path.exists():
            self.long_description = path.read_text()
        else:
            self.long_description = long_description or ""

        self.owner_org = owner_org or Object(id=None)
        self.code_repo = code_repo or Object(id=None)
        self.repo_branch = repo_branch or "main"

        self.container_registry_profile = container_registry_profile or Object(id=None)
        self.icon_url = icon_url
        self.banner_url = banner_url
        self.image_name = image_name
        self.build_args = build_args

        self.lambda_arn = lambda_arn
        self.lambda_config = lambda_config or {}

        self.export_config_command = export_config_command
        self.run_command = run_command

        self.config_schema = config_schema or {}
        self.staging_config = staging_config or {}

        self.base_path = app_base

    @property
    def src_directory(self) -> Path:
        return self.base_path / "src" / (self.name or "").replace("-", "_")

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "Application":
        raise NotImplementedError

    @classmethod
    def from_config(cls, data: dict[str, Any], app_base: Path) -> "Application":
        return cls(
            data.get("id"),
            data.get("key"),
            data.get("name"),
            data.get("display_name"),
            data.get("type"),
            data.get("visibility"),
            data.get("allow_many", False),
            data.get("description"),
            data.get("long_description"),
            [Object(id=d) for d in data.get("depends_on", [])],
            Object(
                id=get_id_or_key(data, "owner_org")
                or get_id_or_key(data, "organisation")
            ),
            Object(id=get_id_or_key(data, "code_repo_id")),
            data.get("repo_branch"),
            data.get("image_name"),
            data.get("build_args"),
            Object(id=get_id_or_key(data, "container_registry_profile")),
            data.get("lambda_arn"),
            data.get("lambda_config"),
            data.get("export_config_command"),
            data.get("run_command"),
            data.get("config_schema"),
            data.get("staging_config", {}),
            data.get("icon_url", None),
            data.get("banner_url", None),
            app_base,
        )

    def to_dict(
        self,
        include_deployment_data: bool = False,
        is_staging: bool = False,
        include_cloud_only: bool = False,
    ) -> dict[str, Any]:
        data = {
            "name": self.name,
            "id": self.id,
            "key": self.key,
            "display_name": self.display_name,
            "type": self.type,
            "visibility": self.visibility,
            "allow_many": self.allow_many,
            "description": self.description,
            "long_description": self.long_description,
            "depends_on": [dep.id for dep in self.depends_on],
            "owner_org_id": self.owner_org.id,
            # duplicate these fields for now...
            "organisation_id": self.owner_org.id,
            "code_repo_id": self.code_repo.id,
            "container_registry_profile_id": self.container_registry_profile.id,
            "repo_branch": self.repo_branch,
            "image_name": self.image_name,
            "lambda_config": self.lambda_config,
            "config_schema": self.config_schema,
            "icon_url": self.icon_url,
            "banner_url": self.banner_url,
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
            data["export_config_command"] = self.export_config_command
            data["run_command"] = self.run_command

        if include_cloud_only:
            data["lambda_arn"] = self.lambda_arn

        return data

    def save_to_disk(self):
        """Saves the application configuration to the disk."""
        if not self.base_path:
            raise ValueError("Application base path is not set.")

        config_path = self.base_path / "doover_config.json"
        app_name = self.name or ""
        data: dict[str, dict[str, Any]] = (
            dict(json.loads(config_path.read_text()))
            if config_path.exists()
            else {app_name: {}}
        )

        upstream = self.to_dict(include_cloud_only=True)
        upstream.pop("long_description", None)
        # upstream.pop("owner_org_id", None)
        # upstream.pop("code_repo_id", None)
        # upstream.pop("container_registry_profile_id", None)

        data.setdefault(app_name, {}).update(**upstream)
        config_path.write_text(json.dumps(data, indent=4))
        log.info(f"Configuration saved to {config_path}")
