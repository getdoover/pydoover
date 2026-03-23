from __future__ import annotations

import inspect
import platform
from collections.abc import Collection
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Generic, Protocol, TypeVar, cast, overload
from urllib.parse import urlencode

from ..auth import (
    AsyncDoover2AuthClient,
    AuthProfile,
    Doover2AuthClient,
)
from ..auth._base import (
    DEFAULT_CONTROL_BASE_URL,
    AsyncAuthClient,
    SyncAuthClient,
    _normalise_datetime,
)
from ... import __version__
from ...models import control as control_models
from ...models.data.exceptions import (
    ForbiddenError,
    HTTPError,
    NotFoundError,
    UnauthorizedError,
)

_python_version = platform.python_version()
TControlModel = TypeVar("TControlModel", bound=control_models.ControlModel)
TValue = TypeVar("TValue")


class ControlMethodUnavailableError(AttributeError):
    pass


@dataclass(frozen=True, slots=True)
class ControlResourceMethods(Generic[TControlModel]):
    model_name: str
    model: type[TControlModel]
    _get: Callable[..., TControlModel] | None = None
    _post: Callable[..., TControlModel] | None = None
    _patch: Callable[..., TControlModel] | None = None
    _put: Callable[..., TControlModel] | None = None
    _list: Callable[..., control_models.ControlPage[TControlModel]] | None = None

    def available_operations(self) -> tuple[str, ...]:
        operations = []
        if self._get is not None:
            operations.append("get")
        if self._post is not None:
            operations.append("post")
        if self._patch is not None:
            operations.append("patch")
        if self._put is not None:
            operations.append("put")
        if self._list is not None:
            operations.append("list")
        return tuple(operations)

    def supports(self, operation: str) -> bool:
        return operation in self.available_operations()

    def get(self, *args: Any, **kwargs: Any) -> TControlModel:
        method = self._require("get", self._get)
        return method(*args, **kwargs)

    def post(self, *args: Any, **kwargs: Any) -> TControlModel:
        method = self._require("post", self._post)
        return method(*args, **kwargs)

    def patch(self, *args: Any, **kwargs: Any) -> TControlModel:
        method = self._require("patch", self._patch)
        return method(*args, **kwargs)

    def put(self, *args: Any, **kwargs: Any) -> TControlModel:
        method = self._require("put", self._put)
        return method(*args, **kwargs)

    def list(self, *args: Any, **kwargs: Any) -> control_models.ControlPage[TControlModel]:
        method = self._require("list", self._list)
        return method(*args, **kwargs)

    @staticmethod
    def _require(operation: str, method: TValue | None) -> TValue:
        if method is None:
            raise ControlMethodUnavailableError(
                f"Control resource does not support {operation!r}."
            )
        return method


def _build_user_agent(http_lib: str, http_lib_version: str) -> str:
    return (
        f"pydoover/{__version__} Python/{_python_version} {http_lib}/{http_lib_version}"
    )


def _raise_for_status(status: int, text: str, url: str):
    if 200 <= status < 300:
        return
    if status == 401:
        raise UnauthorizedError(text, url)
    if status == 403:
        raise ForbiddenError(text, url)
    if status == 404:
        raise NotFoundError(text, url)
    raise HTTPError(status, text, url)


def _normalize_control_base_url(base_url: str | None, control_base_url: str | None) -> str:
    if base_url and control_base_url and base_url.rstrip("/") != control_base_url.rstrip("/"):
        raise ValueError("`base_url` and `control_base_url` must match when both are provided.")
    return (control_base_url or base_url or DEFAULT_CONTROL_BASE_URL).rstrip("/")


def _validate_profile_input(profile: Any):
    if profile is None:
        return
    if not isinstance(profile, (str, AuthProfile)):
        raise TypeError("`profile` must be a profile name or AuthProfile instance.")


def _is_async_callable(value: Any) -> bool:
    return callable(value) and inspect.iscoroutinefunction(value)


def _validate_sync_auth(auth: Any) -> SyncAuthClient:
    missing = [
        name
        for name in ("token", "set_token", "get_auth_headers", "ensure_token")
        if not hasattr(auth, name)
    ]
    if missing:
        raise TypeError(
            "Sync control clients require an auth client with "
            + ", ".join(sorted(missing))
            + "."
        )
    ensure_token = getattr(auth, "ensure_token")
    close = getattr(auth, "close", None)
    if _is_async_callable(ensure_token) or _is_async_callable(close):
        raise TypeError("Sync control clients require a synchronous auth client.")
    return auth


def _validate_async_auth(auth: Any) -> AsyncAuthClient:
    missing = [
        name
        for name in ("token", "set_token", "get_auth_headers", "ensure_token")
        if not hasattr(auth, name)
    ]
    if missing:
        raise TypeError(
            "Async control clients require an auth client with "
            + ", ".join(sorted(missing))
            + "."
        )
    if not _is_async_callable(getattr(auth, "ensure_token")):
        raise TypeError("Async control clients require an asynchronous auth client.")
    return auth


_AUTH_KWARGS = (
    "auth",
    "profile",
    "control_base_url",
    "token",
    "token_expires",
    "refresh_token",
    "refresh_token_id",
    "auth_server_url",
    "auth_server_client_id",
)


def _consume_auth_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    return {name: kwargs.pop(name, None) for name in _AUTH_KWARGS}


def build_sync_control_auth(
    *,
    base_url: str | None = None,
    timeout: float,
    auth: SyncAuthClient | None = None,
    profile: str | AuthProfile | None = None,
    control_base_url: str | None = None,
    token: str | None = None,
    token_expires=None,
    refresh_token: str | None = None,
    refresh_token_id: str | None = None,
    auth_server_url: str | None = None,
    auth_server_client_id: str | None = None,
) -> tuple[SyncAuthClient, str, bool]:
    _validate_profile_input(profile)

    if auth is not None:
        auth_client = _validate_sync_auth(auth)
        resolved = _normalize_control_base_url(
            base_url,
            control_base_url or getattr(auth_client, "control_base_url", None),
        )
        return auth_client, resolved, False

    if profile is not None:
        auth_client = Doover2AuthClient.from_profile(profile, timeout=timeout)
        if token is not None:
            auth_client.set_token(token)
            auth_client.token_expires = _normalise_datetime(token_expires)
        if control_base_url is not None:
            auth_client.control_base_url = control_base_url.rstrip("/")
        if refresh_token is not None:
            auth_client.refresh_token = refresh_token
        if refresh_token_id is not None:
            auth_client.refresh_token_id = refresh_token_id
        if auth_server_url is not None:
            auth_client.auth_server_url = auth_server_url.rstrip("/")
        if auth_server_client_id is not None:
            auth_client.auth_server_client_id = auth_server_client_id
    else:
        auth_client = Doover2AuthClient(
            token=token,
            token_expires=token_expires,
            refresh_token=refresh_token,
            refresh_token_id=refresh_token_id,
            control_base_url=_normalize_control_base_url(base_url, control_base_url),
            auth_server_url=auth_server_url,
            auth_server_client_id=auth_server_client_id,
            timeout=timeout,
        )

    resolved = _normalize_control_base_url(
        base_url,
        control_base_url or auth_client.control_base_url,
    )
    auth_client.control_base_url = resolved
    return auth_client, resolved, True


def build_async_control_auth(
    *,
    base_url: str | None = None,
    timeout: float,
    auth: AsyncAuthClient | None = None,
    profile: str | AuthProfile | None = None,
    control_base_url: str | None = None,
    token: str | None = None,
    token_expires=None,
    refresh_token: str | None = None,
    refresh_token_id: str | None = None,
    auth_server_url: str | None = None,
    auth_server_client_id: str | None = None,
) -> tuple[AsyncAuthClient, str, bool]:
    _validate_profile_input(profile)

    if auth is not None:
        auth_client = _validate_async_auth(auth)
        resolved = _normalize_control_base_url(
            base_url,
            control_base_url or getattr(auth_client, "control_base_url", None),
        )
        return auth_client, resolved, False

    if profile is not None:
        auth_client = AsyncDoover2AuthClient.from_profile(profile, timeout=timeout)
        if token is not None:
            auth_client.set_token(token)
            auth_client.token_expires = _normalise_datetime(token_expires)
        if control_base_url is not None:
            auth_client.control_base_url = control_base_url.rstrip("/")
        if refresh_token is not None:
            auth_client.refresh_token = refresh_token
        if refresh_token_id is not None:
            auth_client.refresh_token_id = refresh_token_id
        if auth_server_url is not None:
            auth_client.auth_server_url = auth_server_url.rstrip("/")
        if auth_server_client_id is not None:
            auth_client.auth_server_client_id = auth_server_client_id
    else:
        auth_client = AsyncDoover2AuthClient(
            token=token,
            token_expires=token_expires,
            refresh_token=refresh_token,
            refresh_token_id=refresh_token_id,
            control_base_url=_normalize_control_base_url(base_url, control_base_url),
            auth_server_url=auth_server_url,
            auth_server_client_id=auth_server_client_id,
            timeout=timeout,
        )

    resolved = _normalize_control_base_url(
        base_url,
        control_base_url or auth_client.control_base_url,
    )
    auth_client.control_base_url = resolved
    return auth_client, resolved, True


class BaseControlClient:
    def __init__(
        self,
        base_url: str,
        *,
        auth: SyncAuthClient | AsyncAuthClient,
        owns_auth: bool = False,
        organisation_id: int | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.organisation_id = int(organisation_id) if organisation_id else None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self._owns_auth = owns_auth

    @cached_property
    def _control_method_lookup(self) -> dict[str, dict[str, Callable[..., Any]]]:
        lookup: dict[str, dict[str, tuple[tuple[int, int, int, int], Callable[..., Any]]]] = {}

        for group_path, group in self._iter_control_groups():
            for method_name in dir(group):
                if method_name.startswith("_"):
                    continue

                operation = self._normalise_control_operation(method_name)
                if operation is None:
                    continue

                method = getattr(group, method_name)
                if not callable(method):
                    continue

                model_name = self._get_method_model_name(method)
                if model_name is None:
                    continue

                score = self._score_control_method(group_path, method_name, method)
                existing = lookup.setdefault(model_name, {}).get(operation)
                if existing is None or score < existing[0]:
                    lookup[model_name][operation] = (score, method)

        return {
            model_name: {
                operation: method
                for operation, (_, method) in methods.items()
            }
            for model_name, methods in lookup.items()
        }

    @property
    def token(self) -> str | None:
        return self.auth.token

    def set_token(self, token: str):
        self.auth.set_token(token)

    @overload
    def get_control_methods(
        self,
        model: type[TControlModel],
    ) -> ControlResourceMethods[TControlModel]: ...

    @overload
    def get_control_methods(
        self,
        model: str,
    ) -> ControlResourceMethods[control_models.ControlModel]: ...

    def get_control_methods(
        self,
        model: str | type[TControlModel],
    ) -> ControlResourceMethods[TControlModel] | ControlResourceMethods[control_models.ControlModel]:
        model_name, model_cls = self._resolve_control_model(model)
        try:
            methods = self._control_method_lookup[model_name]
        except KeyError as exc:
            raise KeyError(f"No control methods found for model {model_name!r}.") from exc

        resource = ControlResourceMethods(
            model_name=model_name,
            model=cast(type[control_models.ControlModel], model_cls),
            _get=cast(Callable[..., control_models.ControlModel] | None, methods.get("get")),
            _post=cast(Callable[..., control_models.ControlModel] | None, methods.get("post")),
            _patch=cast(
                Callable[..., control_models.ControlModel] | None,
                methods.get("patch"),
            ),
            _put=cast(Callable[..., control_models.ControlModel] | None, methods.get("put")),
            _list=cast(
                Callable[..., control_models.ControlPage[control_models.ControlModel]] | None,
                methods.get("list"),
            ),
        )
        return cast(ControlResourceMethods[TControlModel], resource)

    def get_control_method(
        self,
        model: str | type[control_models.ControlModel],
        operation: str,
    ) -> Callable[..., Any]:
        model_name, _ = self._resolve_control_model(model)
        normalised_operation = self._coerce_control_operation_name(operation)

        try:
            return self._control_method_lookup[model_name][normalised_operation]
        except KeyError as exc:
            raise KeyError(
                f"No control method found for model {model_name!r} and "
                f"operation {normalised_operation!r}."
            ) from exc

    def _auth_headers(self, organisation_id: int | None = None) -> dict[str, str]:
        headers = dict(self.auth.get_auth_headers())
        org = organisation_id or self.organisation_id
        if org:
            headers["X-Doover-Organisation"] = str(org)
        return headers

    def _build_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    @staticmethod
    def _build_query(params: dict[str, Any]) -> str:
        filtered = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, bool):
                filtered[key] = str(value).lower()
            elif isinstance(value, list):
                filtered[key] = value
            else:
                filtered[key] = value
        if not filtered:
            return ""
        return "?" + urlencode(filtered, doseq=True)

    def _serialize_body(self, body: Any, schema_name: str | None, method: str) -> Any:
        if body is None:
            return None
        if isinstance(body, control_models.ControlModel):
            if schema_name is None:
                return body.to_dict()
            return body.to_version(schema_name, method=method)
        if isinstance(body, dict):
            return body
        raise TypeError("Control request bodies must be dicts or ControlModel instances.")

    def _deserialize_model(self, schema_name: str, data: dict[str, Any]):
        info = control_models.resolve_control_schema(schema_name)
        model_cls = getattr(control_models, info["model"])
        return model_cls.from_version(info["version"], data)

    def _deserialize_page(self, schema_name: str, data: dict[str, Any]):
        info = control_models.resolve_control_schema(schema_name)
        model_cls = getattr(control_models, info["model"])
        results = [
            model_cls.from_version(info["version"], item)
            for item in data.get("results") or []
        ]
        return control_models.ControlPage(
            count=data.get("count", 0),
            next=data.get("next"),
            previous=data.get("previous"),
            results=results,
        )

    def _deserialize_list(self, item_schema: str, data: list[dict[str, Any]]):
        info = control_models.resolve_control_schema(item_schema)
        model_cls = getattr(control_models, info["model"])
        return [model_cls.from_version(info["version"], item) for item in data]

    @staticmethod
    def _coerce_control_operation_name(operation: str) -> str:
        aliases = {
            "retrieve": "get",
            "get": "get",
            "create": "post",
            "post": "post",
            "partial": "patch",
            "patch": "patch",
            "update": "put",
            "put": "put",
            "list": "list",
        }
        try:
            return aliases[operation]
        except KeyError as exc:
            raise ValueError(f"Unsupported control operation {operation!r}.") from exc

    @classmethod
    def _normalise_control_operation(cls, method_name: str) -> str | None:
        for suffix, operation in (
            ("_retrieve", "get"),
            ("_create", "post"),
            ("_partial", "patch"),
            ("_update", "put"),
            ("_list", "list"),
        ):
            if method_name.endswith(suffix):
                return operation
        if method_name in {"retrieve", "create", "partial", "update", "list"}:
            return cls._coerce_control_operation_name(method_name)
        return None

    def _resolve_control_model(
        self,
        model: str | type[TControlModel],
    ) -> tuple[str, type[TControlModel] | type[control_models.ControlModel]]:
        if isinstance(model, str):
            try:
                model_cls = getattr(control_models, model)
            except AttributeError as exc:
                raise KeyError(f"Unknown control model {model!r}.") from exc
            if not isinstance(model_cls, type) or not issubclass(
                model_cls,
                control_models.ControlModel,
            ):
                raise TypeError(f"{model!r} is not a control model.")
            return model, model_cls
        if isinstance(model, type) and issubclass(model, control_models.ControlModel):
            return model.__name__, model
        raise TypeError("`model` must be a control model name or ControlModel subclass.")

    def _iter_control_groups(self) -> list[tuple[tuple[str, ...], Any]]:
        stack: list[tuple[tuple[str, ...], Any]] = [((), self)]
        groups: list[tuple[tuple[str, ...], Any]] = []
        seen: set[int] = set()

        while stack:
            path, node = stack.pop()
            node_id = id(node)
            if node_id in seen:
                continue
            seen.add(node_id)

            for attr_name, value in vars(node).items():
                if isinstance(value, _ControlGroupBase):
                    child_path = (*path, attr_name)
                    groups.append((child_path, value))
                    stack.append((child_path, value))

        return groups

    @staticmethod
    def _get_method_model_name(method: Callable[..., Any]) -> str | None:
        return_annotation = inspect.signature(method).return_annotation
        if return_annotation is inspect.Signature.empty:
            return None

        if isinstance(return_annotation, str):
            marker = "control_models."
            matches = [
                part.split("[", 1)[0]
                for part in return_annotation.replace("]", "").split(marker)[1:]
            ]
            matches = [match for match in matches if match != "ControlPage"]
            return matches[-1] if matches else None

        if isinstance(return_annotation, type) and issubclass(
            return_annotation,
            control_models.ControlModel,
        ):
            return return_annotation.__name__

        return None

    @staticmethod
    def _score_control_method(
        group_path: tuple[str, ...],
        method_name: str,
        method: Callable[..., Any],
    ) -> tuple[int, int, int, int]:
        signature = inspect.signature(method)
        required_params = 0
        for parameter in signature.parameters.values():
            if parameter.name == "organisation_id":
                continue
            if parameter.default is inspect.Signature.empty:
                required_params += 1

        is_prefixed = 0 if "_" not in method_name else 1
        return (is_prefixed, required_params, len(group_path), len(method_name))


class _SyncControlExecutor(Protocol):
    def _execute(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        body_schema: str | None = None,
        body_mode: str = "json",
        binary_fields: Collection[str] | None = None,
        organisation_id: int | None = None,
        response_kind: str = "raw",
        response_schema: str | None = None,
        item_schema: str | None = None,
    ) -> Any: ...


class _AsyncControlExecutor(Protocol):
    async def _execute(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        body_schema: str | None = None,
        body_mode: str = "json",
        binary_fields: Collection[str] | None = None,
        organisation_id: int | None = None,
        response_kind: str = "raw",
        response_schema: str | None = None,
        item_schema: str | None = None,
    ) -> Any: ...


TRoot = TypeVar("TRoot")


class _ControlGroupBase(Generic[TRoot]):
    def __init__(self, root: TRoot):
        self._root = root
