from __future__ import annotations

from typing import Any, Sequence

from ...models import control as control_models

from ._base import _SyncControlExecutor, _ControlGroupBase


class ControlClientGroups:
    agents: AgentsSyncGroup
    analytics: AnalyticsSyncGroup
    app_deployments: AppDeploymentsSyncGroup
    app_installs: AppInstallsSyncGroup
    applications: ApplicationsSyncGroup
    assistant: AssistantSyncGroup
    container: ContainerSyncGroup
    devices: DevicesSyncGroup
    groups: GroupsSyncGroup
    integrations: IntegrationsSyncGroup
    organisations: OrganisationsSyncGroup
    permissions: PermissionsSyncGroup
    reports: ReportsSyncGroup
    shared_devices: SharedDevicesSyncGroup
    shared_groups: SharedGroupsSyncGroup
    site: SiteSyncGroup
    solution_installs: SolutionInstallsSyncGroup
    solutions: SolutionsSyncGroup
    themes: ThemesSyncGroup
    tunnels: TunnelsSyncGroup
    users: UsersSyncGroup

    def _execute(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

class AgentsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def retrieve(self, organisation_id: int | None = None) -> None:
        path = f"/agents/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

class AnalyticsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def summary(self, organisation_id: int | None = None) -> None:
        path = f"/analytics/summary/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def summary_retrieve_2(self, days: int, organisation_id: int | None = None) -> None:
        path = f"/analytics/summary/{days}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

class AppDeploymentsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, body: Any, organisation_id: int | None = None) -> control_models.ApplicationDeployment:
        path = f"/app_deployments/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='ApplicationDeploymentSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationDeploymentSerializerDetail',
            item_schema=None,
        )

    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.ApplicationDeployment]:
        path = f"/app_deployments/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedApplicationDeploymentSerializerListList',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.ApplicationDeployment:
        path = f"/app_deployments/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationDeploymentSerializerDetail',
            item_schema=None,
        )

class AppInstallsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def archive(self, id: str, organisation_id: int | None = None) -> control_models.ApplicationInstallation:
        path = f"/app_installs/{id}/archive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationInstallationSerializerDetail',
            item_schema=None,
        )

    def create(self, body: Any, organisation_id: int | None = None) -> control_models.ApplicationInstallation:
        path = f"/app_installs/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='ApplicationInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationInstallationSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/app_installs/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def deployments_create(self, parent_lookup_app_install: str, body: Any, organisation_id: int | None = None) -> control_models.ApplicationDeployment:
        path = f"/app_installs/{parent_lookup_app_install}/deployments/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='ApplicationDeploymentSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationDeploymentSerializerDetail',
            item_schema=None,
        )

    def deployments_retrieve(self, id: str, parent_lookup_app_install: str, organisation_id: int | None = None) -> control_models.ApplicationDeployment:
        path = f"/app_installs/{parent_lookup_app_install}/deployments/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationDeploymentSerializerDetail',
            item_schema=None,
        )

    def deployments_list(self, parent_lookup_app_install: str, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.ApplicationDeployment]:
        path = f"/app_installs/{parent_lookup_app_install}/deployments/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedApplicationDeploymentSerializerListList',
            item_schema=None,
        )

    def list(self, application: str | None = None, archived: bool | None = None, device: str | None = None, display_name: str | None = None, display_name__contains: str | None = None, display_name__icontains: str | None = None, id: int | None = None, name: str | None = None, name__contains: str | None = None, name__icontains: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, solution: str | None = None, status: str | None = None, template: str | None = None, version: str | None = None, version__contains: str | None = None, version__icontains: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.ApplicationInstallation]:
        path = f"/app_installs/"
        params = {
            "application": application,
            "archived": archived,
            "device": device,
            "display_name": display_name,
            "display_name__contains": display_name__contains,
            "display_name__icontains": display_name__icontains,
            "id": id,
            "name": name,
            "name__contains": name__contains,
            "name__icontains": name__icontains,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "search": search,
            "solution": solution,
            "status": status,
            "template": template,
            "version": version,
            "version__contains": version__contains,
            "version__icontains": version__icontains,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedApplicationInstallationSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.ApplicationInstallation:
        path = f"/app_installs/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedApplicationInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationInstallationSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.ApplicationInstallation:
        path = f"/app_installs/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationInstallationSerializerDetail',
            item_schema=None,
        )

    def sync_config_profiles(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.ApplicationInstallation:
        path = f"/app_installs/{id}/sync_config_profiles/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='ApplicationInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationInstallationSerializerDetail',
            item_schema=None,
        )

    def unarchive(self, id: str, organisation_id: int | None = None) -> control_models.ApplicationInstallation:
        path = f"/app_installs/{id}/unarchive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationInstallationSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.ApplicationInstallation:
        path = f"/app_installs/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='ApplicationInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationInstallationSerializerDetail',
            item_schema=None,
        )

class ApplicationsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def archive(self, id: str, organisation_id: int | None = None) -> control_models.Application:
        path = f"/applications/{id}/archive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationSerializerDetail',
            item_schema=None,
        )

    def config_profiles_create(self, parent_lookup_application: str, body: Any, organisation_id: int | None = None) -> control_models.ApplicationConfigProfile:
        path = f"/applications/{parent_lookup_application}/config_profiles/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='ApplicationConfigProfileSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationConfigProfileSerializerDetail',
            item_schema=None,
        )

    def config_profiles_retrieve(self, id: str, parent_lookup_application: str, organisation_id: int | None = None) -> control_models.ApplicationConfigProfile:
        path = f"/applications/{parent_lookup_application}/config_profiles/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationConfigProfileSerializerDetail',
            item_schema=None,
        )

    def config_profiles_update(self, id: str, parent_lookup_application: str, body: Any, organisation_id: int | None = None) -> control_models.ApplicationConfigProfile:
        path = f"/applications/{parent_lookup_application}/config_profiles/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='ApplicationConfigProfileSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationConfigProfileSerializerDetail',
            item_schema=None,
        )

    def config_profiles_list(self, parent_lookup_application: str, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.ApplicationConfigProfile]:
        path = f"/applications/{parent_lookup_application}/config_profiles/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedApplicationConfigProfileSerializerListList',
            item_schema=None,
        )

    def config_profiles_partial(self, id: str, parent_lookup_application: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.ApplicationConfigProfile:
        path = f"/applications/{parent_lookup_application}/config_profiles/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedApplicationConfigProfileSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationConfigProfileSerializerDetail',
            item_schema=None,
        )

    def create(self, body: Any, organisation_id: int | None = None) -> control_models.Application:
        path = f"/applications/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='ApplicationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, parent_lookup_application: str, organisation_id: int | None = None) -> None:
        path = f"/applications/{parent_lookup_application}/config_profiles/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def installs_list(self, parent_lookup_application: str, application: str | None = None, archived: bool | None = None, device: str | None = None, display_name: str | None = None, display_name__contains: str | None = None, display_name__icontains: str | None = None, id: int | None = None, name: str | None = None, name__contains: str | None = None, name__icontains: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, solution: str | None = None, status: str | None = None, template: str | None = None, version: str | None = None, version__contains: str | None = None, version__icontains: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.ApplicationInstallation]:
        path = f"/applications/{parent_lookup_application}/installs/"
        params = {
            "application": application,
            "archived": archived,
            "device": device,
            "display_name": display_name,
            "display_name__contains": display_name__contains,
            "display_name__icontains": display_name__icontains,
            "id": id,
            "name": name,
            "name__contains": name__contains,
            "name__icontains": name__icontains,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "search": search,
            "solution": solution,
            "status": status,
            "template": template,
            "version": version,
            "version__contains": version__contains,
            "version__icontains": version__icontains,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedApplicationInstallationSerializerListList',
            item_schema=None,
        )

    def installs_sync_config_profiles(self, id: str, parent_lookup_application: str, body: Any, organisation_id: int | None = None) -> control_models.ApplicationInstallation:
        path = f"/applications/{parent_lookup_application}/installs/{id}/sync_config_profiles/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='ApplicationInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationInstallationSerializerDetail',
            item_schema=None,
        )

    def list(self, allow_many: bool | None = None, approx_installs: int | None = None, approx_installs__gt: int | None = None, approx_installs__gte: int | None = None, approx_installs__lt: int | None = None, approx_installs__lte: int | None = None, archived: bool | None = None, container_registry_profile: str | None = None, description: str | None = None, description__contains: str | None = None, description__icontains: str | None = None, display_name: str | None = None, display_name__contains: str | None = None, display_name__icontains: str | None = None, id: int | None = None, name: str | None = None, name__contains: str | None = None, name__icontains: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, stars: int | None = None, stars__gt: int | None = None, stars__gte: int | None = None, stars__lt: int | None = None, stars__lte: int | None = None, type: str | None = None, visibility: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.Application]:
        path = f"/applications/"
        params = {
            "allow_many": allow_many,
            "approx_installs": approx_installs,
            "approx_installs__gt": approx_installs__gt,
            "approx_installs__gte": approx_installs__gte,
            "approx_installs__lt": approx_installs__lt,
            "approx_installs__lte": approx_installs__lte,
            "archived": archived,
            "container_registry_profile": container_registry_profile,
            "description": description,
            "description__contains": description__contains,
            "description__icontains": description__icontains,
            "display_name": display_name,
            "display_name__contains": display_name__contains,
            "display_name__icontains": display_name__icontains,
            "id": id,
            "name": name,
            "name__contains": name__contains,
            "name__icontains": name__icontains,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "search": search,
            "stars": stars,
            "stars__gt": stars__gt,
            "stars__gte": stars__gte,
            "stars__lt": stars__lt,
            "stars__lte": stars__lte,
            "type": type,
            "visibility": visibility,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedApplicationSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.Application:
        path = f"/applications/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedApplicationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationSerializerDetail',
            item_schema=None,
        )

    def processor_source(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Application:
        path = f"/applications/{id}/processor_source/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='ApplicationSerializerDetailRequest',
            body_mode="multipart",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationSerializerDetail',
            item_schema=None,
        )

    def processor_version(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Application:
        path = f"/applications/{id}/processor_version/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='ApplicationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.Application:
        path = f"/applications/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationSerializerDetail',
            item_schema=None,
        )

    def unarchive(self, id: str, organisation_id: int | None = None) -> control_models.Application:
        path = f"/applications/{id}/unarchive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Application:
        path = f"/applications/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='ApplicationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationSerializerDetail',
            item_schema=None,
        )

class AssistantSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def message(self, organisation_id: int | None = None) -> None:
        path = f"/assistant/message/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def messages(self, id: str, organisation_id: int | None = None) -> control_models.AIChatMessage:
        path = f"/assistant/messages/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='AIChatMessageSerializerDetail',
            item_schema=None,
        )

    def messages_list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.AIChatMessage]:
        path = f"/assistant/messages/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedAIChatMessageSerializerListList',
            item_schema=None,
        )

    def sessions(self, id: str, organisation_id: int | None = None) -> control_models.AIChatSession:
        path = f"/assistant/sessions/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='AIChatSessionDetailSerializerDetail',
            item_schema=None,
        )

    def sessions_list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.AIChatSession]:
        path = f"/assistant/sessions/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedAIChatSessionSerializerListList',
            item_schema=None,
        )

class ContainerSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    registry: ContainerRegistrySyncGroup

class ContainerRegistrySyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def archive(self, id: str, organisation_id: int | None = None) -> control_models.ContainerRegistryProfile:
        path = f"/container/registry/{id}/archive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ContainerRegistryProfileSeraliserDetail',
            item_schema=None,
        )

    def create(self, body: Any, organisation_id: int | None = None) -> control_models.ContainerRegistryProfile:
        path = f"/container/registry/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='ContainerRegistryProfileSeraliserDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ContainerRegistryProfileSeraliserDetail',
            item_schema=None,
        )

    def list(self, archived: bool | None = None, description: str | None = None, description__contains: str | None = None, description__icontains: str | None = None, id: int | None = None, name: str | None = None, name__contains: str | None = None, name__icontains: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, url: str | None = None, url__contains: str | None = None, url__icontains: str | None = None, username: str | None = None, username__contains: str | None = None, username__icontains: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.ContainerRegistryProfile]:
        path = f"/container/registry/"
        params = {
            "archived": archived,
            "description": description,
            "description__contains": description__contains,
            "description__icontains": description__icontains,
            "id": id,
            "name": name,
            "name__contains": name__contains,
            "name__icontains": name__icontains,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "search": search,
            "url": url,
            "url__contains": url__contains,
            "url__icontains": url__icontains,
            "username": username,
            "username__contains": username__contains,
            "username__icontains": username__icontains,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedContainerRegistryProfileSeraliserListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.ContainerRegistryProfile:
        path = f"/container/registry/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedContainerRegistryProfileSeraliserDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ContainerRegistryProfileSeraliserDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.ContainerRegistryProfile:
        path = f"/container/registry/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ContainerRegistryProfileSeraliserDetail',
            item_schema=None,
        )

    def unarchive(self, id: str, organisation_id: int | None = None) -> control_models.ContainerRegistryProfile:
        path = f"/container/registry/{id}/unarchive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ContainerRegistryProfileSeraliserDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.ContainerRegistryProfile:
        path = f"/container/registry/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='ContainerRegistryProfileSeraliserDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ContainerRegistryProfileSeraliserDetail',
            item_schema=None,
        )

class DevicesSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def app_installs_list(self, parent_lookup_device: str, application: str | None = None, archived: bool | None = None, device: str | None = None, display_name: str | None = None, display_name__contains: str | None = None, display_name__icontains: str | None = None, id: int | None = None, name: str | None = None, name__contains: str | None = None, name__icontains: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, solution: str | None = None, status: str | None = None, template: str | None = None, version: str | None = None, version__contains: str | None = None, version__icontains: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.ApplicationInstallation]:
        path = f"/devices/{parent_lookup_device}/app_installs/"
        params = {
            "application": application,
            "archived": archived,
            "device": device,
            "display_name": display_name,
            "display_name__contains": display_name__contains,
            "display_name__icontains": display_name__icontains,
            "id": id,
            "name": name,
            "name__contains": name__contains,
            "name__icontains": name__icontains,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "search": search,
            "solution": solution,
            "status": status,
            "template": template,
            "version": version,
            "version__contains": version__contains,
            "version__icontains": version__icontains,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedApplicationInstallationSerializerListList',
            item_schema=None,
        )

    def app_installs_sync_config_profiles(self, id: str, parent_lookup_device: str, body: Any, organisation_id: int | None = None) -> control_models.ApplicationInstallation:
        path = f"/devices/{parent_lookup_device}/app_installs/{id}/sync_config_profiles/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='ApplicationInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationInstallationSerializerDetail',
            item_schema=None,
        )

    def archive(self, id: str, organisation_id: int | None = None) -> control_models.Device:
        path = f"/devices/{id}/archive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceSerializerDetail',
            item_schema=None,
        )

    def create(self, body: Any, organisation_id: int | None = None) -> control_models.Device:
        path = f"/devices/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='DeviceSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, parent_lookup_device: str, organisation_id: int | None = None) -> None:
        path = f"/devices/{parent_lookup_device}/tunnels/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def installer(self, id: str, organisation_id: int | None = None) -> control_models.Device:
        path = f"/devices/{id}/installer/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceSerializerDetail',
            item_schema=None,
        )

    def installer_info(self, id: str, organisation_id: int | None = None) -> control_models.Device:
        path = f"/devices/{id}/installer/info/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceSerializerDetail',
            item_schema=None,
        )

    def installer_tarball(self, id: str, organisation_id: int | None = None) -> bytes:
        path = f"/devices/{id}/installer/tarball/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="bytes",
            response_schema=None,
            item_schema=None,
        )

    def installer_zip(self, id: str, organisation_id: int | None = None) -> bytes:
        path = f"/devices/{id}/installer/zip/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="bytes",
            response_schema=None,
            item_schema=None,
        )

    def list(self, application: str | None = None, archived: bool | None = None, display_name: str | None = None, display_name__contains: str | None = None, display_name__icontains: str | None = None, group: str | None = None, id: Sequence[Any] | None = None, name: str | None = None, name__contains: str | None = None, name__icontains: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, type: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.Device]:
        path = f"/devices/"
        params = {
            "application": application,
            "archived": archived,
            "display_name": display_name,
            "display_name__contains": display_name__contains,
            "display_name__icontains": display_name__icontains,
            "group": group,
            "id": id,
            "name": name,
            "name__contains": name__contains,
            "name__icontains": name__icontains,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "search": search,
            "type": type,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedDeviceSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.Device:
        path = f"/devices/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedDeviceSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.Device:
        path = f"/devices/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceSerializerDetail',
            item_schema=None,
        )

    def solution_installs_deploy(self, id: str, parent_lookup_device: str, body: Any, organisation_id: int | None = None) -> control_models.SolutionInstallation:
        path = f"/devices/{parent_lookup_device}/solution_installs/{id}/deploy/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='SolutionInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionInstallationSerializerDetail',
            item_schema=None,
        )

    def solution_installs_list(self, parent_lookup_device: str, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.SolutionInstallation]:
        path = f"/devices/{parent_lookup_device}/solution_installs/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedSolutionInstallationSerializerListList',
            item_schema=None,
        )

    def solution_installs_sync(self, id: str, parent_lookup_device: str, body: Any, organisation_id: int | None = None) -> control_models.SolutionInstallation:
        path = f"/devices/{parent_lookup_device}/solution_installs/{id}/sync/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='SolutionInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionInstallationSerializerDetail',
            item_schema=None,
        )

    def tunnels_create(self, parent_lookup_device: str, body: Any, organisation_id: int | None = None) -> control_models.Tunnel:
        path = f"/devices/{parent_lookup_device}/tunnels/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='TunnelSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='TunnelSerializerDetail',
            item_schema=None,
        )

    def tunnels_retrieve(self, id: str, parent_lookup_device: str, organisation_id: int | None = None) -> control_models.Tunnel:
        path = f"/devices/{parent_lookup_device}/tunnels/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='TunnelSerializerDetail',
            item_schema=None,
        )

    def tunnels_update(self, id: str, parent_lookup_device: str, body: Any, organisation_id: int | None = None) -> control_models.Tunnel:
        path = f"/devices/{parent_lookup_device}/tunnels/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='TunnelSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='TunnelSerializerDetail',
            item_schema=None,
        )

    def tunnels_activate(self, id: str, parent_lookup_device: str, body: Any, organisation_id: int | None = None) -> control_models.Tunnel:
        path = f"/devices/{parent_lookup_device}/tunnels/{id}/activate/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='TunnelSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='TunnelSerializerDetail',
            item_schema=None,
        )

    def tunnels_deactivate(self, id: str, parent_lookup_device: str, body: Any, organisation_id: int | None = None) -> control_models.Tunnel:
        path = f"/devices/{parent_lookup_device}/tunnels/{id}/deactivate/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='TunnelSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='TunnelSerializerDetail',
            item_schema=None,
        )

    def tunnels_list(self, parent_lookup_device: str, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.Tunnel]:
        path = f"/devices/{parent_lookup_device}/tunnels/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedTunnelSerializerListList',
            item_schema=None,
        )

    def tunnels_partial(self, id: str, parent_lookup_device: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.Tunnel:
        path = f"/devices/{parent_lookup_device}/tunnels/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedTunnelSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='TunnelSerializerDetail',
            item_schema=None,
        )

    def types_create(self, body: Any, organisation_id: int | None = None) -> control_models.DeviceType:
        path = f"/devices/types/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='DeviceTypeSerializerDetailRequest',
            body_mode="multipart",
            binary_fields=['installer'],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceTypeSerializerDetail',
            item_schema=None,
        )

    def types_retrieve(self, id: str, organisation_id: int | None = None) -> control_models.DeviceType:
        path = f"/devices/types/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceTypeSerializerDetail',
            item_schema=None,
        )

    def types_update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.DeviceType:
        path = f"/devices/types/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='DeviceTypeSerializerDetailRequest',
            body_mode="multipart",
            binary_fields=['installer'],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceTypeSerializerDetail',
            item_schema=None,
        )

    def types_archive(self, id: str, organisation_id: int | None = None) -> control_models.DeviceType:
        path = f"/devices/types/{id}/archive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceTypeSerializerDetail',
            item_schema=None,
        )

    def types_list(self, archived: bool | None = None, id: int | None = None, name: str | None = None, name__contains: str | None = None, name__icontains: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, stars: int | None = None, stars__gt: int | None = None, stars__gte: int | None = None, stars__lt: int | None = None, stars__lte: int | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.DeviceType]:
        path = f"/devices/types/"
        params = {
            "archived": archived,
            "id": id,
            "name": name,
            "name__contains": name__contains,
            "name__icontains": name__icontains,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "search": search,
            "stars": stars,
            "stars__gt": stars__gt,
            "stars__gte": stars__gte,
            "stars__lt": stars__lt,
            "stars__lte": stars__lte,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedDeviceTypeSerializerListList',
            item_schema=None,
        )

    def types_partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.DeviceType:
        path = f"/devices/types/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedDeviceTypeSerializerDetailRequest',
            body_mode="multipart",
            binary_fields=['installer'],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceTypeSerializerDetail',
            item_schema=None,
        )

    def types_unarchive(self, id: str, organisation_id: int | None = None) -> control_models.DeviceType:
        path = f"/devices/types/{id}/unarchive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceTypeSerializerDetail',
            item_schema=None,
        )

    def unarchive(self, id: str, organisation_id: int | None = None) -> control_models.Device:
        path = f"/devices/{id}/unarchive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Device:
        path = f"/devices/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='DeviceSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceSerializerDetail',
            item_schema=None,
        )

class GroupsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def archive(self, id: str, organisation_id: int | None = None) -> control_models.Group:
        path = f"/groups/{id}/archive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupSerializerDetail',
            item_schema=None,
        )

    def create(self, body: Any, organisation_id: int | None = None) -> control_models.Group:
        path = f"/groups/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='GroupSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/groups/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def roles_delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/groups/roles/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def users_delete(self, parent_lookup_group: str, user: str, organisation_id: int | None = None) -> None:
        path = f"/groups/{parent_lookup_group}/users/{user}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, archived: bool | None = None, name: str | None = None, name__contains: str | None = None, name__icontains: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, permission: str | None = None, root_group: bool | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.Group]:
        path = f"/groups/"
        params = {
            "archived": archived,
            "name": name,
            "name__contains": name__contains,
            "name__icontains": name__icontains,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "permission": permission,
            "root_group": root_group,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedGroupSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.Group:
        path = f"/groups/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedGroupSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.Group:
        path = f"/groups/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupSerializerDetail',
            item_schema=None,
        )

    def roles_create(self, body: Any, organisation_id: int | None = None) -> control_models.GroupRole:
        path = f"/groups/roles/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='GroupRoleSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupRoleSerializerDetail',
            item_schema=None,
        )

    def roles_retrieve(self, id: str, organisation_id: int | None = None) -> control_models.GroupRole:
        path = f"/groups/roles/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupRoleSerializerDetail',
            item_schema=None,
        )

    def roles_update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.GroupRole:
        path = f"/groups/roles/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='GroupRoleSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupRoleSerializerDetail',
            item_schema=None,
        )

    def roles_archive(self, id: str, organisation_id: int | None = None) -> control_models.GroupRole:
        path = f"/groups/roles/{id}/archive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupRoleSerializerDetail',
            item_schema=None,
        )

    def roles_list(self, archived: bool | None = None, id: int | None = None, name: str | None = None, name__contains: str | None = None, name__icontains: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.GroupRole]:
        path = f"/groups/roles/"
        params = {
            "archived": archived,
            "id": id,
            "name": name,
            "name__contains": name__contains,
            "name__icontains": name__icontains,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedGroupRoleSerializerListList',
            item_schema=None,
        )

    def roles_partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.GroupRole:
        path = f"/groups/roles/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedGroupRoleSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupRoleSerializerDetail',
            item_schema=None,
        )

    def roles_unarchive(self, id: str, organisation_id: int | None = None) -> control_models.GroupRole:
        path = f"/groups/roles/{id}/unarchive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupRoleSerializerDetail',
            item_schema=None,
        )

    def unarchive(self, id: str, organisation_id: int | None = None) -> control_models.Group:
        path = f"/groups/{id}/unarchive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Group:
        path = f"/groups/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='GroupSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupSerializerDetail',
            item_schema=None,
        )

    def users_create(self, parent_lookup_group: str, body: Any, organisation_id: int | None = None) -> control_models.GroupPermission:
        path = f"/groups/{parent_lookup_group}/users/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='GroupPermissionSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupPermissionSerializerDetail',
            item_schema=None,
        )

    def users_retrieve(self, parent_lookup_group: str, user: str, organisation_id: int | None = None) -> control_models.GroupPermission:
        path = f"/groups/{parent_lookup_group}/users/{user}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupPermissionSerializerDetail',
            item_schema=None,
        )

    def users_update(self, parent_lookup_group: str, user: str, body: Any, organisation_id: int | None = None) -> control_models.GroupPermission:
        path = f"/groups/{parent_lookup_group}/users/{user}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='GroupPermissionSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupPermissionSerializerDetail',
            item_schema=None,
        )

    def users_list(self, parent_lookup_group: str, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.GroupPermission]:
        path = f"/groups/{parent_lookup_group}/users/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedGroupPermissionSerializerListList',
            item_schema=None,
        )

    def users_partial(self, parent_lookup_group: str, user: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.GroupPermission:
        path = f"/groups/{parent_lookup_group}/users/{user}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedGroupPermissionSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='GroupPermissionSerializerDetail',
            item_schema=None,
        )

class IntegrationsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def archive(self, id: str, organisation_id: int | None = None) -> control_models.Integration:
        path = f"/integrations/{id}/archive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='IntegrationSerializerDetail',
            item_schema=None,
        )

    def create(self, body: Any, organisation_id: int | None = None) -> control_models.Integration:
        path = f"/integrations/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='IntegrationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='IntegrationSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/integrations/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, application: str | None = None, archived: bool | None = None, device: str | None = None, display_name: str | None = None, display_name__contains: str | None = None, display_name__icontains: str | None = None, id: int | None = None, name: str | None = None, name__contains: str | None = None, name__icontains: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, solution: str | None = None, status: str | None = None, template: str | None = None, version: str | None = None, version__contains: str | None = None, version__icontains: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.Integration]:
        path = f"/integrations/"
        params = {
            "application": application,
            "archived": archived,
            "device": device,
            "display_name": display_name,
            "display_name__contains": display_name__contains,
            "display_name__icontains": display_name__icontains,
            "id": id,
            "name": name,
            "name__contains": name__contains,
            "name__icontains": name__icontains,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "search": search,
            "solution": solution,
            "status": status,
            "template": template,
            "version": version,
            "version__contains": version__contains,
            "version__icontains": version__icontains,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedIntegrationSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.Integration:
        path = f"/integrations/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedIntegrationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='IntegrationSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.Integration:
        path = f"/integrations/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='IntegrationSerializerDetail',
            item_schema=None,
        )

    def sync_config_profiles(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Integration:
        path = f"/integrations/{id}/sync_config_profiles/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='IntegrationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='IntegrationSerializerDetail',
            item_schema=None,
        )

    def unarchive(self, id: str, organisation_id: int | None = None) -> control_models.Integration:
        path = f"/integrations/{id}/unarchive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='IntegrationSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Integration:
        path = f"/integrations/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='IntegrationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='IntegrationSerializerDetail',
            item_schema=None,
        )

class OrganisationsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    billing: OrganisationsBillingSyncGroup
    domains: OrganisationsDomainsSyncGroup
    pending_users: OrganisationsPendingUsersSyncGroup
    roles: OrganisationsRolesSyncGroup
    shared_profiles: OrganisationsSharedProfilesSyncGroup
    sharing_profiles: OrganisationsSharingProfilesSyncGroup
    users: OrganisationsUsersSyncGroup

    def archive(self, id: str, organisation_id: int | None = None) -> control_models.Organisation:
        path = f"/organisations/{id}/archive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSerializerDetail',
            item_schema=None,
        )

    def create(self, body: Any, organisation_id: int | None = None) -> control_models.Organisation:
        path = f"/organisations/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='OrganisationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, archived: bool | None = None, id: int | None = None, name: str | None = None, name__contains: str | None = None, name__icontains: str | None = None, ordering: str | None = None, page: int | None = None, per_page: int | None = None, retention_period: int | None = None, retention_period__gt: int | None = None, retention_period__gte: int | None = None, retention_period__lt: int | None = None, retention_period__lte: int | None = None, search: str | None = None, test_field_A: int | None = None, test_field_A__gt: int | None = None, test_field_A__gte: int | None = None, test_field_A__lt: int | None = None, test_field_A__lte: int | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.Organisation]:
        path = f"/organisations/"
        params = {
            "archived": archived,
            "id": id,
            "name": name,
            "name__contains": name__contains,
            "name__icontains": name__icontains,
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "retention_period": retention_period,
            "retention_period__gt": retention_period__gt,
            "retention_period__gte": retention_period__gte,
            "retention_period__lt": retention_period__lt,
            "retention_period__lte": retention_period__lte,
            "search": search,
            "test_field_A": test_field_A,
            "test_field_A__gt": test_field_A__gt,
            "test_field_A__gte": test_field_A__gte,
            "test_field_A__lt": test_field_A__lt,
            "test_field_A__lte": test_field_A__lte,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedOrganisationSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.Organisation:
        path = f"/organisations/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedOrganisationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.Organisation:
        path = f"/organisations/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSerializerDetail',
            item_schema=None,
        )

    def sync_data(self, body: Any, organisation_id: int | None = None) -> control_models.Organisation:
        path = f"/organisations/sync_data/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='OrganisationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSerializerDetail',
            item_schema=None,
        )

    def sync_data_create_2(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Organisation:
        path = f"/organisations/{id}/sync_data/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='OrganisationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSerializerDetail',
            item_schema=None,
        )

    def sync_fusion(self, body: Any, organisation_id: int | None = None) -> control_models.Organisation:
        path = f"/organisations/sync_fusion/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='OrganisationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSerializerDetail',
            item_schema=None,
        )

    def sync_fusion_create_2(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Organisation:
        path = f"/organisations/{id}/sync_fusion/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='OrganisationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSerializerDetail',
            item_schema=None,
        )

    def unarchive(self, id: str, organisation_id: int | None = None) -> control_models.Organisation:
        path = f"/organisations/{id}/unarchive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Organisation:
        path = f"/organisations/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='OrganisationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSerializerDetail',
            item_schema=None,
        )

class OrganisationsBillingSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    account: OrganisationsBillingAccountSyncGroup
    admin: OrganisationsBillingAdminSyncGroup
    agent_items: OrganisationsBillingAgentItemsSyncGroup
    app_configs: OrganisationsBillingAppConfigsSyncGroup
    device_type_configs: OrganisationsBillingDeviceTypeConfigsSyncGroup
    devices: OrganisationsBillingDevicesSyncGroup
    group: OrganisationsBillingGroupSyncGroup
    invoices: OrganisationsBillingInvoicesSyncGroup
    metering_runs: OrganisationsBillingMeteringRunsSyncGroup
    products: OrganisationsBillingProductsSyncGroup
    seller_customers: OrganisationsBillingSellerCustomersSyncGroup
    stripe: OrganisationsBillingStripeSyncGroup
    subscriptions: OrganisationsBillingSubscriptionsSyncGroup
    usage_records: OrganisationsBillingUsageRecordsSyncGroup

    def checkout(self, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/checkout/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def portal(self, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/portal/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def usage(self, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/usage/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

class OrganisationsBillingAccountSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.BillingAccount]:
        path = f"/organisations/billing/account/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedBillingAccountSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.BillingAccount:
        path = f"/organisations/billing/account/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedBillingAccountSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='BillingAccountSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.BillingAccount:
        path = f"/organisations/billing/account/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='BillingAccountSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.BillingAccount:
        path = f"/organisations/billing/account/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='BillingAccountSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='BillingAccountSerializerDetail',
            item_schema=None,
        )

class OrganisationsBillingAdminSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def group_seller_customer_overview(self, group_id: int, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/admin/group/{group_id}/seller-customer-overview/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def org(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/admin/org/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def org_invoices_pdf(self, id: str, invoice_id: str, organisation_id: int | None = None) -> bytes:
        path = f"/organisations/billing/admin/org/{id}/invoices/{invoice_id}/pdf/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="bytes",
            response_schema=None,
            item_schema=None,
        )

    def org_invoices_upcoming_pdf(self, id: str, organisation_id: int | None = None) -> bytes:
        path = f"/organisations/billing/admin/org/{id}/invoices/upcoming/pdf/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="bytes",
            response_schema=None,
            item_schema=None,
        )

    def org_meter(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/admin/org/{id}/meter/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def org_metering_mode_partial(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/admin/org/{id}/metering-mode/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def org_portal(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/admin/org/{id}/portal/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def org_resync(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/admin/org/{id}/resync/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def org_seller_account_link(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/admin/org/{id}/seller-account-link/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def org_seller_customer_overview(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/admin/org/{id}/seller-customer-overview/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def org_seller_customer_portal(self, id: str, sc_id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/admin/org/{id}/seller-customer-portal/{sc_id}/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def org_seller_overview(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/admin/org/{id}/seller-overview/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def org_setup(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/admin/org/{id}/setup/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def org_setup_seller(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/admin/org/{id}/setup-seller/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def org_setup_seller_customer(self, id: str, sc_id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/admin/org/{id}/setup-seller-customer/{sc_id}/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

class OrganisationsBillingAgentItemsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, body: Any, organisation_id: int | None = None) -> control_models.AgentBillingItem:
        path = f"/organisations/billing/agent_items/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='AgentBillingItemSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='AgentBillingItemSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/agent_items/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, billing_product: str | None = None, device: str | None = None, effective_from: str | None = None, effective_from__gte: str | None = None, effective_from__lte: str | None = None, effective_until: str | None = None, effective_until__gte: str | None = None, effective_until__isnull: bool | None = None, effective_until__lte: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.AgentBillingItem]:
        path = f"/organisations/billing/agent_items/"
        params = {
            "billing_product": billing_product,
            "device": device,
            "effective_from": effective_from,
            "effective_from__gte": effective_from__gte,
            "effective_from__lte": effective_from__lte,
            "effective_until": effective_until,
            "effective_until__gte": effective_until__gte,
            "effective_until__isnull": effective_until__isnull,
            "effective_until__lte": effective_until__lte,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedAgentBillingItemSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.AgentBillingItem:
        path = f"/organisations/billing/agent_items/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedAgentBillingItemSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='AgentBillingItemSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.AgentBillingItem:
        path = f"/organisations/billing/agent_items/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='AgentBillingItemSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.AgentBillingItem:
        path = f"/organisations/billing/agent_items/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='AgentBillingItemSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='AgentBillingItemSerializerDetail',
            item_schema=None,
        )

class OrganisationsBillingAppConfigsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, body: Any, organisation_id: int | None = None) -> control_models.AppBillingConfig:
        path = f"/organisations/billing/app_configs/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='AppBillingConfigSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='AppBillingConfigSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/app_configs/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, application: str | None = None, billable: bool | None = None, ordering: str | None = None, owner_organisation: str | None = None, owner_organisation__isnull: bool | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.AppBillingConfig]:
        path = f"/organisations/billing/app_configs/"
        params = {
            "application": application,
            "billable": billable,
            "ordering": ordering,
            "owner_organisation": owner_organisation,
            "owner_organisation__isnull": owner_organisation__isnull,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedAppBillingConfigSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.AppBillingConfig:
        path = f"/organisations/billing/app_configs/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedAppBillingConfigSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='AppBillingConfigSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.AppBillingConfig:
        path = f"/organisations/billing/app_configs/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='AppBillingConfigSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.AppBillingConfig:
        path = f"/organisations/billing/app_configs/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='AppBillingConfigSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='AppBillingConfigSerializerDetail',
            item_schema=None,
        )

class OrganisationsBillingDeviceTypeConfigsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, body: Any, organisation_id: int | None = None) -> control_models.DeviceTypeBillingConfig:
        path = f"/organisations/billing/device_type_configs/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='DeviceTypeBillingConfigSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceTypeBillingConfigSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/device_type_configs/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, billing_product: str | None = None, device_type: str | None = None, ordering: str | None = None, owner_organisation: str | None = None, owner_organisation__isnull: bool | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.DeviceTypeBillingConfig]:
        path = f"/organisations/billing/device_type_configs/"
        params = {
            "billing_product": billing_product,
            "device_type": device_type,
            "ordering": ordering,
            "owner_organisation": owner_organisation,
            "owner_organisation__isnull": owner_organisation__isnull,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedDeviceTypeBillingConfigSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.DeviceTypeBillingConfig:
        path = f"/organisations/billing/device_type_configs/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedDeviceTypeBillingConfigSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceTypeBillingConfigSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.DeviceTypeBillingConfig:
        path = f"/organisations/billing/device_type_configs/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceTypeBillingConfigSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.DeviceTypeBillingConfig:
        path = f"/organisations/billing/device_type_configs/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='DeviceTypeBillingConfigSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceTypeBillingConfigSerializerDetail',
            item_schema=None,
        )

class OrganisationsBillingDevicesSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.DeviceBillingConfig]:
        path = f"/organisations/billing/devices/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedDeviceBillingConfigSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.DeviceBillingConfig:
        path = f"/organisations/billing/devices/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedDeviceBillingConfigSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceBillingConfigSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.DeviceBillingConfig:
        path = f"/organisations/billing/devices/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='DeviceBillingConfigSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='DeviceBillingConfigSerializerDetail',
            item_schema=None,
        )

class OrganisationsBillingGroupSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def billing_create(self, group_id: int, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/group/{group_id}/billing/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def billing_retrieve(self, group_id: int, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/group/{group_id}/billing/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

class OrganisationsBillingInvoicesSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def pdf(self, id: str, organisation_id: int | None = None) -> bytes:
        path = f"/organisations/billing/invoices/{id}/pdf/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="bytes",
            response_schema=None,
            item_schema=None,
        )

    def retrieve(self, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/invoices/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def retrieve_2(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/invoices/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def upcoming_pdf(self, organisation_id: int | None = None) -> bytes:
        path = f"/organisations/billing/invoices/upcoming/pdf/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="bytes",
            response_schema=None,
            item_schema=None,
        )

class OrganisationsBillingMeteringRunsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, organisation_id: int | None = None) -> control_models.UsageMeteringRun:
        path = f"/organisations/billing/metering_runs/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='UsageMeteringRunSerializerDetail',
            item_schema=None,
        )

    def list(self, date: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, started_at__gte: str | None = None, started_at__lte: str | None = None, status: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.UsageMeteringRun]:
        path = f"/organisations/billing/metering_runs/"
        params = {
            "date": date,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "search": search,
            "started_at__gte": started_at__gte,
            "started_at__lte": started_at__lte,
            "status": status,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedUsageMeteringRunSerializerListList',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.UsageMeteringRun:
        path = f"/organisations/billing/metering_runs/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='UsageMeteringRunSerializerDetail',
            item_schema=None,
        )

class OrganisationsBillingProductsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, body: Any, organisation_id: int | None = None) -> control_models.BillingProduct:
        path = f"/organisations/billing/products/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='BillingProductSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='BillingProductSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/products/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, active: bool | None = None, app_visibility_tier: str | None = None, ordering: str | None = None, owner_organisation: str | None = None, owner_organisation__isnull: bool | None = None, page: int | None = None, per_page: int | None = None, product_type: str | None = None, search: str | None = None, stripe_account: str | None = None, stripe_account__isnull: bool | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.BillingProduct]:
        path = f"/organisations/billing/products/"
        params = {
            "active": active,
            "app_visibility_tier": app_visibility_tier,
            "ordering": ordering,
            "owner_organisation": owner_organisation,
            "owner_organisation__isnull": owner_organisation__isnull,
            "page": page,
            "per_page": per_page,
            "product_type": product_type,
            "search": search,
            "stripe_account": stripe_account,
            "stripe_account__isnull": stripe_account__isnull,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedBillingProductSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.BillingProduct:
        path = f"/organisations/billing/products/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedBillingProductSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='BillingProductSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.BillingProduct:
        path = f"/organisations/billing/products/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='BillingProductSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.BillingProduct:
        path = f"/organisations/billing/products/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='BillingProductSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='BillingProductSerializerDetail',
            item_schema=None,
        )

class OrganisationsBillingSellerCustomersSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, body: Any, organisation_id: int | None = None) -> control_models.SellerCustomer:
        path = f"/organisations/billing/seller_customers/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='SellerCustomerSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SellerCustomerSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/seller_customers/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, group: str | None = None, group__organisation: str | None = None, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, stripe_customer_id: str | None = None, stripe_customer_id__isnull: bool | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.SellerCustomer]:
        path = f"/organisations/billing/seller_customers/"
        params = {
            "group": group,
            "group__organisation": group__organisation,
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
            "stripe_customer_id": stripe_customer_id,
            "stripe_customer_id__isnull": stripe_customer_id__isnull,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedSellerCustomerSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.SellerCustomer:
        path = f"/organisations/billing/seller_customers/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedSellerCustomerSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SellerCustomerSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.SellerCustomer:
        path = f"/organisations/billing/seller_customers/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SellerCustomerSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.SellerCustomer:
        path = f"/organisations/billing/seller_customers/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='SellerCustomerSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SellerCustomerSerializerDetail',
            item_schema=None,
        )

class OrganisationsBillingStripeSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def accounts(self, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/stripe/accounts/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def products_create(self, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/stripe/products/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def products_retrieve(self, organisation_id: int | None = None) -> None:
        path = f"/organisations/billing/stripe/products/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

class OrganisationsBillingSubscriptionsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.BillingSubscription]:
        path = f"/organisations/billing/subscriptions/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedBillingSubscriptionSerializerListList',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.BillingSubscription:
        path = f"/organisations/billing/subscriptions/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='BillingSubscriptionSerializerDetail',
            item_schema=None,
        )

class OrganisationsBillingUsageRecordsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def list(self, agent_billing_item: str | None = None, billing_product: str | None = None, device_online: bool | None = None, metering_run: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, record_type: str | None = None, revenue_target: str | None = None, search: str | None = None, seller_customer: str | None = None, seller_customer__isnull: bool | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.UsageRecord]:
        path = f"/organisations/billing/usage_records/"
        params = {
            "agent_billing_item": agent_billing_item,
            "billing_product": billing_product,
            "device_online": device_online,
            "metering_run": metering_run,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "record_type": record_type,
            "revenue_target": revenue_target,
            "search": search,
            "seller_customer": seller_customer,
            "seller_customer__isnull": seller_customer__isnull,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedUsageRecordSerializerListList',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.UsageRecord:
        path = f"/organisations/billing/usage_records/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='UsageRecordSerializerDetail',
            item_schema=None,
        )

class OrganisationsDomainsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Organisation:
        path = f"/organisations/{id}/domains/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='OrganisationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: int, organisation_id: int | None = None) -> None:
        path = f"/organisations/domains/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.OrganisationDomain]:
        path = f"/organisations/domains/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedOrganisationDomainSerializerListList',
            item_schema=None,
        )

    def partial(self, id: int, body: Any | None = None, organisation_id: int | None = None) -> control_models.OrganisationDomain:
        path = f"/organisations/domains/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedOrganisationDomainSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationDomainSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: int, organisation_id: int | None = None) -> control_models.OrganisationDomain:
        path = f"/organisations/domains/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationDomainSerializerDetail',
            item_schema=None,
        )

class OrganisationsPendingUsersSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def approve(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.PendingUser:
        path = f"/organisations/pending_users/{id}/approve/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='PendingUserSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='PendingUserSerializerDetail',
            item_schema=None,
        )

    def create(self, body: Any, organisation_id: int | None = None) -> control_models.PendingUser:
        path = f"/organisations/pending_users/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='PendingUserSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='PendingUserSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/pending_users/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.PendingUser]:
        path = f"/organisations/pending_users/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedPendingUserSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.PendingUser:
        path = f"/organisations/pending_users/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedPendingUserSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='PendingUserSerializerDetail',
            item_schema=None,
        )

    def reject(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.PendingUser:
        path = f"/organisations/pending_users/{id}/reject/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='PendingUserSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='PendingUserSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.PendingUser:
        path = f"/organisations/pending_users/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='PendingUserSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.PendingUser:
        path = f"/organisations/pending_users/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='PendingUserSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='PendingUserSerializerDetail',
            item_schema=None,
        )

class OrganisationsRolesSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def archive(self, id: str, organisation_id: int | None = None) -> control_models.OrganisationRole:
        path = f"/organisations/roles/{id}/archive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationRoleSerializerDetail',
            item_schema=None,
        )

    def create(self, body: Any, organisation_id: int | None = None) -> control_models.OrganisationRole:
        path = f"/organisations/roles/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='OrganisationRoleSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationRoleSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/roles/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, archived: bool | None = None, id: int | None = None, name: str | None = None, name__contains: str | None = None, name__icontains: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.OrganisationRole]:
        path = f"/organisations/roles/"
        params = {
            "archived": archived,
            "id": id,
            "name": name,
            "name__contains": name__contains,
            "name__icontains": name__icontains,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedOrganisationRoleSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.OrganisationRole:
        path = f"/organisations/roles/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedOrganisationRoleSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationRoleSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.OrganisationRole:
        path = f"/organisations/roles/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationRoleSerializerDetail',
            item_schema=None,
        )

    def unarchive(self, id: str, organisation_id: int | None = None) -> control_models.OrganisationRole:
        path = f"/organisations/roles/{id}/unarchive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationRoleSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.OrganisationRole:
        path = f"/organisations/roles/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='OrganisationRoleSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationRoleSerializerDetail',
            item_schema=None,
        )

class OrganisationsSharedProfilesSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, body: Any, organisation_id: int | None = None) -> control_models.OrganisationSharedReceiveProfile:
        path = f"/organisations/shared_profiles/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='OrganisationSharedReceiveProfileSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSharedReceiveProfileSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/shared_profiles/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.OrganisationSharedReceiveProfile]:
        path = f"/organisations/shared_profiles/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedOrganisationSharedReceiveProfileSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.OrganisationSharedReceiveProfile:
        path = f"/organisations/shared_profiles/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedOrganisationSharedReceiveProfileSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSharedReceiveProfileSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.OrganisationSharedReceiveProfile:
        path = f"/organisations/shared_profiles/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSharedReceiveProfileSerializerDetail',
            item_schema=None,
        )

    def sharing_profile(self, id: str, organisation_id: int | None = None) -> control_models.OrganisationSharedReceiveProfile:
        path = f"/organisations/shared_profiles/{id}/sharing_profile/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSharedReceiveProfileSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.OrganisationSharedReceiveProfile:
        path = f"/organisations/shared_profiles/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='OrganisationSharedReceiveProfileSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSharedReceiveProfileSerializerDetail',
            item_schema=None,
        )

class OrganisationsSharingProfilesSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, body: Any, organisation_id: int | None = None) -> control_models.OrganisationSharingProfile:
        path = f"/organisations/sharing_profiles/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='OrganisationSharingProfileSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSharingProfileSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/sharing_profiles/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.OrganisationSharingProfile]:
        path = f"/organisations/sharing_profiles/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedOrganisationSharingProfileSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.OrganisationSharingProfile:
        path = f"/organisations/sharing_profiles/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedOrganisationSharingProfileSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSharingProfileSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.OrganisationSharingProfile:
        path = f"/organisations/sharing_profiles/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSharingProfileSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.OrganisationSharingProfile:
        path = f"/organisations/sharing_profiles/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='OrganisationSharingProfileSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationSharingProfileSerializerDetail',
            item_schema=None,
        )

class OrganisationsUsersSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, body: Any, organisation_id: int | None = None) -> control_models.OrganisationUser:
        path = f"/organisations/users/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='OrganisationUserSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationUserSerializerDetail',
            item_schema=None,
        )

    def delete(self, user: str, organisation_id: int | None = None) -> None:
        path = f"/organisations/users/{user}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def groups_list(self, parent_lookup_user: str, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.GroupPermission]:
        path = f"/organisations/users/{parent_lookup_user}/groups/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedGroupPermissionSerializerListList',
            item_schema=None,
        )

    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.OrganisationUser]:
        path = f"/organisations/users/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedOrganisationUserSerializerListList',
            item_schema=None,
        )

    def partial(self, user: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.OrganisationUser:
        path = f"/organisations/users/{user}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedOrganisationUserSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationUserSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, user: str, organisation_id: int | None = None) -> control_models.OrganisationUser:
        path = f"/organisations/users/{user}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationUserSerializerDetail',
            item_schema=None,
        )

    def update(self, user: str, body: Any, organisation_id: int | None = None) -> control_models.OrganisationUser:
        path = f"/organisations/users/{user}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='OrganisationUserSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='OrganisationUserSerializerDetail',
            item_schema=None,
        )

class PermissionsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def sync(self, organisation_id: int | None = None) -> None:
        path = f"/permissions/sync"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

class ReportsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, body: Any, organisation_id: int | None = None) -> control_models.Report:
        path = f"/reports/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='ReportCreateSerialiserDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ReportSerialiserDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/reports/schedules/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, organisation_id: int | None = None) -> list[control_models.Report]:
        path = f"/reports/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="list_model",
            response_schema=None,
            item_schema='ReportSerialiserList',
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.Report:
        path = f"/reports/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ReportSerialiserDetail',
            item_schema=None,
        )

    def schedules_create(self, body: Any, organisation_id: int | None = None) -> control_models.ReportSchedule:
        path = f"/reports/schedules/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='ReportScheduleSerialiserDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ReportScheduleSerialiserDetail',
            item_schema=None,
        )

    def schedules_retrieve(self, id: str, organisation_id: int | None = None) -> control_models.ReportSchedule:
        path = f"/reports/schedules/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ReportScheduleSerialiserDetail',
            item_schema=None,
        )

    def schedules_update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.ReportSchedule:
        path = f"/reports/schedules/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='ReportScheduleSerialiserDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ReportScheduleSerialiserDetail',
            item_schema=None,
        )

    def schedules_archive(self, id: str, organisation_id: int | None = None) -> control_models.ReportSchedule:
        path = f"/reports/schedules/{id}/archive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ReportScheduleSerialiserDetail',
            item_schema=None,
        )

    def schedules_list(self, application: str | None = None, archived: bool | None = None, display_name: str | None = None, display_name__contains: str | None = None, display_name__icontains: str | None = None, id: int | None = None, name: str | None = None, name__contains: str | None = None, name__icontains: str | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, status: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.ReportSchedule]:
        path = f"/reports/schedules/"
        params = {
            "application": application,
            "archived": archived,
            "display_name": display_name,
            "display_name__contains": display_name__contains,
            "display_name__icontains": display_name__icontains,
            "id": id,
            "name": name,
            "name__contains": name__contains,
            "name__icontains": name__icontains,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "search": search,
            "status": status,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedReportScheduleSerialiserListList',
            item_schema=None,
        )

    def schedules_partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.ReportSchedule:
        path = f"/reports/schedules/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedReportScheduleSerialiserDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ReportScheduleSerialiserDetail',
            item_schema=None,
        )

    def schedules_unarchive(self, id: str, organisation_id: int | None = None) -> control_models.ReportSchedule:
        path = f"/reports/schedules/{id}/unarchive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ReportScheduleSerialiserDetail',
            item_schema=None,
        )

class SharedDevicesSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, body: Any, organisation_id: int | None = None) -> control_models.SharedDevice:
        path = f"/shared_devices/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='SharedDeviceSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SharedDeviceSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/shared_devices/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.SharedDevice]:
        path = f"/shared_devices/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedSharedDeviceSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.SharedDevice:
        path = f"/shared_devices/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedSharedDeviceSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SharedDeviceSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.SharedDevice:
        path = f"/shared_devices/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SharedDeviceSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.SharedDevice:
        path = f"/shared_devices/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='SharedDeviceSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SharedDeviceSerializerDetail',
            item_schema=None,
        )

class SharedGroupsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, body: Any, organisation_id: int | None = None) -> control_models.SharedGroup:
        path = f"/shared_groups/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='SharedGroupSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SharedGroupSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/shared_groups/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.SharedGroup]:
        path = f"/shared_groups/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedSharedGroupSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.SharedGroup:
        path = f"/shared_groups/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedSharedGroupSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SharedGroupSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.SharedGroup:
        path = f"/shared_groups/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SharedGroupSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.SharedGroup:
        path = f"/shared_groups/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='SharedGroupSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SharedGroupSerializerDetail',
            item_schema=None,
        )

class SiteSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def retrieve(self, hostname: str | None = None, organisation_id: int | None = None) -> control_models.CustomerSite:
        path = f"/site/"
        params = {
            "hostname": hostname,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='CustomerSiteSerializerDetail',
            item_schema=None,
        )

class SolutionInstallsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def create(self, body: Any, organisation_id: int | None = None) -> control_models.SolutionInstallation:
        path = f"/solution_installs/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='SolutionInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionInstallationSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/solution_installs/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def deploy(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.SolutionInstallation:
        path = f"/solution_installs/{id}/deploy/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='SolutionInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionInstallationSerializerDetail',
            item_schema=None,
        )

    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.SolutionInstallation]:
        path = f"/solution_installs/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedSolutionInstallationSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.SolutionInstallation:
        path = f"/solution_installs/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedSolutionInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionInstallationSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.SolutionInstallation:
        path = f"/solution_installs/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionInstallationSerializerDetail',
            item_schema=None,
        )

    def sync(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.SolutionInstallation:
        path = f"/solution_installs/{id}/sync/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='SolutionInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionInstallationSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.SolutionInstallation:
        path = f"/solution_installs/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='SolutionInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionInstallationSerializerDetail',
            item_schema=None,
        )

class SolutionsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def application_templates_create(self, parent_lookup_solution: str, body: Any, organisation_id: int | None = None) -> control_models.ApplicationTemplate:
        path = f"/solutions/{parent_lookup_solution}/application_templates/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='ApplicationTemplateSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationTemplateSerializerDetail',
            item_schema=None,
        )

    def application_templates_retrieve(self, id: str, parent_lookup_solution: str, organisation_id: int | None = None) -> control_models.ApplicationTemplate:
        path = f"/solutions/{parent_lookup_solution}/application_templates/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationTemplateSerializerDetail',
            item_schema=None,
        )

    def application_templates_update(self, id: str, parent_lookup_solution: str, body: Any, organisation_id: int | None = None) -> control_models.ApplicationTemplate:
        path = f"/solutions/{parent_lookup_solution}/application_templates/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='ApplicationTemplateSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationTemplateSerializerDetail',
            item_schema=None,
        )

    def application_templates_list(self, parent_lookup_solution: str, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.ApplicationTemplate]:
        path = f"/solutions/{parent_lookup_solution}/application_templates/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedApplicationTemplateSerializerListList',
            item_schema=None,
        )

    def application_templates_partial(self, id: str, parent_lookup_solution: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.ApplicationTemplate:
        path = f"/solutions/{parent_lookup_solution}/application_templates/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedApplicationTemplateSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ApplicationTemplateSerializerDetail',
            item_schema=None,
        )

    def archive(self, id: str, organisation_id: int | None = None) -> control_models.Solution:
        path = f"/solutions/{id}/archive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionSerializerDetail',
            item_schema=None,
        )

    def create(self, body: Any, organisation_id: int | None = None) -> control_models.Solution:
        path = f"/solutions/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='SolutionSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, parent_lookup_solution: str, organisation_id: int | None = None) -> None:
        path = f"/solutions/{parent_lookup_solution}/application_templates/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def installs_deploy(self, id: str, parent_lookup_solution: str, body: Any, organisation_id: int | None = None) -> control_models.SolutionInstallation:
        path = f"/solutions/{parent_lookup_solution}/installs/{id}/deploy/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='SolutionInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionInstallationSerializerDetail',
            item_schema=None,
        )

    def installs_list(self, parent_lookup_solution: str, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.SolutionInstallation]:
        path = f"/solutions/{parent_lookup_solution}/installs/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedSolutionInstallationSerializerListList',
            item_schema=None,
        )

    def installs_sync(self, id: str, parent_lookup_solution: str, body: Any, organisation_id: int | None = None) -> control_models.SolutionInstallation:
        path = f"/solutions/{parent_lookup_solution}/installs/{id}/sync/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='SolutionInstallationSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionInstallationSerializerDetail',
            item_schema=None,
        )

    def list(self, archived: bool | None = None, description: str | None = None, description__contains: str | None = None, description__icontains: str | None = None, display_name: str | None = None, display_name__contains: str | None = None, display_name__icontains: str | None = None, id: int | None = None, ordering: str | None = None, organisation: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.Solution]:
        path = f"/solutions/"
        params = {
            "archived": archived,
            "description": description,
            "description__contains": description__contains,
            "description__icontains": description__icontains,
            "display_name": display_name,
            "display_name__contains": display_name__contains,
            "display_name__icontains": display_name__icontains,
            "id": id,
            "ordering": ordering,
            "organisation": organisation,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedSolutionSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.Solution:
        path = f"/solutions/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedSolutionSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.Solution:
        path = f"/solutions/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionSerializerDetail',
            item_schema=None,
        )

    def unarchive(self, id: str, organisation_id: int | None = None) -> control_models.Solution:
        path = f"/solutions/{id}/unarchive/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Solution:
        path = f"/solutions/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='SolutionSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='SolutionSerializerDetail',
            item_schema=None,
        )

class ThemesSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.Theme]:
        path = f"/themes/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedThemeSerializerWithIdListList',
            item_schema=None,
        )

    def partial(self, organisation: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.Theme:
        path = f"/themes/{organisation}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedThemeSerializerWithIdDetailRequest',
            body_mode="multipart",
            binary_fields=['banner_image', 'login_banner', 'sidebar_banner_image', 'site_logo'],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ThemeSerializerWithIdDetail',
            item_schema=None,
        )

    def retrieve(self, organisation: str, organisation_id: int | None = None) -> control_models.Theme:
        path = f"/themes/{organisation}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ThemeSerializerWithIdDetail',
            item_schema=None,
        )

    def update(self, organisation: str, body: Any, organisation_id: int | None = None) -> control_models.Theme:
        path = f"/themes/{organisation}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='ThemeSerializerWithIdDetailRequest',
            body_mode="multipart",
            binary_fields=['banner_image', 'login_banner', 'sidebar_banner_image', 'site_logo'],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='ThemeSerializerWithIdDetail',
            item_schema=None,
        )

class TunnelsSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def activate(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Tunnel:
        path = f"/tunnels/{id}/activate/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='TunnelSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='TunnelSerializerDetail',
            item_schema=None,
        )

    def create(self, body: Any, organisation_id: int | None = None) -> control_models.Tunnel:
        path = f"/tunnels/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='TunnelSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='TunnelSerializerDetail',
            item_schema=None,
        )

    def deactivate(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Tunnel:
        path = f"/tunnels/{id}/deactivate/"
        params = None
        return self._root._execute(
            "POST",
            path,
            params=params,
            body=body,
            body_schema='TunnelSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='TunnelSerializerDetail',
            item_schema=None,
        )

    def delete(self, id: str, organisation_id: int | None = None) -> None:
        path = f"/tunnels/{id}/"
        params = None
        return self._root._execute(
            "DELETE",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.Tunnel]:
        path = f"/tunnels/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedTunnelSerializerListList',
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.Tunnel:
        path = f"/tunnels/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedTunnelSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='TunnelSerializerDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.Tunnel:
        path = f"/tunnels/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='TunnelSerializerDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any, organisation_id: int | None = None) -> control_models.Tunnel:
        path = f"/tunnels/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='TunnelSerializerDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='TunnelSerializerDetail',
            item_schema=None,
        )

class UsersSyncGroup(_ControlGroupBase[_SyncControlExecutor]):
    def list(self, ordering: str | None = None, page: int | None = None, per_page: int | None = None, search: str | None = None, organisation_id: int | None = None) -> control_models.ControlPage[control_models.User]:
        path = f"/users/"
        params = {
            "ordering": ordering,
            "page": page,
            "per_page": per_page,
            "search": search,
        }
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="page",
            response_schema='PaginatedUserSerialiserListList',
            item_schema=None,
        )

    def me(self, organisation_id: int | None = None) -> None:
        path = f"/users/me/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="none",
            response_schema=None,
            item_schema=None,
        )

    def partial(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.User:
        path = f"/users/{id}/"
        params = None
        return self._root._execute(
            "PATCH",
            path,
            params=params,
            body=body,
            body_schema='PatchedUserSerialiserDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='UserSerialiserDetail',
            item_schema=None,
        )

    def retrieve(self, id: str, organisation_id: int | None = None) -> control_models.User:
        path = f"/users/{id}/"
        params = None
        return self._root._execute(
            "GET",
            path,
            params=params,
            body=None,
            body_schema=None,
            body_mode="json",
            binary_fields=None,
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='UserSerialiserDetail',
            item_schema=None,
        )

    def update(self, id: str, body: Any | None = None, organisation_id: int | None = None) -> control_models.User:
        path = f"/users/{id}/"
        params = None
        return self._root._execute(
            "PUT",
            path,
            params=params,
            body=body,
            body_schema='UserSerialiserDetailRequest',
            body_mode="json",
            binary_fields=[],
            organisation_id=organisation_id,
            response_kind="model",
            response_schema='UserSerialiserDetail',
            item_schema=None,
        )

def _attach_sync_groups(root: ControlClientGroups):
    root.agents = AgentsSyncGroup(root)
    root.analytics = AnalyticsSyncGroup(root)
    root.app_deployments = AppDeploymentsSyncGroup(root)
    root.app_installs = AppInstallsSyncGroup(root)
    root.applications = ApplicationsSyncGroup(root)
    root.assistant = AssistantSyncGroup(root)
    root.container = ContainerSyncGroup(root)
    root.container.registry = ContainerRegistrySyncGroup(root)
    root.devices = DevicesSyncGroup(root)
    root.groups = GroupsSyncGroup(root)
    root.integrations = IntegrationsSyncGroup(root)
    root.organisations = OrganisationsSyncGroup(root)
    root.organisations.billing = OrganisationsBillingSyncGroup(root)
    root.organisations.billing.account = OrganisationsBillingAccountSyncGroup(root)
    root.organisations.billing.admin = OrganisationsBillingAdminSyncGroup(root)
    root.organisations.billing.agent_items = OrganisationsBillingAgentItemsSyncGroup(root)
    root.organisations.billing.app_configs = OrganisationsBillingAppConfigsSyncGroup(root)
    root.organisations.billing.device_type_configs = OrganisationsBillingDeviceTypeConfigsSyncGroup(root)
    root.organisations.billing.devices = OrganisationsBillingDevicesSyncGroup(root)
    root.organisations.billing.group = OrganisationsBillingGroupSyncGroup(root)
    root.organisations.billing.invoices = OrganisationsBillingInvoicesSyncGroup(root)
    root.organisations.billing.metering_runs = OrganisationsBillingMeteringRunsSyncGroup(root)
    root.organisations.billing.products = OrganisationsBillingProductsSyncGroup(root)
    root.organisations.billing.seller_customers = OrganisationsBillingSellerCustomersSyncGroup(root)
    root.organisations.billing.stripe = OrganisationsBillingStripeSyncGroup(root)
    root.organisations.billing.subscriptions = OrganisationsBillingSubscriptionsSyncGroup(root)
    root.organisations.billing.usage_records = OrganisationsBillingUsageRecordsSyncGroup(root)
    root.organisations.domains = OrganisationsDomainsSyncGroup(root)
    root.organisations.pending_users = OrganisationsPendingUsersSyncGroup(root)
    root.organisations.roles = OrganisationsRolesSyncGroup(root)
    root.organisations.shared_profiles = OrganisationsSharedProfilesSyncGroup(root)
    root.organisations.sharing_profiles = OrganisationsSharingProfilesSyncGroup(root)
    root.organisations.users = OrganisationsUsersSyncGroup(root)
    root.permissions = PermissionsSyncGroup(root)
    root.reports = ReportsSyncGroup(root)
    root.shared_devices = SharedDevicesSyncGroup(root)
    root.shared_groups = SharedGroupsSyncGroup(root)
    root.site = SiteSyncGroup(root)
    root.solution_installs = SolutionInstallsSyncGroup(root)
    root.solutions = SolutionsSyncGroup(root)
    root.themes = ThemesSyncGroup(root)
    root.tunnels = TunnelsSyncGroup(root)
    root.users = UsersSyncGroup(root)

OPERATION_COUNT = 299

__all__ = [
    "ControlClientGroups",
    "_attach_sync_groups",
    "OPERATION_COUNT",
    "AgentsSyncGroup",
    "AnalyticsSyncGroup",
    "AppDeploymentsSyncGroup",
    "AppInstallsSyncGroup",
    "ApplicationsSyncGroup",
    "AssistantSyncGroup",
    "ContainerSyncGroup",
    "ContainerRegistrySyncGroup",
    "DevicesSyncGroup",
    "GroupsSyncGroup",
    "IntegrationsSyncGroup",
    "OrganisationsSyncGroup",
    "OrganisationsBillingSyncGroup",
    "OrganisationsBillingAccountSyncGroup",
    "OrganisationsBillingAdminSyncGroup",
    "OrganisationsBillingAgentItemsSyncGroup",
    "OrganisationsBillingAppConfigsSyncGroup",
    "OrganisationsBillingDeviceTypeConfigsSyncGroup",
    "OrganisationsBillingDevicesSyncGroup",
    "OrganisationsBillingGroupSyncGroup",
    "OrganisationsBillingInvoicesSyncGroup",
    "OrganisationsBillingMeteringRunsSyncGroup",
    "OrganisationsBillingProductsSyncGroup",
    "OrganisationsBillingSellerCustomersSyncGroup",
    "OrganisationsBillingStripeSyncGroup",
    "OrganisationsBillingSubscriptionsSyncGroup",
    "OrganisationsBillingUsageRecordsSyncGroup",
    "OrganisationsDomainsSyncGroup",
    "OrganisationsPendingUsersSyncGroup",
    "OrganisationsRolesSyncGroup",
    "OrganisationsSharedProfilesSyncGroup",
    "OrganisationsSharingProfilesSyncGroup",
    "OrganisationsUsersSyncGroup",
    "PermissionsSyncGroup",
    "ReportsSyncGroup",
    "SharedDevicesSyncGroup",
    "SharedGroupsSyncGroup",
    "SiteSyncGroup",
    "SolutionInstallsSyncGroup",
    "SolutionsSyncGroup",
    "ThemesSyncGroup",
    "TunnelsSyncGroup",
    "UsersSyncGroup",
]

