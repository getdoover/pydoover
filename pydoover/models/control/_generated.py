from __future__ import annotations

from typing import Any

from ._base import ControlField, ControlModel, ObjectFieldType


class Location(ObjectFieldType):
    latitude: float
    longitude: float
    def __init__(
        self,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> None:
        super().__init__(
            latitude=latitude,
            longitude=longitude,
        )
    _structure = {
        "latitude": ControlField(type="float", nullable=False),
        "longitude": ControlField(type="float", nullable=False),
    }

class AIChatMessage(ControlModel):
    _model_name = "AIChatMessage"
    id: int
    session: str
    created_at: str
    user_message: str
    assistant_response: str
    tokens_input: int
    tokens_output: int
    gatekeeper_stopped: bool
    recursion_depth: int
    tools_used: Any
    actions_returned: Any
    navigation_context: Any
    debug_log: str
    def __init__(
        self,
        *,
        id: int | None = None,
        session: str | None = None,
        created_at: str | None = None,
        user_message: str | None = None,
        assistant_response: str | None = None,
        tokens_input: int | None = None,
        tokens_output: int | None = None,
        gatekeeper_stopped: bool | None = None,
        recursion_depth: int | None = None,
        tools_used: Any | None = None,
        actions_returned: Any | None = None,
        navigation_context: Any | None = None,
        debug_log: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            session=session,
            created_at=created_at,
            user_message=user_message,
            assistant_response=assistant_response,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            gatekeeper_stopped=gatekeeper_stopped,
            recursion_depth=recursion_depth,
            tools_used=tools_used,
            actions_returned=actions_returned,
            navigation_context=navigation_context,
            debug_log=debug_log,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "session": ControlField(type="string", nullable=False),
        "created_at": ControlField(type="string", nullable=False),
        "user_message": ControlField(type="string", nullable=False),
        "assistant_response": ControlField(type="string", nullable=False),
        "tokens_input": ControlField(type="integer", nullable=False),
        "tokens_output": ControlField(type="integer", nullable=False),
        "gatekeeper_stopped": ControlField(type="boolean", nullable=False),
        "recursion_depth": ControlField(type="integer", nullable=False),
        "tools_used": ControlField(type="json", nullable=False),
        "actions_returned": ControlField(type="json", nullable=False),
        "navigation_context": ControlField(type="json", nullable=False),
        "debug_log": ControlField(type="string", nullable=False),
    }
    _versions = {
        "AIChatMessageSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "session": {'required': True},
                "created_at": {'required': True},
                "user_message": {'required': True},
                "assistant_response": {'required': True},
                "tokens_input": {'required': True},
                "tokens_output": {'required': True},
                "gatekeeper_stopped": {'required': True},
                "recursion_depth": {'required': True},
                "tools_used": {'required': True},
                "actions_returned": {'required': True},
                "navigation_context": {'required': True},
                "debug_log": {'required': True},
            },
        },
        "AIChatMessageSerializerList": {
            "fields": {
                "id": {'required': True},
                "session": {'required': True},
                "created_at": {'required': True},
                "user_message": {'required': True},
                "assistant_response": {'required': True},
                "tokens_input": {'required': True},
                "tokens_output": {'required': True},
                "gatekeeper_stopped": {'required': True},
                "recursion_depth": {'required': True},
                "tools_used": {'required': True},
                "actions_returned": {'required': True},
                "navigation_context": {'required': True},
                "debug_log": {'required': True},
            },
        },
    }

class AIChatSession(ControlModel):
    _model_name = "AIChatSession"
    id: int
    session_key: str
    user: User
    organisation: Organisation
    created_at: str
    last_message_at: str
    total_tokens_input: int
    total_tokens_output: int
    gatekeeper_count: int
    max_recursion_depth: int
    tools_used: Any
    message_count: str
    message_history: Any
    messages: list[AIChatMessage]
    def __init__(
        self,
        *,
        id: int | None = None,
        session_key: str | None = None,
        user: User | dict[str, Any] | str | int | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        created_at: str | None = None,
        last_message_at: str | None = None,
        total_tokens_input: int | None = None,
        total_tokens_output: int | None = None,
        gatekeeper_count: int | None = None,
        max_recursion_depth: int | None = None,
        tools_used: Any | None = None,
        message_count: str | None = None,
        message_history: Any | None = None,
        messages: list[AIChatMessage | dict[str, Any] | str | int] | None = None,
    ) -> None:
        super().__init__(
            id=id,
            session_key=session_key,
            user=user,
            organisation=organisation,
            created_at=created_at,
            last_message_at=last_message_at,
            total_tokens_input=total_tokens_input,
            total_tokens_output=total_tokens_output,
            gatekeeper_count=gatekeeper_count,
            max_recursion_depth=max_recursion_depth,
            tools_used=tools_used,
            message_count=message_count,
            message_history=message_history,
            messages=messages,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "session_key": ControlField(type="string", nullable=False),
        "user": ControlField(type="resource", nullable=False, ref="User"),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
        "created_at": ControlField(type="string", nullable=False),
        "last_message_at": ControlField(type="string", nullable=False),
        "total_tokens_input": ControlField(type="integer", nullable=False),
        "total_tokens_output": ControlField(type="integer", nullable=False),
        "gatekeeper_count": ControlField(type="integer", nullable=False),
        "max_recursion_depth": ControlField(type="integer", nullable=False),
        "tools_used": ControlField(type="json", nullable=False),
        "message_count": ControlField(type="string", nullable=False),
        "message_history": ControlField(type="json", nullable=False),
        "messages": ControlField(type="resource", nullable=False, is_array=True, ref="AIChatMessage"),
    }
    _versions = {
        "AIChatSessionDetailSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "session_key": {'required': True},
                "user": {'required': True, 'version': 'UserBasicSerializerDetail'},
                "organisation": {'required': True, 'version': 'OrganisationBasicSerializerDetail'},
                "created_at": {'required': True},
                "last_message_at": {'required': True},
                "total_tokens_input": {'required': True},
                "total_tokens_output": {'required': True},
                "gatekeeper_count": {'required': True},
                "max_recursion_depth": {'required': True},
                "tools_used": {'required': True},
                "message_count": {'required': True},
                "message_history": {},
                "messages": {'required': True, 'version': 'AIChatMessageSerializerDetail'},
            },
        },
        "AIChatSessionSerializerList": {
            "fields": {
                "id": {'required': True},
                "session_key": {'required': True},
                "user": {'required': True, 'version': 'UserBasicSerializerList'},
                "organisation": {'required': True, 'version': 'OrganisationBasicSerializerList'},
                "created_at": {'required': True},
                "last_message_at": {'required': True},
                "total_tokens_input": {'required': True},
                "total_tokens_output": {'required': True},
                "gatekeeper_count": {'required': True},
                "max_recursion_depth": {'required': True},
                "tools_used": {'required': True},
                "message_count": {'required': True},
            },
        },
    }

class AgentBillingItem(ControlModel):
    _model_name = "AgentBillingItem"
    id: int
    billing_product: AgentItemProduct
    device: AgentItemDevice | None
    organisation: AgentItemOrg | None
    effective_from: str
    effective_until: str | None
    notes: str
    created_at: str
    updated_at: str
    def __init__(
        self,
        *,
        id: int | None = None,
        billing_product: AgentItemProduct | dict[str, Any] | str | int | None = None,
        device: AgentItemDevice | dict[str, Any] | str | int | None = None,
        organisation: AgentItemOrg | dict[str, Any] | str | int | None = None,
        effective_from: str | None = None,
        effective_until: str | None = None,
        notes: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            billing_product=billing_product,
            device=device,
            organisation=organisation,
            effective_from=effective_from,
            effective_until=effective_until,
            notes=notes,
            created_at=created_at,
            updated_at=updated_at,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "billing_product": ControlField(type="resource", nullable=False, ref="AgentItemProduct"),
        "device": ControlField(type="resource", nullable=True, ref="AgentItemDevice"),
        "organisation": ControlField(type="resource", nullable=True, ref="AgentItemOrg"),
        "effective_from": ControlField(type="string", nullable=False),
        "effective_until": ControlField(type="string", nullable=True),
        "notes": ControlField(type="string", nullable=False),
        "created_at": ControlField(type="string", nullable=False),
        "updated_at": ControlField(type="string", nullable=False),
    }
    _versions = {
        "AgentBillingItemSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "billing_product": {'required': True, 'version': 'AgentItemProductSerializerDetail'},
                "device": {'required': True, 'version': 'AgentItemDeviceSerializerDetail'},
                "organisation": {'required': True, 'version': 'AgentItemOrgSerializerDetail'},
                "effective_from": {'required': True},
                "effective_until": {},
                "notes": {},
                "created_at": {'required': True},
                "updated_at": {'required': True},
            },
        },
        "AgentBillingItemSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "billing_product": {'required': True, 'output_id': 'billing_product_id'},
                "device": {'output_id': 'device_id'},
                "organisation": {'output_id': 'organisation_id'},
                "effective_from": {'required': True},
                "effective_until": {},
                "notes": {},
            },
        },
        "AgentBillingItemSerializerList": {
            "fields": {
                "id": {'required': True},
                "billing_product": {'required': True, 'version': 'AgentItemProductSerializerList'},
                "device": {'required': True, 'version': 'AgentItemDeviceSerializerList'},
                "organisation": {'required': True, 'version': 'AgentItemOrgSerializerList'},
                "effective_from": {'required': True},
                "effective_until": {},
                "notes": {},
                "created_at": {'required': True},
                "updated_at": {'required': True},
            },
        },
        "PatchedAgentBillingItemSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "billing_product": {'output_id': 'billing_product_id'},
                "device": {'output_id': 'device_id'},
                "organisation": {'output_id': 'organisation_id'},
                "effective_from": {},
                "effective_until": {},
                "notes": {},
            },
        },
    }

class AgentItemDevice(ControlModel):
    _model_name = "AgentItemDevice"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "AgentItemDeviceSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "AgentItemDeviceSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class AgentItemOrg(ControlModel):
    _model_name = "AgentItemOrg"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "AgentItemOrgSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "AgentItemOrgSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class AgentItemProduct(ControlModel):
    _model_name = "AgentItemProduct"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "AgentItemProductSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "AgentItemProductSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class AppBillingConfig(ControlModel):
    _model_name = "AppBillingConfig"
    id: int
    application: AppBillingConfigApp
    billable: bool
    billing_product: AppBillingConfigProduct | None
    owner_organisation: AppBillingConfigOwnerOrg | None
    created_at: str
    updated_at: str
    def __init__(
        self,
        *,
        id: int | None = None,
        application: AppBillingConfigApp | dict[str, Any] | str | int | None = None,
        billable: bool | None = None,
        billing_product: AppBillingConfigProduct | dict[str, Any] | str | int | None = None,
        owner_organisation: AppBillingConfigOwnerOrg | dict[str, Any] | str | int | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            application=application,
            billable=billable,
            billing_product=billing_product,
            owner_organisation=owner_organisation,
            created_at=created_at,
            updated_at=updated_at,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "application": ControlField(type="resource", nullable=False, ref="AppBillingConfigApp"),
        "billable": ControlField(type="boolean", nullable=False),
        "billing_product": ControlField(type="resource", nullable=True, ref="AppBillingConfigProduct"),
        "owner_organisation": ControlField(type="resource", nullable=True, ref="AppBillingConfigOwnerOrg"),
        "created_at": ControlField(type="string", nullable=False),
        "updated_at": ControlField(type="string", nullable=False),
    }
    _versions = {
        "AppBillingConfigSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "application": {'required': True, 'version': 'AppBillingConfigAppSerializerDetail'},
                "billable": {},
                "billing_product": {'required': True, 'version': 'AppBillingConfigProductSerializerDetail'},
                "owner_organisation": {'required': True, 'version': 'AppBillingConfigOwnerOrgSerializerDetail'},
                "created_at": {'required': True},
                "updated_at": {'required': True},
            },
        },
        "AppBillingConfigSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "application": {'required': True, 'output_id': 'application_id'},
                "billable": {},
                "billing_product": {'output_id': 'billing_product_id'},
                "owner_organisation": {'output_id': 'owner_organisation_id'},
            },
        },
        "AppBillingConfigSerializerList": {
            "fields": {
                "id": {'required': True},
                "application": {'required': True, 'version': 'AppBillingConfigAppSerializerList'},
                "billable": {},
                "billing_product": {'required': True, 'version': 'AppBillingConfigProductSerializerList'},
                "owner_organisation": {'required': True, 'version': 'AppBillingConfigOwnerOrgSerializerList'},
                "created_at": {'required': True},
                "updated_at": {'required': True},
            },
        },
        "PatchedAppBillingConfigSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "application": {'output_id': 'application_id'},
                "billable": {},
                "billing_product": {'output_id': 'billing_product_id'},
                "owner_organisation": {'output_id': 'owner_organisation_id'},
            },
        },
    }

class AppBillingConfigApp(ControlModel):
    _model_name = "AppBillingConfigApp"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "AppBillingConfigAppSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "AppBillingConfigAppSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class AppBillingConfigOwnerOrg(ControlModel):
    _model_name = "AppBillingConfigOwnerOrg"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "AppBillingConfigOwnerOrgSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "AppBillingConfigOwnerOrgSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class AppBillingConfigProduct(ControlModel):
    _model_name = "AppBillingConfigProduct"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "AppBillingConfigProductSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "AppBillingConfigProductSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class Application(ControlModel):
    _model_name = "Application"
    id: int
    archived: bool
    name: str
    display_name: str
    description: str
    long_description: str
    type: str
    visibility: str
    allow_many: bool
    config_schema: Any
    depends_on: list[str]
    organisation: Organisation | None
    approx_installs: int
    stars: int
    container_registry_profile: ContainerRegistry | None
    deployment_data: str | None
    image_name: str | None
    lambda_arn: str | None
    lambda_config: Any
    config_profiles: list[ApplicationConfigProfile]
    icon_url: str | None
    banner_url: str | None
    def __init__(
        self,
        *,
        id: int | None = None,
        archived: bool | None = None,
        name: str | None = None,
        display_name: str | None = None,
        description: str | None = None,
        long_description: str | None = None,
        type: str | None = None,
        visibility: str | None = None,
        allow_many: bool | None = None,
        config_schema: Any | None = None,
        depends_on: list[str] | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        approx_installs: int | None = None,
        stars: int | None = None,
        container_registry_profile: ContainerRegistry | dict[str, Any] | str | int | None = None,
        deployment_data: str | None = None,
        image_name: str | None = None,
        lambda_arn: str | None = None,
        lambda_config: Any | None = None,
        config_profiles: list[ApplicationConfigProfile | dict[str, Any] | str | int] | None = None,
        icon_url: str | None = None,
        banner_url: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            archived=archived,
            name=name,
            display_name=display_name,
            description=description,
            long_description=long_description,
            type=type,
            visibility=visibility,
            allow_many=allow_many,
            config_schema=config_schema,
            depends_on=depends_on,
            organisation=organisation,
            approx_installs=approx_installs,
            stars=stars,
            container_registry_profile=container_registry_profile,
            deployment_data=deployment_data,
            image_name=image_name,
            lambda_arn=lambda_arn,
            lambda_config=lambda_config,
            config_profiles=config_profiles,
            icon_url=icon_url,
            banner_url=banner_url,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "archived": ControlField(type="boolean", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "display_name": ControlField(type="string", nullable=False),
        "description": ControlField(type="string", nullable=False),
        "long_description": ControlField(type="string", nullable=False),
        "type": ControlField(type="string", nullable=False),
        "visibility": ControlField(type="string", nullable=False),
        "allow_many": ControlField(type="boolean", nullable=False),
        "config_schema": ControlField(type="json", nullable=False),
        "depends_on": ControlField(type="string", nullable=False, is_array=True),
        "organisation": ControlField(type="resource", nullable=True, ref="Organisation"),
        "approx_installs": ControlField(type="integer", nullable=False),
        "stars": ControlField(type="integer", nullable=False),
        "container_registry_profile": ControlField(type="resource", nullable=True, ref="ContainerRegistry"),
        "deployment_data": ControlField(type="string", nullable=True),
        "image_name": ControlField(type="string", nullable=True),
        "lambda_arn": ControlField(type="string", nullable=True),
        "lambda_config": ControlField(type="json", nullable=False),
        "config_profiles": ControlField(type="resource", nullable=False, is_array=True, ref="ApplicationConfigProfile"),
        "icon_url": ControlField(type="string", nullable=True),
        "banner_url": ControlField(type="string", nullable=True),
    }
    _versions = {
        "ApplicationSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "archived": {'required': True},
                "name": {'required': True},
                "display_name": {'required': True},
                "description": {'required': True},
                "long_description": {},
                "type": {'required': True},
                "visibility": {'required': True},
                "allow_many": {},
                "config_schema": {},
                "depends_on": {'required': True},
                "organisation": {'required': True, 'version': 'BasicOrganisationDetail'},
                "approx_installs": {'required': True},
                "stars": {},
                "container_registry_profile": {'required': True, 'version': 'SlimContainerRegistryDetail'},
                "deployment_data": {},
                "image_name": {},
                "lambda_arn": {},
                "lambda_config": {},
                "config_profiles": {'required': True, 'version': 'SlimApplicationConfigProfileSerializerDetail'},
                "icon_url": {},
                "banner_url": {},
            },
        },
        "ApplicationSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "name": {'required': True},
                "display_name": {'required': True},
                "description": {'required': True},
                "long_description": {},
                "type": {'required': True},
                "visibility": {'required': True},
                "allow_many": {},
                "config_schema": {},
                "depends_on": {'required': True},
                "organisation": {'required': True, 'output_id': 'organisation_id'},
                "stars": {},
                "container_registry_profile": {'required': True, 'output_id': 'container_registry_profile_id'},
                "deployment_data": {},
                "image_name": {},
                "lambda_arn": {},
                "lambda_config": {},
                "icon_url": {},
                "banner_url": {},
            },
        },
        "ApplicationSerializerList": {
            "fields": {
                "id": {'required': True},
                "archived": {'required': True},
                "name": {'required': True},
                "display_name": {'required': True},
                "description": {'required': True},
                "long_description": {},
                "type": {'required': True},
                "visibility": {'required': True},
                "allow_many": {},
                "config_schema": {},
                "depends_on": {'required': True},
                "organisation": {'required': True, 'version': 'BasicOrganisationList'},
                "approx_installs": {'required': True},
                "stars": {},
                "container_registry_profile": {'required': True, 'version': 'SlimContainerRegistryList'},
                "deployment_data": {},
                "image_name": {},
                "lambda_arn": {},
                "lambda_config": {},
                "config_profiles": {'required': True, 'version': 'SlimApplicationConfigProfileSerializerList'},
                "icon_url": {},
                "banner_url": {},
            },
        },
        "PatchedApplicationSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "name": {},
                "display_name": {},
                "description": {},
                "long_description": {},
                "type": {},
                "visibility": {},
                "allow_many": {},
                "config_schema": {},
                "depends_on": {},
                "organisation": {'output_id': 'organisation_id'},
                "stars": {},
                "container_registry_profile": {'output_id': 'container_registry_profile_id'},
                "deployment_data": {},
                "image_name": {},
                "lambda_arn": {},
                "lambda_config": {},
                "icon_url": {},
                "banner_url": {},
            },
        },
        "PublicApplicationSerializerList": {
            "fields": {
                "id": {'required': True},
                "archived": {'required': True},
                "name": {'required': True},
                "display_name": {'required': True},
                "description": {'required': True},
                "long_description": {'required': True},
                "type": {'required': True},
                "visibility": {'required': True},
                "allow_many": {'required': True},
                "config_schema": {'required': True},
                "approx_installs": {'required': True},
                "stars": {'required': True},
                "image_name": {'required': True},
                "depends_on": {'required': True},
                "icon_url": {'required': True},
                "banner_url": {'required': True},
            },
        },
        "SlimApplicationDetail": {
            "fields": {
                "id": {'required': True},
                "archived": {'required': True},
                "name": {'required': True},
                "type": {'required': True},
                "display_name": {'required': True},
                "description": {'required': True},
                "depends_on": {'required': True},
                "config_schema": {'required': True},
                "organisation": {'required': True, 'version': 'BasicOrganisationDetail'},
                "icon_url": {'required': True},
                "banner_url": {'required': True},
            },
        },
        "SlimApplicationList": {
            "fields": {
                "id": {'required': True},
                "archived": {'required': True},
                "name": {'required': True},
                "type": {'required': True},
                "display_name": {'required': True},
                "description": {'required': True},
                "depends_on": {'required': True},
                "config_schema": {'required': True},
                "organisation": {'required': True, 'version': 'BasicOrganisationList'},
                "icon_url": {'required': True},
                "banner_url": {'required': True},
            },
        },
    }

class ApplicationConfigProfile(ControlModel):
    _model_name = "ApplicationConfigProfile"
    id: int
    organisation: Organisation | None
    display_name: str
    description: str
    deployment_config: Any
    application: Application
    def __init__(
        self,
        *,
        id: int | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        display_name: str | None = None,
        description: str | None = None,
        deployment_config: Any | None = None,
        application: Application | dict[str, Any] | str | int | None = None,
    ) -> None:
        super().__init__(
            id=id,
            organisation=organisation,
            display_name=display_name,
            description=description,
            deployment_config=deployment_config,
            application=application,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "organisation": ControlField(type="resource", nullable=True, ref="Organisation"),
        "display_name": ControlField(type="string", nullable=False),
        "description": ControlField(type="string", nullable=False),
        "deployment_config": ControlField(type="json", nullable=False),
        "application": ControlField(type="resource", nullable=False, ref="Application"),
    }
    _versions = {
        "ApplicationConfigProfileSerializerDetail": {
            "fields": {
                "id": {},
                "organisation": {'required': True, 'version': 'BasicOrganisationDetail'},
                "display_name": {'required': True},
                "description": {},
                "deployment_config": {},
                "application": {'required': True, 'version': 'ApplicationSerializerDetail'},
            },
        },
        "ApplicationConfigProfileSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "id": {},
                "display_name": {'required': True},
                "description": {},
                "deployment_config": {},
                "application": {'required': True, 'output_id': 'application_id'},
            },
        },
        "ApplicationConfigProfileSerializerList": {
            "fields": {
                "id": {},
                "organisation": {'required': True, 'version': 'BasicOrganisationList'},
                "display_name": {'required': True},
                "description": {},
                "deployment_config": {},
                "application": {'required': True, 'version': 'ApplicationSerializerList'},
            },
        },
        "PatchedApplicationConfigProfileSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "id": {},
                "display_name": {},
                "description": {},
                "deployment_config": {},
                "application": {'output_id': 'application_id'},
            },
        },
        "SlimApplicationConfigProfileSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "organisation": {},
                "display_name": {'required': True},
                "description": {},
                "application": {'required': True},
                "deployment_config": {},
            },
        },
        "SlimApplicationConfigProfileSerializerDetailRequest": {
            "fields": {
                "organisation": {},
                "display_name": {'required': True},
                "description": {},
                "deployment_config": {},
            },
        },
        "SlimApplicationConfigProfileSerializerList": {
            "fields": {
                "id": {'required': True},
                "organisation": {},
                "display_name": {'required': True},
                "description": {},
                "application": {'required': True},
                "deployment_config": {},
            },
        },
    }

class ApplicationDeployment(ControlModel):
    _model_name = "ApplicationDeployment"
    id: int
    app_install: str
    status: str
    created_at: str
    log_output: str
    deployment_config: Any
    docker_message_id: str
    def __init__(
        self,
        *,
        id: int | None = None,
        app_install: str | None = None,
        status: str | None = None,
        created_at: str | None = None,
        log_output: str | None = None,
        deployment_config: Any | None = None,
        docker_message_id: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            app_install=app_install,
            status=status,
            created_at=created_at,
            log_output=log_output,
            deployment_config=deployment_config,
            docker_message_id=docker_message_id,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "app_install": ControlField(type="string", nullable=False),
        "status": ControlField(type="string", nullable=False),
        "created_at": ControlField(type="string", nullable=False),
        "log_output": ControlField(type="string", nullable=False),
        "deployment_config": ControlField(type="json", nullable=False),
        "docker_message_id": ControlField(type="id", nullable=False),
    }
    _versions = {
        "ApplicationDeploymentSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "app_install": {'required': True},
                "status": {'required': True},
                "created_at": {'required': True},
                "log_output": {'required': True},
                "deployment_config": {'required': True},
                "docker_message_id": {'required': True},
            },
        },
        "ApplicationDeploymentSerializerDetailRequest": {
            "methods": ['POST'],
            "fields": {
                "app_install": {'required': True},
                "docker_message_id": {'required': True},
            },
        },
        "ApplicationDeploymentSerializerList": {
            "fields": {
                "id": {'required': True},
                "app_install": {'required': True},
                "status": {'required': True},
                "created_at": {'required': True},
                "log_output": {'required': True},
                "deployment_config": {'required': True},
                "docker_message_id": {'required': True},
            },
        },
    }

class ApplicationInstallation(ControlModel):
    _model_name = "ApplicationInstallation"
    id: int
    archived: bool
    name: str
    display_name: str
    application: Application
    organisation: Organisation
    device: Device | None
    version: str | None
    managed_by: list[str]
    deployment_config: Any
    latest_deployment: ApplicationDeployment
    pre_archive_latest_deployment: str
    config_profiles: list[ApplicationConfigProfile]
    solution_id: str | None
    template: ApplicationTemplate
    def __init__(
        self,
        *,
        id: int | None = None,
        archived: bool | None = None,
        name: str | None = None,
        display_name: str | None = None,
        application: Application | dict[str, Any] | str | int | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        device: Device | dict[str, Any] | str | int | None = None,
        version: str | None = None,
        managed_by: list[str] | None = None,
        deployment_config: Any | None = None,
        latest_deployment: ApplicationDeployment | dict[str, Any] | str | int | None = None,
        pre_archive_latest_deployment: str | None = None,
        config_profiles: list[ApplicationConfigProfile | dict[str, Any] | str | int] | None = None,
        solution_id: str | None = None,
        template: ApplicationTemplate | dict[str, Any] | str | int | None = None,
    ) -> None:
        super().__init__(
            id=id,
            archived=archived,
            name=name,
            display_name=display_name,
            application=application,
            organisation=organisation,
            device=device,
            version=version,
            managed_by=managed_by,
            deployment_config=deployment_config,
            latest_deployment=latest_deployment,
            pre_archive_latest_deployment=pre_archive_latest_deployment,
            config_profiles=config_profiles,
            solution_id=solution_id,
            template=template,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "archived": ControlField(type="boolean", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "display_name": ControlField(type="string", nullable=False),
        "application": ControlField(type="resource", nullable=False, ref="Application"),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
        "device": ControlField(type="resource", nullable=True, ref="Device"),
        "version": ControlField(type="string", nullable=True),
        "managed_by": ControlField(type="string", nullable=False, is_array=True),
        "deployment_config": ControlField(type="json", nullable=False),
        "latest_deployment": ControlField(type="resource", nullable=False, ref="ApplicationDeployment"),
        "pre_archive_latest_deployment": ControlField(type="string", nullable=False),
        "config_profiles": ControlField(type="resource", nullable=False, is_array=True, ref="ApplicationConfigProfile"),
        "solution_id": ControlField(type="id", nullable=True),
        "template": ControlField(type="resource", nullable=False, ref="ApplicationTemplate"),
    }
    _versions = {
        "ApplicationInstallationSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "archived": {'required': True},
                "name": {},
                "display_name": {'required': True},
                "application": {'required': True, 'version': 'SlimApplicationDetail'},
                "organisation": {'required': True, 'version': 'BasicOrganisationDetail'},
                "device": {'required': True, 'version': 'DeviceSuperBasicSerialiserDetail'},
                "version": {},
                "managed_by": {'required': True},
                "deployment_config": {},
                "latest_deployment": {'required': True, 'version': 'ApplicationDeploymentSerializerDetail'},
                "pre_archive_latest_deployment": {'required': True},
                "config_profiles": {'required': True, 'version': 'SlimApplicationConfigProfileSerializerDetail'},
                "solution_id": {},
                "template": {'required': True, 'version': 'ApplicationTemplateSerializerDetail'},
            },
        },
        "ApplicationInstallationSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "name": {},
                "display_name": {'required': True},
                "application": {'required': True, 'output_id': 'application_id'},
                "device": {'required': True, 'output_id': 'device_id'},
                "version": {},
                "deployment_config": {},
                "config_profiles": {'output_id': 'config_profile_ids'},
                "solution_id": {},
            },
        },
        "ApplicationInstallationSerializerList": {
            "fields": {
                "id": {'required': True},
                "archived": {'required': True},
                "name": {},
                "display_name": {'required': True},
                "application": {'required': True, 'version': 'SlimApplicationList'},
                "organisation": {'required': True, 'version': 'BasicOrganisationList'},
                "device": {'required': True, 'version': 'DeviceSuperBasicSerialiserList'},
                "version": {},
                "managed_by": {'required': True},
                "deployment_config": {},
                "latest_deployment": {'required': True, 'version': 'ApplicationDeploymentSerializerList'},
                "pre_archive_latest_deployment": {'required': True},
                "config_profiles": {'required': True, 'version': 'SlimApplicationConfigProfileSerializerList'},
                "solution_id": {},
                "template": {'required': True, 'version': 'ApplicationTemplateSerializerList'},
            },
        },
        "PatchedApplicationInstallationSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "name": {},
                "display_name": {},
                "application": {'output_id': 'application_id'},
                "device": {'output_id': 'device_id'},
                "version": {},
                "deployment_config": {},
                "config_profiles": {'output_id': 'config_profile_ids'},
                "solution_id": {},
            },
        },
    }

class ApplicationTemplate(ControlModel):
    _model_name = "ApplicationTemplate"
    id: int
    name: str
    display_name: str
    description: str
    application: Application
    deployment_config: Any
    synced: bool
    config_profiles: list[ApplicationConfigProfile]
    solution_id: str | None
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        display_name: str | None = None,
        description: str | None = None,
        application: Application | dict[str, Any] | str | int | None = None,
        deployment_config: Any | None = None,
        synced: bool | None = None,
        config_profiles: list[ApplicationConfigProfile | dict[str, Any] | str | int] | None = None,
        solution_id: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            display_name=display_name,
            description=description,
            application=application,
            deployment_config=deployment_config,
            synced=synced,
            config_profiles=config_profiles,
            solution_id=solution_id,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "display_name": ControlField(type="string", nullable=False),
        "description": ControlField(type="string", nullable=False),
        "application": ControlField(type="resource", nullable=False, ref="Application"),
        "deployment_config": ControlField(type="json", nullable=False),
        "synced": ControlField(type="boolean", nullable=False),
        "config_profiles": ControlField(type="resource", nullable=False, is_array=True, ref="ApplicationConfigProfile"),
        "solution_id": ControlField(type="id", nullable=True),
    }
    _versions = {
        "ApplicationTemplateSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {},
                "display_name": {'required': True},
                "description": {},
                "application": {'required': True, 'version': 'ApplicationSerializerDetail'},
                "deployment_config": {},
                "synced": {},
                "config_profiles": {'required': True, 'version': 'ApplicationConfigProfileSerializerDetail'},
            },
        },
        "ApplicationTemplateSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "name": {},
                "display_name": {'required': True},
                "description": {},
                "application": {'required': True, 'output_id': 'application_id'},
                "deployment_config": {},
                "synced": {},
                "config_profiles": {'output_id': 'config_profile_ids'},
                "solution_id": {'required': True},
            },
        },
        "ApplicationTemplateSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {},
                "display_name": {'required': True},
                "description": {},
                "application": {'required': True, 'version': 'ApplicationSerializerList'},
                "deployment_config": {},
                "synced": {},
                "config_profiles": {'required': True, 'version': 'ApplicationConfigProfileSerializerList'},
            },
        },
        "PatchedApplicationTemplateSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "name": {},
                "display_name": {},
                "description": {},
                "application": {'output_id': 'application_id'},
                "deployment_config": {},
                "synced": {},
                "config_profiles": {'output_id': 'config_profile_ids'},
                "solution_id": {},
            },
        },
    }

class Attachment(ControlModel):
    _model_name = "Attachment"
    filename: str
    content_type: str
    size: int
    url: str
    def __init__(
        self,
        *,
        filename: str | None = None,
        content_type: str | None = None,
        size: int | None = None,
        url: str | None = None,
    ) -> None:
        super().__init__(
            filename=filename,
            content_type=content_type,
            size=size,
            url=url,
        )
    _field_defs = {
        "filename": ControlField(type="string", nullable=False),
        "content_type": ControlField(type="string", nullable=False),
        "size": ControlField(type="integer", nullable=False),
        "url": ControlField(type="string", nullable=False),
    }
    _versions = {
        "AttachmentSerializerDetail": {
            "fields": {
                "filename": {'required': True},
                "content_type": {'required': True},
                "size": {'required': True},
                "url": {'required': True},
            },
        },
        "AttachmentSerializerList": {
            "fields": {
                "filename": {'required': True},
                "content_type": {'required': True},
                "size": {'required': True},
                "url": {'required': True},
            },
        },
    }

class BillingAccount(ControlModel):
    _model_name = "BillingAccount"
    id: int
    organisation: str
    stripe_customer_id: str | None
    billing_email: str | None
    metering_mode: str
    created_at: str
    updated_at: str
    def __init__(
        self,
        *,
        id: int | None = None,
        organisation: str | None = None,
        stripe_customer_id: str | None = None,
        billing_email: str | None = None,
        metering_mode: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            organisation=organisation,
            stripe_customer_id=stripe_customer_id,
            billing_email=billing_email,
            metering_mode=metering_mode,
            created_at=created_at,
            updated_at=updated_at,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "organisation": ControlField(type="string", nullable=False),
        "stripe_customer_id": ControlField(type="id", nullable=True),
        "billing_email": ControlField(type="string", nullable=True),
        "metering_mode": ControlField(type="string", nullable=False),
        "created_at": ControlField(type="string", nullable=False),
        "updated_at": ControlField(type="string", nullable=False),
    }
    _versions = {
        "BillingAccountSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "organisation": {'required': True},
                "stripe_customer_id": {'required': True},
                "billing_email": {},
                "metering_mode": {},
                "created_at": {'required': True},
                "updated_at": {'required': True},
            },
        },
        "BillingAccountSerializerDetailRequest": {
            "methods": ['PUT'],
            "fields": {
                "billing_email": {},
                "metering_mode": {},
            },
        },
        "BillingAccountSerializerList": {
            "fields": {
                "id": {'required': True},
                "organisation": {'required': True},
                "stripe_customer_id": {'required': True},
                "billing_email": {},
                "metering_mode": {},
                "created_at": {'required': True},
                "updated_at": {'required': True},
            },
        },
        "PatchedBillingAccountSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "billing_email": {},
                "metering_mode": {},
            },
        },
    }

class BillingProduct(ControlModel):
    _model_name = "BillingProduct"
    id: int
    name: str
    description: str
    stripe_product_id: str
    offline_stripe_product_id: str | None
    stripe_account: str | None
    product_type: str
    app_visibility_tier: str | None
    owner_organisation: BillingProductOrg | None
    active: bool
    created_at: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        description: str | None = None,
        stripe_product_id: str | None = None,
        offline_stripe_product_id: str | None = None,
        stripe_account: str | None = None,
        product_type: str | None = None,
        app_visibility_tier: str | None = None,
        owner_organisation: BillingProductOrg | dict[str, Any] | str | int | None = None,
        active: bool | None = None,
        created_at: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            description=description,
            stripe_product_id=stripe_product_id,
            offline_stripe_product_id=offline_stripe_product_id,
            stripe_account=stripe_account,
            product_type=product_type,
            app_visibility_tier=app_visibility_tier,
            owner_organisation=owner_organisation,
            active=active,
            created_at=created_at,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "description": ControlField(type="string", nullable=False),
        "stripe_product_id": ControlField(type="id", nullable=False),
        "offline_stripe_product_id": ControlField(type="id", nullable=True),
        "stripe_account": ControlField(type="string", nullable=True),
        "product_type": ControlField(type="string", nullable=False),
        "app_visibility_tier": ControlField(type="string", nullable=True),
        "owner_organisation": ControlField(type="resource", nullable=True, ref="BillingProductOrg"),
        "active": ControlField(type="boolean", nullable=False),
        "created_at": ControlField(type="string", nullable=False),
    }
    _versions = {
        "BillingProductSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "description": {},
                "stripe_product_id": {'required': True},
                "offline_stripe_product_id": {},
                "stripe_account": {},
                "product_type": {'required': True},
                "app_visibility_tier": {},
                "owner_organisation": {'required': True, 'version': 'BillingProductOrgSerializerDetail'},
                "active": {},
                "created_at": {'required': True},
            },
        },
        "BillingProductSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "name": {'required': True},
                "description": {},
                "stripe_product_id": {'required': True},
                "offline_stripe_product_id": {},
                "stripe_account": {},
                "product_type": {'required': True},
                "app_visibility_tier": {},
                "owner_organisation": {'output_id': 'owner_organisation_id'},
                "active": {},
            },
        },
        "BillingProductSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "product_type": {'required': True},
                "app_visibility_tier": {},
                "active": {},
            },
        },
        "PatchedBillingProductSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "name": {},
                "description": {},
                "stripe_product_id": {},
                "offline_stripe_product_id": {},
                "stripe_account": {},
                "product_type": {},
                "app_visibility_tier": {},
                "owner_organisation": {'output_id': 'owner_organisation_id'},
                "active": {},
            },
        },
    }

class BillingProductOrg(ControlModel):
    _model_name = "BillingProductOrg"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "BillingProductOrgSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class BillingSubscription(ControlModel):
    _model_name = "BillingSubscription"
    id: int
    billing_account: str
    stripe_subscription_id: str
    status: str
    current_period_start: str | None
    current_period_end: str | None
    items: list[BillingSubscriptionItem]
    created_at: str
    updated_at: str
    def __init__(
        self,
        *,
        id: int | None = None,
        billing_account: str | None = None,
        stripe_subscription_id: str | None = None,
        status: str | None = None,
        current_period_start: str | None = None,
        current_period_end: str | None = None,
        items: list[BillingSubscriptionItem | dict[str, Any] | str | int] | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            billing_account=billing_account,
            stripe_subscription_id=stripe_subscription_id,
            status=status,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            items=items,
            created_at=created_at,
            updated_at=updated_at,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "billing_account": ControlField(type="string", nullable=False),
        "stripe_subscription_id": ControlField(type="id", nullable=False),
        "status": ControlField(type="string", nullable=False),
        "current_period_start": ControlField(type="string", nullable=True),
        "current_period_end": ControlField(type="string", nullable=True),
        "items": ControlField(type="resource", nullable=False, is_array=True, ref="BillingSubscriptionItem"),
        "created_at": ControlField(type="string", nullable=False),
        "updated_at": ControlField(type="string", nullable=False),
    }
    _versions = {
        "BillingSubscriptionSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "billing_account": {'required': True},
                "stripe_subscription_id": {'required': True},
                "status": {'required': True},
                "current_period_start": {'required': True},
                "current_period_end": {'required': True},
                "items": {'required': True, 'version': 'BillingSubscriptionItemSerializerDetail'},
                "created_at": {'required': True},
                "updated_at": {'required': True},
            },
        },
        "BillingSubscriptionSerializerList": {
            "fields": {
                "id": {'required': True},
                "stripe_subscription_id": {'required': True},
                "status": {'required': True},
                "current_period_start": {'required': True},
                "current_period_end": {'required': True},
                "created_at": {'required': True},
            },
        },
    }

class BillingSubscriptionItem(ControlModel):
    _model_name = "BillingSubscriptionItem"
    id: int
    billing_product: BillingProduct
    stripe_subscription_item_id: str
    stripe_product_id: str | None
    is_offline: str
    created_at: str
    def __init__(
        self,
        *,
        id: int | None = None,
        billing_product: BillingProduct | dict[str, Any] | str | int | None = None,
        stripe_subscription_item_id: str | None = None,
        stripe_product_id: str | None = None,
        is_offline: str | None = None,
        created_at: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            billing_product=billing_product,
            stripe_subscription_item_id=stripe_subscription_item_id,
            stripe_product_id=stripe_product_id,
            is_offline=is_offline,
            created_at=created_at,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "billing_product": ControlField(type="resource", nullable=False, ref="BillingProduct"),
        "stripe_subscription_item_id": ControlField(type="id", nullable=False),
        "stripe_product_id": ControlField(type="id", nullable=True),
        "is_offline": ControlField(type="string", nullable=False),
        "created_at": ControlField(type="string", nullable=False),
    }
    _versions = {
        "BillingSubscriptionItemSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "billing_product": {'required': True, 'version': 'BillingProductSerializerDetail'},
                "stripe_subscription_item_id": {'required': True},
                "stripe_product_id": {},
                "is_offline": {'required': True},
                "created_at": {'required': True},
            },
        },
    }

class ContainerRegistry(ControlModel):
    _model_name = "ContainerRegistry"
    id: int
    name: str
    description: str
    archived: bool
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        description: str | None = None,
        archived: bool | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            description=description,
            archived=archived,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "description": ControlField(type="string", nullable=False),
        "archived": ControlField(type="boolean", nullable=False),
    }
    _versions = {
        "SlimContainerRegistryDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "description": {'required': True},
                "archived": {'required': True},
            },
        },
        "SlimContainerRegistryList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "description": {'required': True},
                "archived": {'required': True},
            },
        },
    }

class ContainerRegistryProfile(ControlModel):
    _model_name = "ContainerRegistryProfile"
    id: int
    organisation: Organisation
    archived: bool
    name: str
    description: str
    url: str
    username: str
    password: str
    def __init__(
        self,
        *,
        id: int | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        archived: bool | None = None,
        name: str | None = None,
        description: str | None = None,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            organisation=organisation,
            archived=archived,
            name=name,
            description=description,
            url=url,
            username=username,
            password=password,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
        "archived": ControlField(type="boolean", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "description": ControlField(type="string", nullable=False),
        "url": ControlField(type="string", nullable=False),
        "username": ControlField(type="string", nullable=False),
        "password": ControlField(type="string", nullable=False),
    }
    _versions = {
        "ContainerRegistryProfileSeraliserDetail": {
            "fields": {
                "id": {'required': True},
                "organisation": {'required': True, 'version': 'BasicOrganisationDetail'},
                "archived": {'required': True},
                "name": {'required': True},
                "description": {'required': True},
                "url": {'required': True},
                "username": {'required': True},
                "password": {'required': True},
            },
        },
        "ContainerRegistryProfileSeraliserDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "name": {'required': True},
                "description": {'required': True},
                "url": {'required': True},
                "username": {'required': True},
                "password": {'required': True},
            },
        },
        "ContainerRegistryProfileSeraliserList": {
            "fields": {
                "id": {'required': True},
                "organisation": {'required': True, 'version': 'BasicOrganisationList'},
                "archived": {'required': True},
                "name": {'required': True},
                "description": {'required': True},
            },
        },
        "PatchedContainerRegistryProfileSeraliserDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "name": {},
                "description": {},
                "url": {},
                "username": {},
                "password": {},
            },
        },
    }

class CustomerSite(ControlModel):
    _model_name = "CustomerSite"
    name: str
    application_id: str
    id: int
    theme: Theme
    archived: bool
    def __init__(
        self,
        *,
        name: str | None = None,
        application_id: str | None = None,
        id: int | None = None,
        theme: Theme | dict[str, Any] | str | int | None = None,
        archived: bool | None = None,
    ) -> None:
        super().__init__(
            name=name,
            application_id=application_id,
            id=id,
            theme=theme,
            archived=archived,
        )
    _field_defs = {
        "name": ControlField(type="string", nullable=False),
        "application_id": ControlField(type="id", nullable=False),
        "id": ControlField(type="SnowflakeId", nullable=False),
        "theme": ControlField(type="resource", nullable=False, ref="Theme"),
        "archived": ControlField(type="boolean", nullable=False),
    }
    _versions = {
        "CustomerSiteSerializerDetail": {
            "fields": {
                "name": {'required': True},
                "application_id": {'required': True},
                "id": {'required': True},
                "theme": {'required': True, 'version': 'ThemeSerializerDetail'},
                "archived": {'required': True},
            },
        },
    }

class DTBillingConfigDeviceType(ControlModel):
    _model_name = "DTBillingConfigDeviceType"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "DTBillingConfigDeviceTypeSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "DTBillingConfigDeviceTypeSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class DTBillingConfigOwnerOrg(ControlModel):
    _model_name = "DTBillingConfigOwnerOrg"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "DTBillingConfigOwnerOrgSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "DTBillingConfigOwnerOrgSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class DTBillingConfigProduct(ControlModel):
    _model_name = "DTBillingConfigProduct"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "DTBillingConfigProductSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "DTBillingConfigProductSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class Device(ControlModel):
    _model_name = "Device"
    id: int
    archived: bool
    name: str
    display_name: str
    type: DeviceType
    organisation: Organisation
    group: Group
    fa_icon: str | None
    notes: str | None
    extra_config: Any
    fusion_entity_id: str | None
    fusion_entity_secret: str | None
    fixed_location: Location | None
    solution_config: Any
    def __init__(
        self,
        *,
        id: int | None = None,
        archived: bool | None = None,
        name: str | None = None,
        display_name: str | None = None,
        type: DeviceType | dict[str, Any] | str | int | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        group: Group | dict[str, Any] | str | int | None = None,
        fa_icon: str | None = None,
        notes: str | None = None,
        extra_config: Any | None = None,
        fusion_entity_id: str | None = None,
        fusion_entity_secret: str | None = None,
        fixed_location: Location | dict[str, Any] | None = None,
        solution_config: Any | None = None,
    ) -> None:
        super().__init__(
            id=id,
            archived=archived,
            name=name,
            display_name=display_name,
            type=type,
            organisation=organisation,
            group=group,
            fa_icon=fa_icon,
            notes=notes,
            extra_config=extra_config,
            fusion_entity_id=fusion_entity_id,
            fusion_entity_secret=fusion_entity_secret,
            fixed_location=fixed_location,
            solution_config=solution_config,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "archived": ControlField(type="boolean", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "display_name": ControlField(type="string", nullable=False),
        "type": ControlField(type="resource", nullable=False, ref="DeviceType"),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
        "group": ControlField(type="resource", nullable=False, ref="Group"),
        "fa_icon": ControlField(type="string", nullable=True),
        "notes": ControlField(type="string", nullable=True),
        "extra_config": ControlField(type="json", nullable=False),
        "fusion_entity_id": ControlField(type="id", nullable=True),
        "fusion_entity_secret": ControlField(type="string", nullable=True),
        "fixed_location": ControlField(type="Location", nullable=True),
        "solution_config": ControlField(type="json", nullable=False),
    }
    _versions = {
        "DeviceSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "archived": {'required': True},
                "name": {},
                "display_name": {'required': True},
                "type": {'required': True, 'version': 'DeviceTypeSerializerDetail'},
                "organisation": {'required': True, 'version': 'BasicOrganisationDetail'},
                "group": {'required': True, 'version': 'GroupSerializerDetail'},
                "fa_icon": {},
                "notes": {},
                "extra_config": {},
                "fusion_entity_id": {'required': True},
                "fusion_entity_secret": {'required': True},
                "fixed_location": {},
            },
        },
        "DeviceSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "name": {},
                "display_name": {'required': True},
                "type": {'required': True, 'output_id': 'type_id'},
                "group": {'required': True, 'output_id': 'group_id'},
                "fa_icon": {},
                "notes": {},
                "extra_config": {},
                "fixed_location": {},
                "solution_config": {},
            },
        },
        "DeviceSerializerList": {
            "fields": {
                "id": {'required': True},
                "archived": {'required': True},
                "name": {},
                "display_name": {'required': True},
                "type": {'required': True, 'version': 'DeviceTypeSerializerList'},
                "organisation": {'required': True, 'version': 'BasicOrganisationList'},
                "group": {'required': True, 'version': 'GroupSerializerList'},
                "fa_icon": {},
                "notes": {},
                "extra_config": {},
                "fusion_entity_id": {'required': True},
                "fusion_entity_secret": {'required': True},
                "fixed_location": {},
            },
        },
        "DeviceSuperBasicSerialiserDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "DeviceSuperBasicSerialiserList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "PatchedDeviceSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "name": {},
                "display_name": {},
                "type": {'output_id': 'type_id'},
                "group": {'output_id': 'group_id'},
                "fa_icon": {},
                "notes": {},
                "extra_config": {},
                "fixed_location": {},
                "solution_config": {},
            },
        },
    }

class DeviceBillingConfig(ControlModel):
    _model_name = "DeviceBillingConfig"
    id: int
    device: str
    device_name: str
    billing_mode: str
    created_at: str
    updated_at: str
    def __init__(
        self,
        *,
        id: int | None = None,
        device: str | None = None,
        device_name: str | None = None,
        billing_mode: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            device=device,
            device_name=device_name,
            billing_mode=billing_mode,
            created_at=created_at,
            updated_at=updated_at,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "device": ControlField(type="string", nullable=False),
        "device_name": ControlField(type="string", nullable=False),
        "billing_mode": ControlField(type="string", nullable=False),
        "created_at": ControlField(type="string", nullable=False),
        "updated_at": ControlField(type="string", nullable=False),
    }
    _versions = {
        "DeviceBillingConfigSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "device": {'required': True},
                "device_name": {'required': True},
                "billing_mode": {},
                "created_at": {'required': True},
                "updated_at": {'required': True},
            },
        },
        "DeviceBillingConfigSerializerDetailRequest": {
            "methods": ['PUT'],
            "fields": {
                "billing_mode": {},
            },
        },
        "DeviceBillingConfigSerializerList": {
            "fields": {
                "id": {'required': True},
                "device": {'required': True},
                "device_name": {'required': True},
                "billing_mode": {},
                "created_at": {'required': True},
                "updated_at": {'required': True},
            },
        },
        "PatchedDeviceBillingConfigSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "billing_mode": {},
            },
        },
    }

class DeviceType(ControlModel):
    _model_name = "DeviceType"
    id: int
    organisation: Organisation
    archived: bool
    name: str
    config: Any
    config_schema: Any
    device_extra_config_schema: Any
    installer: str | None
    installer_info: str
    copy_command: str
    description: str
    logo_url: str | None
    extra_info: str | None
    stars: int
    default_icon: str | None
    solution: Solution | None
    def __init__(
        self,
        *,
        id: int | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        archived: bool | None = None,
        name: str | None = None,
        config: Any | None = None,
        config_schema: Any | None = None,
        device_extra_config_schema: Any | None = None,
        installer: str | None = None,
        installer_info: str | None = None,
        copy_command: str | None = None,
        description: str | None = None,
        logo_url: str | None = None,
        extra_info: str | None = None,
        stars: int | None = None,
        default_icon: str | None = None,
        solution: Solution | dict[str, Any] | str | int | None = None,
    ) -> None:
        super().__init__(
            id=id,
            organisation=organisation,
            archived=archived,
            name=name,
            config=config,
            config_schema=config_schema,
            device_extra_config_schema=device_extra_config_schema,
            installer=installer,
            installer_info=installer_info,
            copy_command=copy_command,
            description=description,
            logo_url=logo_url,
            extra_info=extra_info,
            stars=stars,
            default_icon=default_icon,
            solution=solution,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
        "archived": ControlField(type="boolean", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "config": ControlField(type="json", nullable=False),
        "config_schema": ControlField(type="json", nullable=False),
        "device_extra_config_schema": ControlField(type="json", nullable=False),
        "installer": ControlField(type="string", nullable=True),
        "installer_info": ControlField(type="string", nullable=False),
        "copy_command": ControlField(type="string", nullable=False),
        "description": ControlField(type="string", nullable=False),
        "logo_url": ControlField(type="string", nullable=True),
        "extra_info": ControlField(type="string", nullable=True),
        "stars": ControlField(type="integer", nullable=False),
        "default_icon": ControlField(type="string", nullable=True),
        "solution": ControlField(type="resource", nullable=True, ref="Solution"),
    }
    _versions = {
        "DeviceTypeSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "organisation": {'required': True, 'version': 'BasicOrganisationDetail'},
                "archived": {'required': True},
                "name": {'required': True},
                "config": {},
                "config_schema": {},
                "device_extra_config_schema": {},
                "installer": {},
                "installer_info": {},
                "copy_command": {},
                "description": {},
                "logo_url": {},
                "extra_info": {},
                "stars": {},
                "default_icon": {},
                "solution": {'required': True, 'version': 'SolutionSerializerDetail'},
            },
        },
        "DeviceTypeSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "name": {'required': True},
                "config": {},
                "config_schema": {},
                "device_extra_config_schema": {},
                "installer": {},
                "installer_info": {},
                "copy_command": {},
                "description": {},
                "logo_url": {},
                "extra_info": {},
                "stars": {},
                "default_icon": {},
                "solution": {'required': True, 'output_id': 'solution_id'},
            },
        },
        "DeviceTypeSerializerList": {
            "fields": {
                "id": {'required': True},
                "organisation": {'required': True, 'version': 'BasicOrganisationList'},
                "archived": {'required': True},
                "name": {'required': True},
                "config": {},
                "config_schema": {},
                "device_extra_config_schema": {},
                "installer": {},
                "installer_info": {},
                "copy_command": {},
                "description": {},
                "logo_url": {},
                "extra_info": {},
                "stars": {},
                "default_icon": {},
                "solution": {'required': True, 'version': 'SolutionSerializerList'},
            },
        },
        "PatchedDeviceTypeSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "name": {},
                "config": {},
                "config_schema": {},
                "device_extra_config_schema": {},
                "installer": {},
                "installer_info": {},
                "copy_command": {},
                "description": {},
                "logo_url": {},
                "extra_info": {},
                "stars": {},
                "default_icon": {},
                "solution": {'output_id': 'solution_id'},
            },
        },
    }

class DeviceTypeBillingConfig(ControlModel):
    _model_name = "DeviceTypeBillingConfig"
    id: int
    device_type: DTBillingConfigDeviceType
    billing_product: DTBillingConfigProduct | None
    online_lookback_hours: int | None
    owner_organisation: DTBillingConfigOwnerOrg | None
    created_at: str
    updated_at: str
    def __init__(
        self,
        *,
        id: int | None = None,
        device_type: DTBillingConfigDeviceType | dict[str, Any] | str | int | None = None,
        billing_product: DTBillingConfigProduct | dict[str, Any] | str | int | None = None,
        online_lookback_hours: int | None = None,
        owner_organisation: DTBillingConfigOwnerOrg | dict[str, Any] | str | int | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            device_type=device_type,
            billing_product=billing_product,
            online_lookback_hours=online_lookback_hours,
            owner_organisation=owner_organisation,
            created_at=created_at,
            updated_at=updated_at,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "device_type": ControlField(type="resource", nullable=False, ref="DTBillingConfigDeviceType"),
        "billing_product": ControlField(type="resource", nullable=True, ref="DTBillingConfigProduct"),
        "online_lookback_hours": ControlField(type="integer", nullable=True),
        "owner_organisation": ControlField(type="resource", nullable=True, ref="DTBillingConfigOwnerOrg"),
        "created_at": ControlField(type="string", nullable=False),
        "updated_at": ControlField(type="string", nullable=False),
    }
    _versions = {
        "DeviceTypeBillingConfigSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "device_type": {'required': True, 'version': 'DTBillingConfigDeviceTypeSerializerDetail'},
                "billing_product": {'required': True, 'version': 'DTBillingConfigProductSerializerDetail'},
                "online_lookback_hours": {},
                "owner_organisation": {'required': True, 'version': 'DTBillingConfigOwnerOrgSerializerDetail'},
                "created_at": {'required': True},
                "updated_at": {'required': True},
            },
        },
        "DeviceTypeBillingConfigSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "device_type": {'required': True, 'output_id': 'device_type_id'},
                "billing_product": {'output_id': 'billing_product_id'},
                "online_lookback_hours": {},
                "owner_organisation": {'output_id': 'owner_organisation_id'},
            },
        },
        "DeviceTypeBillingConfigSerializerList": {
            "fields": {
                "id": {'required': True},
                "device_type": {'required': True, 'version': 'DTBillingConfigDeviceTypeSerializerList'},
                "billing_product": {'required': True, 'version': 'DTBillingConfigProductSerializerList'},
                "online_lookback_hours": {},
                "owner_organisation": {'required': True, 'version': 'DTBillingConfigOwnerOrgSerializerList'},
                "created_at": {'required': True},
                "updated_at": {'required': True},
            },
        },
        "PatchedDeviceTypeBillingConfigSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "device_type": {'output_id': 'device_type_id'},
                "billing_product": {'output_id': 'billing_product_id'},
                "online_lookback_hours": {},
                "owner_organisation": {'output_id': 'owner_organisation_id'},
            },
        },
    }

class Group(ControlModel):
    _model_name = "Group"
    id: int
    name: str
    organisation: Organisation
    archived: bool
    parent_id: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        archived: bool | None = None,
        parent_id: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            organisation=organisation,
            archived=archived,
            parent_id=parent_id,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
        "archived": ControlField(type="boolean", nullable=False),
        "parent_id": ControlField(type="id", nullable=False),
    }
    _versions = {
        "GroupBasicSerialiserDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "GroupBasicSerialiserList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "GroupChildrenSerialiserDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "GroupParentSerialiserDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "GroupSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "organisation": {'required': True, 'version': 'OrganisationSimpleSerialiserDetail'},
                "archived": {'required': True},
            },
        },
        "GroupSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "name": {'required': True},
            },
        },
        "GroupSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "organisation": {'required': True, 'version': 'OrganisationSimpleSerialiserList'},
                "archived": {'required': True},
            },
        },
        "PatchedGroupSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "name": {},
                "parent_id": {},
            },
        },
    }

class GroupPermission(ControlModel):
    _model_name = "GroupPermission"
    group: Group
    user: PermissionUser
    role: GroupRole | None
    def __init__(
        self,
        *,
        group: Group | dict[str, Any] | str | int | None = None,
        user: PermissionUser | dict[str, Any] | str | int | None = None,
        role: GroupRole | dict[str, Any] | str | int | None = None,
    ) -> None:
        super().__init__(
            group=group,
            user=user,
            role=role,
        )
    _field_defs = {
        "group": ControlField(type="resource", nullable=False, ref="Group"),
        "user": ControlField(type="resource", nullable=False, ref="PermissionUser"),
        "role": ControlField(type="resource", nullable=True, ref="GroupRole"),
    }
    _versions = {
        "GroupPermissionSerializerDetail": {
            "fields": {
                "group": {'required': True, 'version': 'GroupBasicSerialiserDetail'},
                "user": {'required': True, 'version': 'PermissionUserSerializerDetail'},
                "role": {'required': True, 'version': 'GroupRoleSerializerDetail'},
            },
        },
        "GroupPermissionSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "user": {'required': True, 'output_id': 'user_id'},
                "role": {'required': True, 'output_id': 'role_id'},
            },
        },
        "GroupPermissionSerializerList": {
            "fields": {
                "group": {'required': True, 'version': 'GroupBasicSerialiserList'},
                "user": {'required': True, 'version': 'PermissionUserSerializerList'},
                "role": {'required': True, 'version': 'GroupRoleSerializerList'},
            },
        },
        "PatchedGroupPermissionSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "user": {'output_id': 'user_id'},
                "role": {'output_id': 'role_id'},
            },
        },
    }

class GroupRole(ControlModel):
    _model_name = "GroupRole"
    id: int
    name: str
    organisation: Organisation
    archived: bool
    billing_manager: bool
    group_move: bool
    group_edit: bool
    group_view: bool
    group_users_manage: bool
    group_users_view: bool
    device_create: bool
    device_configure: bool
    device_tunnels: bool
    device_private_view: bool
    device_control: bool
    device_history: bool
    device_view: bool
    alarms_manage: bool
    alarms_view: bool
    turn_client_connect: bool
    dashboard_create: bool
    dashboard_edit: bool
    dashboard_control: bool
    dashboard_view: bool
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        archived: bool | None = None,
        billing_manager: bool | None = None,
        group_move: bool | None = None,
        group_edit: bool | None = None,
        group_view: bool | None = None,
        group_users_manage: bool | None = None,
        group_users_view: bool | None = None,
        device_create: bool | None = None,
        device_configure: bool | None = None,
        device_tunnels: bool | None = None,
        device_private_view: bool | None = None,
        device_control: bool | None = None,
        device_history: bool | None = None,
        device_view: bool | None = None,
        alarms_manage: bool | None = None,
        alarms_view: bool | None = None,
        turn_client_connect: bool | None = None,
        dashboard_create: bool | None = None,
        dashboard_edit: bool | None = None,
        dashboard_control: bool | None = None,
        dashboard_view: bool | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            organisation=organisation,
            archived=archived,
            billing_manager=billing_manager,
            group_move=group_move,
            group_edit=group_edit,
            group_view=group_view,
            group_users_manage=group_users_manage,
            group_users_view=group_users_view,
            device_create=device_create,
            device_configure=device_configure,
            device_tunnels=device_tunnels,
            device_private_view=device_private_view,
            device_control=device_control,
            device_history=device_history,
            device_view=device_view,
            alarms_manage=alarms_manage,
            alarms_view=alarms_view,
            turn_client_connect=turn_client_connect,
            dashboard_create=dashboard_create,
            dashboard_edit=dashboard_edit,
            dashboard_control=dashboard_control,
            dashboard_view=dashboard_view,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
        "archived": ControlField(type="boolean", nullable=False),
        "billing_manager": ControlField(type="boolean", nullable=False),
        "group_move": ControlField(type="boolean", nullable=False),
        "group_edit": ControlField(type="boolean", nullable=False),
        "group_view": ControlField(type="boolean", nullable=False),
        "group_users_manage": ControlField(type="boolean", nullable=False),
        "group_users_view": ControlField(type="boolean", nullable=False),
        "device_create": ControlField(type="boolean", nullable=False),
        "device_configure": ControlField(type="boolean", nullable=False),
        "device_tunnels": ControlField(type="boolean", nullable=False),
        "device_private_view": ControlField(type="boolean", nullable=False),
        "device_control": ControlField(type="boolean", nullable=False),
        "device_history": ControlField(type="boolean", nullable=False),
        "device_view": ControlField(type="boolean", nullable=False),
        "alarms_manage": ControlField(type="boolean", nullable=False),
        "alarms_view": ControlField(type="boolean", nullable=False),
        "turn_client_connect": ControlField(type="boolean", nullable=False),
        "dashboard_create": ControlField(type="boolean", nullable=False),
        "dashboard_edit": ControlField(type="boolean", nullable=False),
        "dashboard_control": ControlField(type="boolean", nullable=False),
        "dashboard_view": ControlField(type="boolean", nullable=False),
    }
    _versions = {
        "BasicGroupRoleDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "BasicGroupRoleList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "GroupRoleSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "organisation": {'required': True, 'version': 'BasicOrganisationDetail'},
                "archived": {'required': True},
                "billing_manager": {},
                "group_move": {},
                "group_edit": {},
                "group_view": {},
                "group_users_manage": {},
                "group_users_view": {},
                "device_create": {},
                "device_configure": {},
                "device_tunnels": {},
                "device_private_view": {},
                "device_control": {},
                "device_history": {},
                "device_view": {},
                "alarms_manage": {},
                "alarms_view": {},
                "turn_client_connect": {},
                "dashboard_create": {},
                "dashboard_edit": {},
                "dashboard_control": {},
                "dashboard_view": {},
            },
        },
        "GroupRoleSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "name": {'required': True},
                "billing_manager": {},
                "group_move": {},
                "group_edit": {},
                "group_view": {},
                "group_users_manage": {},
                "group_users_view": {},
                "device_create": {},
                "device_configure": {},
                "device_tunnels": {},
                "device_private_view": {},
                "device_control": {},
                "device_history": {},
                "device_view": {},
                "alarms_manage": {},
                "alarms_view": {},
                "turn_client_connect": {},
                "dashboard_create": {},
                "dashboard_edit": {},
                "dashboard_control": {},
                "dashboard_view": {},
            },
        },
        "GroupRoleSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "organisation": {'required': True, 'version': 'BasicOrganisationList'},
                "archived": {'required': True},
                "billing_manager": {},
                "group_move": {},
                "group_edit": {},
                "group_view": {},
                "group_users_manage": {},
                "group_users_view": {},
                "device_create": {},
                "device_configure": {},
                "device_tunnels": {},
                "device_private_view": {},
                "device_control": {},
                "device_history": {},
                "device_view": {},
                "alarms_manage": {},
                "alarms_view": {},
                "turn_client_connect": {},
                "dashboard_create": {},
                "dashboard_edit": {},
                "dashboard_control": {},
                "dashboard_view": {},
            },
        },
        "PatchedGroupRoleSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "name": {},
                "billing_manager": {},
                "group_move": {},
                "group_edit": {},
                "group_view": {},
                "group_users_manage": {},
                "group_users_view": {},
                "device_create": {},
                "device_configure": {},
                "device_tunnels": {},
                "device_private_view": {},
                "device_control": {},
                "device_history": {},
                "device_view": {},
                "alarms_manage": {},
                "alarms_view": {},
                "turn_client_connect": {},
                "dashboard_create": {},
                "dashboard_edit": {},
                "dashboard_control": {},
                "dashboard_view": {},
            },
        },
    }

class GroupRoleAssignment(ControlModel):
    _model_name = "GroupRoleAssignment"
    group_id: str
    role_id: str
    def __init__(
        self,
        *,
        group_id: str | None = None,
        role_id: str | None = None,
    ) -> None:
        super().__init__(
            group_id=group_id,
            role_id=role_id,
        )
    _field_defs = {
        "group_id": ControlField(type="id", nullable=False),
        "role_id": ControlField(type="id", nullable=False),
    }
    _versions = {
        "GroupRoleAssignmentSerializerDetailRequest": {
            "fields": {
                "group_id": {'required': True},
                "role_id": {'required': True},
            },
        },
    }

class IngestionEndpoint(ControlModel):
    _model_name = "IngestionEndpoint"
    id: int
    url: str
    token: str
    def __init__(
        self,
        *,
        id: int | None = None,
        url: str | None = None,
        token: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            url=url,
            token=token,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "url": ControlField(type="string", nullable=False),
        "token": ControlField(type="string", nullable=False),
    }
    _versions = {
        "IngestionEndpointSerializerDetail": {
            "fields": {
                "id": {},
                "url": {},
                "token": {},
            },
        },
        "IngestionEndpointSerializerDetailRequest": {
            "fields": {
                "id": {},
                "url": {},
                "token": {},
            },
        },
        "IngestionEndpointSerializerList": {
            "fields": {
                "id": {},
                "url": {},
                "token": {},
            },
        },
    }

class Integration(ControlModel):
    _model_name = "Integration"
    id: int
    name: str
    display_name: str
    application: Application
    deployment_config: Any
    organisation: Organisation
    latest_deployment: ApplicationDeployment
    ingestion_endpoints: list[IngestionEndpoint]
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        display_name: str | None = None,
        application: Application | dict[str, Any] | str | int | None = None,
        deployment_config: Any | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        latest_deployment: ApplicationDeployment | dict[str, Any] | str | int | None = None,
        ingestion_endpoints: list[IngestionEndpoint | dict[str, Any] | str | int] | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            display_name=display_name,
            application=application,
            deployment_config=deployment_config,
            organisation=organisation,
            latest_deployment=latest_deployment,
            ingestion_endpoints=ingestion_endpoints,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "display_name": ControlField(type="string", nullable=False),
        "application": ControlField(type="resource", nullable=False, ref="Application"),
        "deployment_config": ControlField(type="json", nullable=False),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
        "latest_deployment": ControlField(type="resource", nullable=False, ref="ApplicationDeployment"),
        "ingestion_endpoints": ControlField(type="resource", nullable=False, is_array=True, ref="IngestionEndpoint"),
    }
    _versions = {
        "IntegrationSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "display_name": {'required': True},
                "application": {'required': True, 'version': 'SlimApplicationDetail'},
                "deployment_config": {},
                "organisation": {'required': True, 'version': 'OrganisationSuperBasicSerialiserDetail'},
                "latest_deployment": {'required': True, 'version': 'ApplicationDeploymentSerializerDetail'},
                "ingestion_endpoints": {'required': True, 'version': 'IngestionEndpointSerializerDetail'},
            },
        },
        "IntegrationSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "name": {'required': True},
                "display_name": {'required': True},
                "application": {'required': True, 'output_id': 'application_id'},
                "deployment_config": {},
            },
        },
        "IntegrationSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "display_name": {'required': True},
                "application": {'required': True, 'version': 'SlimApplicationList'},
                "deployment_config": {},
                "organisation": {'required': True, 'version': 'OrganisationSuperBasicSerialiserList'},
                "latest_deployment": {'required': True, 'version': 'ApplicationDeploymentSerializerList'},
                "ingestion_endpoints": {'required': True, 'version': 'IngestionEndpointSerializerList'},
            },
        },
        "PatchedIntegrationSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "name": {},
                "display_name": {},
                "application": {'output_id': 'application_id'},
                "deployment_config": {},
            },
        },
    }

class MeteringRunOrg(ControlModel):
    _model_name = "MeteringRunOrg"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "MeteringRunOrgSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "MeteringRunOrgSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class Organisation(ControlModel):
    _model_name = "Organisation"
    id: int
    name: str
    archived: bool
    application_id: str
    domains: list[OrganisationDomain]
    root_group: Group
    test_field_A: int
    retention_period: int
    legacy_doover_api_key: str | None
    llm_api_key: str | None
    theme: Theme
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        archived: bool | None = None,
        application_id: str | None = None,
        domains: list[OrganisationDomain | dict[str, Any] | str | int] | None = None,
        root_group: Group | dict[str, Any] | str | int | None = None,
        test_field_A: int | None = None,
        retention_period: int | None = None,
        legacy_doover_api_key: str | None = None,
        llm_api_key: str | None = None,
        theme: Theme | dict[str, Any] | str | int | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            archived=archived,
            application_id=application_id,
            domains=domains,
            root_group=root_group,
            test_field_A=test_field_A,
            retention_period=retention_period,
            legacy_doover_api_key=legacy_doover_api_key,
            llm_api_key=llm_api_key,
            theme=theme,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "archived": ControlField(type="boolean", nullable=False),
        "application_id": ControlField(type="id", nullable=False),
        "domains": ControlField(type="resource", nullable=False, is_array=True, ref="OrganisationDomain"),
        "root_group": ControlField(type="resource", nullable=False, ref="Group"),
        "test_field_A": ControlField(type="integer", nullable=False),
        "retention_period": ControlField(type="integer", nullable=False),
        "legacy_doover_api_key": ControlField(type="string", nullable=True),
        "llm_api_key": ControlField(type="string", nullable=True),
        "theme": ControlField(type="resource", nullable=False, ref="Theme"),
    }
    _versions = {
        "BasicOrganisationDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "archived": {'required': True},
            },
        },
        "BasicOrganisationList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "archived": {'required': True},
            },
        },
        "OrganisationBasicSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "OrganisationBasicSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "OrganisationSerializerDetail": {
            "fields": {
                "name": {'required': True},
                "archived": {'required': True},
                "application_id": {'required': True},
                "domains": {'required': True, 'version': 'OrganisationDomainSerializerDetail'},
                "root_group": {'required': True, 'version': 'GroupBasicSerialiserDetail'},
                "id": {'required': True},
                "test_field_A": {},
                "retention_period": {},
                "legacy_doover_api_key": {},
                "llm_api_key": {},
                "theme": {'version': 'ThemeSerializerDetail'},
            },
        },
        "OrganisationSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "name": {'required': True},
                "test_field_A": {},
                "retention_period": {},
                "legacy_doover_api_key": {},
                "llm_api_key": {},
                "theme": {'version': 'ThemeSerializerDetailRequest'},
            },
        },
        "OrganisationSerializerList": {
            "fields": {
                "name": {'required': True},
                "archived": {'required': True},
                "application_id": {'required': True},
                "domains": {'required': True, 'version': 'OrganisationDomainSerializerList'},
                "root_group": {'required': True, 'version': 'GroupBasicSerialiserList'},
                "id": {'required': True},
                "test_field_A": {},
                "retention_period": {},
                "legacy_doover_api_key": {},
                "llm_api_key": {},
                "theme": {'version': 'ThemeSerializerList'},
            },
        },
        "OrganisationSimpleSerialiserDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "OrganisationSimpleSerialiserList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "OrganisationSuperBasicSerialiserDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "OrganisationSuperBasicSerialiserList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "PatchedOrganisationSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "name": {},
                "test_field_A": {},
                "retention_period": {},
                "legacy_doover_api_key": {},
                "llm_api_key": {},
                "theme": {'version': 'ThemeSerializerDetailRequest'},
            },
        },
    }

class OrganisationDomain(ControlModel):
    _model_name = "OrganisationDomain"
    id: int
    hostname: str
    default: bool
    def __init__(
        self,
        *,
        id: int | None = None,
        hostname: str | None = None,
        default: bool | None = None,
    ) -> None:
        super().__init__(
            id=id,
            hostname=hostname,
            default=default,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "hostname": ControlField(type="string", nullable=False),
        "default": ControlField(type="boolean", nullable=False),
    }
    _versions = {
        "OrganisationDomainSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "hostname": {'required': True},
                "default": {},
            },
        },
        "OrganisationDomainSerializerDetailRequest": {
            "fields": {
                "hostname": {'required': True},
                "default": {},
            },
        },
        "OrganisationDomainSerializerList": {
            "fields": {
                "id": {'required': True},
                "hostname": {'required': True},
                "default": {},
            },
        },
        "PatchedOrganisationDomainSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "hostname": {},
                "default": {},
            },
        },
    }

class OrganisationRole(ControlModel):
    _model_name = "OrganisationRole"
    id: int
    name: str
    organisation: Organisation
    default_root_group_role: GroupRole | None
    archived: bool
    billing_manager: bool
    applications_manage: bool
    applications_view: bool
    device_types_manage: bool
    device_types_view: bool
    user_permissions_manage: bool
    users_manage: bool
    users_view: bool
    users_invite: bool
    reports_create: bool
    integrations_manage: bool
    theme_manage: bool
    domains_manage: bool
    conatiner_registry_profile_manage: bool
    conatiner_registry_profile_view: bool
    access_site: bool
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        default_root_group_role: GroupRole | dict[str, Any] | str | int | None = None,
        archived: bool | None = None,
        billing_manager: bool | None = None,
        applications_manage: bool | None = None,
        applications_view: bool | None = None,
        device_types_manage: bool | None = None,
        device_types_view: bool | None = None,
        user_permissions_manage: bool | None = None,
        users_manage: bool | None = None,
        users_view: bool | None = None,
        users_invite: bool | None = None,
        reports_create: bool | None = None,
        integrations_manage: bool | None = None,
        theme_manage: bool | None = None,
        domains_manage: bool | None = None,
        conatiner_registry_profile_manage: bool | None = None,
        conatiner_registry_profile_view: bool | None = None,
        access_site: bool | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            organisation=organisation,
            default_root_group_role=default_root_group_role,
            archived=archived,
            billing_manager=billing_manager,
            applications_manage=applications_manage,
            applications_view=applications_view,
            device_types_manage=device_types_manage,
            device_types_view=device_types_view,
            user_permissions_manage=user_permissions_manage,
            users_manage=users_manage,
            users_view=users_view,
            users_invite=users_invite,
            reports_create=reports_create,
            integrations_manage=integrations_manage,
            theme_manage=theme_manage,
            domains_manage=domains_manage,
            conatiner_registry_profile_manage=conatiner_registry_profile_manage,
            conatiner_registry_profile_view=conatiner_registry_profile_view,
            access_site=access_site,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
        "default_root_group_role": ControlField(type="resource", nullable=True, ref="GroupRole"),
        "archived": ControlField(type="boolean", nullable=False),
        "billing_manager": ControlField(type="boolean", nullable=False),
        "applications_manage": ControlField(type="boolean", nullable=False),
        "applications_view": ControlField(type="boolean", nullable=False),
        "device_types_manage": ControlField(type="boolean", nullable=False),
        "device_types_view": ControlField(type="boolean", nullable=False),
        "user_permissions_manage": ControlField(type="boolean", nullable=False),
        "users_manage": ControlField(type="boolean", nullable=False),
        "users_view": ControlField(type="boolean", nullable=False),
        "users_invite": ControlField(type="boolean", nullable=False),
        "reports_create": ControlField(type="boolean", nullable=False),
        "integrations_manage": ControlField(type="boolean", nullable=False),
        "theme_manage": ControlField(type="boolean", nullable=False),
        "domains_manage": ControlField(type="boolean", nullable=False),
        "conatiner_registry_profile_manage": ControlField(type="boolean", nullable=False),
        "conatiner_registry_profile_view": ControlField(type="boolean", nullable=False),
        "access_site": ControlField(type="boolean", nullable=False),
    }
    _versions = {
        "OrganisationRoleSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "organisation": {'required': True, 'version': 'BasicOrganisationDetail'},
                "default_root_group_role": {'required': True, 'version': 'BasicGroupRoleDetail'},
                "archived": {'required': True},
                "billing_manager": {},
                "applications_manage": {},
                "applications_view": {},
                "device_types_manage": {},
                "device_types_view": {},
                "user_permissions_manage": {},
                "users_manage": {},
                "users_view": {},
                "users_invite": {},
                "reports_create": {},
                "integrations_manage": {},
                "theme_manage": {},
                "domains_manage": {},
                "conatiner_registry_profile_manage": {},
                "conatiner_registry_profile_view": {},
                "access_site": {},
            },
        },
        "OrganisationRoleSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "name": {'required': True},
                "default_root_group_role": {'output_id': 'default_root_group_role_id'},
                "billing_manager": {},
                "applications_manage": {},
                "applications_view": {},
                "device_types_manage": {},
                "device_types_view": {},
                "user_permissions_manage": {},
                "users_manage": {},
                "users_view": {},
                "users_invite": {},
                "reports_create": {},
                "integrations_manage": {},
                "theme_manage": {},
                "domains_manage": {},
                "conatiner_registry_profile_manage": {},
                "conatiner_registry_profile_view": {},
                "access_site": {},
            },
        },
        "OrganisationRoleSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "organisation": {'required': True, 'version': 'BasicOrganisationList'},
                "default_root_group_role": {'required': True, 'version': 'BasicGroupRoleList'},
                "archived": {'required': True},
                "billing_manager": {},
                "applications_manage": {},
                "applications_view": {},
                "device_types_manage": {},
                "device_types_view": {},
                "user_permissions_manage": {},
                "users_manage": {},
                "users_view": {},
                "users_invite": {},
                "reports_create": {},
                "integrations_manage": {},
                "theme_manage": {},
                "domains_manage": {},
                "conatiner_registry_profile_manage": {},
                "conatiner_registry_profile_view": {},
                "access_site": {},
            },
        },
        "PatchedOrganisationRoleSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "name": {},
                "default_root_group_role": {'output_id': 'default_root_group_role_id'},
                "billing_manager": {},
                "applications_manage": {},
                "applications_view": {},
                "device_types_manage": {},
                "device_types_view": {},
                "user_permissions_manage": {},
                "users_manage": {},
                "users_view": {},
                "users_invite": {},
                "reports_create": {},
                "integrations_manage": {},
                "theme_manage": {},
                "domains_manage": {},
                "conatiner_registry_profile_manage": {},
                "conatiner_registry_profile_view": {},
                "access_site": {},
            },
        },
    }

class OrganisationSharedReceiveProfile(ControlModel):
    _model_name = "OrganisationSharedReceiveProfile"
    id: int
    name: str
    description: str
    organisation: Organisation
    sharing_organisation_id: str
    sharing_base_url: str
    sharing_data_url: str | None
    sharing_auth_tenant_id: str | None
    sharing_profile_id: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        description: str | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        sharing_organisation_id: str | None = None,
        sharing_base_url: str | None = None,
        sharing_data_url: str | None = None,
        sharing_auth_tenant_id: str | None = None,
        sharing_profile_id: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            description=description,
            organisation=organisation,
            sharing_organisation_id=sharing_organisation_id,
            sharing_base_url=sharing_base_url,
            sharing_data_url=sharing_data_url,
            sharing_auth_tenant_id=sharing_auth_tenant_id,
            sharing_profile_id=sharing_profile_id,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "description": ControlField(type="string", nullable=False),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
        "sharing_organisation_id": ControlField(type="id", nullable=False),
        "sharing_base_url": ControlField(type="string", nullable=False),
        "sharing_data_url": ControlField(type="string", nullable=True),
        "sharing_auth_tenant_id": ControlField(type="id", nullable=True),
        "sharing_profile_id": ControlField(type="id", nullable=False),
    }
    _versions = {
        "OrganisationSharedReceiveProfileSerializerDetail": {
            "fields": {
                "id": {},
                "name": {'required': True},
                "description": {'required': True},
                "organisation": {'required': True, 'version': 'BasicOrganisationDetail'},
                "sharing_organisation_id": {'required': True},
                "sharing_base_url": {'required': True},
                "sharing_data_url": {},
                "sharing_auth_tenant_id": {},
                "sharing_profile_id": {'required': True},
            },
        },
        "OrganisationSharedReceiveProfileSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "id": {},
                "name": {'required': True},
                "description": {'required': True},
                "sharing_organisation_id": {'required': True},
                "sharing_base_url": {'required': True},
                "sharing_data_url": {},
                "sharing_auth_tenant_id": {},
                "sharing_profile_id": {'required': True},
            },
        },
        "OrganisationSharedReceiveProfileSerializerList": {
            "fields": {
                "id": {},
                "name": {'required': True},
                "description": {'required': True},
                "organisation": {'required': True, 'version': 'BasicOrganisationList'},
                "sharing_organisation_id": {'required': True},
                "sharing_base_url": {'required': True},
                "sharing_data_url": {},
                "sharing_auth_tenant_id": {},
                "sharing_profile_id": {'required': True},
            },
        },
        "PatchedOrganisationSharedReceiveProfileSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "id": {},
                "name": {},
                "description": {},
                "sharing_organisation_id": {},
                "sharing_base_url": {},
                "sharing_data_url": {},
                "sharing_auth_tenant_id": {},
                "sharing_profile_id": {},
            },
        },
    }

class OrganisationSharingProfile(ControlModel):
    _model_name = "OrganisationSharingProfile"
    id: int
    name: str
    description: str
    all_devices: list[Device]
    devices: list[Device]
    groups: list[Group]
    role: OrganisationRole | None
    dd_permission_id: str
    organisation: Organisation
    shared_organisation_id: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        description: str | None = None,
        all_devices: list[Device | dict[str, Any] | str | int] | None = None,
        devices: list[Device | dict[str, Any] | str | int] | None = None,
        groups: list[Group | dict[str, Any] | str | int] | None = None,
        role: OrganisationRole | dict[str, Any] | str | int | None = None,
        dd_permission_id: str | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        shared_organisation_id: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            description=description,
            all_devices=all_devices,
            devices=devices,
            groups=groups,
            role=role,
            dd_permission_id=dd_permission_id,
            organisation=organisation,
            shared_organisation_id=shared_organisation_id,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "description": ControlField(type="string", nullable=False),
        "all_devices": ControlField(type="resource", nullable=False, is_array=True, ref="Device"),
        "devices": ControlField(type="resource", nullable=False, is_array=True, ref="Device"),
        "groups": ControlField(type="resource", nullable=False, is_array=True, ref="Group"),
        "role": ControlField(type="resource", nullable=True, ref="OrganisationRole"),
        "dd_permission_id": ControlField(type="id", nullable=False),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
        "shared_organisation_id": ControlField(type="id", nullable=False),
    }
    _versions = {
        "OrganisationSharingProfileSerializerDetail": {
            "fields": {
                "id": {},
                "name": {'required': True},
                "description": {'required': True},
                "all_devices": {'required': True, 'version': 'DeviceSerializerDetail'},
                "devices": {'required': True, 'version': 'DeviceSerializerDetail'},
                "groups": {'required': True, 'version': 'GroupSerializerDetail'},
                "role": {'required': True, 'version': 'OrganisationRoleSerializerDetail'},
                "dd_permission_id": {'required': True},
                "organisation": {'required': True, 'output_id': 'organisation_id'},
                "shared_organisation_id": {'required': True},
            },
        },
        "OrganisationSharingProfileSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "id": {},
                "name": {'required': True},
                "description": {'required': True},
                "devices": {'output_id': 'device_ids'},
                "groups": {'output_id': 'group_ids'},
                "role": {'required': True, 'output_id': 'role_id'},
                "dd_permission_id": {'required': True},
                "shared_organisation_id": {'required': True},
            },
        },
        "OrganisationSharingProfileSerializerList": {
            "fields": {
                "id": {},
                "name": {'required': True},
                "description": {'required': True},
                "all_devices": {'required': True, 'version': 'DeviceSerializerList'},
                "devices": {'required': True, 'version': 'DeviceSerializerList'},
                "groups": {'required': True, 'version': 'GroupSerializerList'},
                "role": {'required': True, 'version': 'OrganisationRoleSerializerList'},
                "dd_permission_id": {'required': True},
                "organisation": {'required': True, 'output_id': 'organisation_id'},
                "shared_organisation_id": {'required': True},
            },
        },
        "PatchedOrganisationSharingProfileSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "id": {},
                "name": {},
                "description": {},
                "devices": {'output_id': 'device_ids'},
                "groups": {'output_id': 'group_ids'},
                "role": {'output_id': 'role_id'},
                "dd_permission_id": {},
                "shared_organisation_id": {},
            },
        },
    }

class OrganisationUser(ControlModel):
    _model_name = "OrganisationUser"
    organisation: str
    user: PermissionUser
    role: OrganisationRole | None
    user_email: str
    add_to_group: list[GroupRoleAssignment]
    def __init__(
        self,
        *,
        organisation: str | None = None,
        user: PermissionUser | dict[str, Any] | str | int | None = None,
        role: OrganisationRole | dict[str, Any] | str | int | None = None,
        user_email: str | None = None,
        add_to_group: list[GroupRoleAssignment | dict[str, Any] | str | int] | None = None,
    ) -> None:
        super().__init__(
            organisation=organisation,
            user=user,
            role=role,
            user_email=user_email,
            add_to_group=add_to_group,
        )
    _field_defs = {
        "organisation": ControlField(type="string", nullable=False),
        "user": ControlField(type="resource", nullable=False, ref="PermissionUser"),
        "role": ControlField(type="resource", nullable=True, ref="OrganisationRole"),
        "user_email": ControlField(type="string", nullable=False),
        "add_to_group": ControlField(type="resource", nullable=False, is_array=True, ref="GroupRoleAssignment"),
    }
    _versions = {
        "OrganisationUserSerializerDetail": {
            "fields": {
                "organisation": {'required': True},
                "user": {'required': True, 'version': 'PermissionUserSerializerDetail'},
                "role": {'required': True, 'version': 'OrganisationRoleSerializerDetail'},
            },
        },
        "OrganisationUserSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "user_email": {'required': True},
                "role": {'required': True, 'output_id': 'role_id'},
                "add_to_group": {'version': 'GroupRoleAssignmentSerializerDetailRequest'},
            },
        },
        "OrganisationUserSerializerList": {
            "fields": {
                "organisation": {'required': True},
                "user": {'required': True, 'version': 'PermissionUserSerializerList'},
                "role": {'required': True, 'version': 'OrganisationRoleSerializerList'},
            },
        },
        "PatchedOrganisationUserSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "user_email": {},
                "role": {'output_id': 'role_id'},
                "add_to_group": {'version': 'GroupRoleAssignmentSerializerDetailRequest'},
            },
        },
    }

class PendingUser(ControlModel):
    _model_name = "PendingUser"
    email: str
    organisation: Organisation
    message: str | None
    id: int
    created_at: str
    last_invited: str | None
    def __init__(
        self,
        *,
        email: str | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        message: str | None = None,
        id: int | None = None,
        created_at: str | None = None,
        last_invited: str | None = None,
    ) -> None:
        super().__init__(
            email=email,
            organisation=organisation,
            message=message,
            id=id,
            created_at=created_at,
            last_invited=last_invited,
        )
    _field_defs = {
        "email": ControlField(type="string", nullable=False),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
        "message": ControlField(type="string", nullable=True),
        "id": ControlField(type="SnowflakeId", nullable=False),
        "created_at": ControlField(type="string", nullable=False),
        "last_invited": ControlField(type="string", nullable=True),
    }
    _versions = {
        "PatchedPendingUserSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "email": {},
                "organisation": {'output_id': 'organisation_id'},
                "message": {},
            },
        },
        "PendingUserSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "email": {'required': True},
                "organisation": {'required': True, 'version': 'OrganisationSerializerDetail'},
                "created_at": {'required': True},
                "message": {},
                "last_invited": {'required': True},
            },
        },
        "PendingUserSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "email": {'required': True},
                "organisation": {'required': True, 'output_id': 'organisation_id'},
                "message": {},
            },
        },
        "PendingUserSerializerList": {
            "fields": {
                "id": {'required': True},
                "email": {'required': True},
                "organisation": {'required': True, 'version': 'OrganisationSerializerList'},
                "created_at": {'required': True},
                "message": {},
                "last_invited": {'required': True},
            },
        },
    }

class PermissionUser(ControlModel):
    _model_name = "PermissionUser"
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        username: str | None = None,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "username": ControlField(type="string", nullable=False),
        "email": ControlField(type="string", nullable=False),
        "first_name": ControlField(type="string", nullable=False),
        "last_name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "PermissionUserSerializerDetail": {
            "fields": {
                "id": {},
                "username": {'required': True},
                "email": {},
                "first_name": {},
                "last_name": {},
            },
        },
        "PermissionUserSerializerDetailRequest": {
            "fields": {
                "id": {},
                "username": {'required': True},
                "email": {},
                "first_name": {},
                "last_name": {},
            },
        },
        "PermissionUserSerializerList": {
            "fields": {
                "id": {},
                "username": {'required': True},
                "email": {},
                "first_name": {},
                "last_name": {},
            },
        },
    }

class Report(ControlModel):
    _model_name = "Report"
    id: int
    devices: list[str]
    logs: str
    period_end: int
    period_start: int
    report_generator: Application
    status: str
    name: str
    config: Any
    schedule: ReportSchedule | None
    files: list[Attachment]
    def __init__(
        self,
        *,
        id: int | None = None,
        devices: list[str] | None = None,
        logs: str | None = None,
        period_end: int | None = None,
        period_start: int | None = None,
        report_generator: Application | dict[str, Any] | str | int | None = None,
        status: str | None = None,
        name: str | None = None,
        config: Any | None = None,
        schedule: ReportSchedule | dict[str, Any] | str | int | None = None,
        files: list[Attachment | dict[str, Any] | str | int] | None = None,
    ) -> None:
        super().__init__(
            id=id,
            devices=devices,
            logs=logs,
            period_end=period_end,
            period_start=period_start,
            report_generator=report_generator,
            status=status,
            name=name,
            config=config,
            schedule=schedule,
            files=files,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "devices": ControlField(type="string", nullable=False, is_array=True),
        "logs": ControlField(type="string", nullable=False),
        "period_end": ControlField(type="integer", nullable=False),
        "period_start": ControlField(type="integer", nullable=False),
        "report_generator": ControlField(type="resource", nullable=False, ref="Application"),
        "status": ControlField(type="string", nullable=False),
        "name": ControlField(type="string", nullable=False),
        "config": ControlField(type="json", nullable=False),
        "schedule": ControlField(type="resource", nullable=True, ref="ReportSchedule"),
        "files": ControlField(type="resource", nullable=False, is_array=True, ref="Attachment"),
    }
    _versions = {
        "ReportSerialiserDetail": {
            "fields": {
                "id": {'required': True},
                "devices": {'required': True},
                "logs": {'required': True},
                "period_end": {'required': True},
                "period_start": {'required': True},
                "report_generator": {'required': True, 'version': 'SlimApplicationDetail'},
                "status": {'required': True},
                "name": {},
                "config": {},
                "schedule": {'required': True, 'version': 'ReportScheduleSerialiserDetail'},
                "files": {'required': True, 'version': 'AttachmentSerializerDetail'},
            },
        },
        "ReportSerialiserList": {
            "fields": {
                "id": {'required': True},
                "devices": {'required': True},
                "logs": {'required': True},
                "period_end": {'required': True},
                "period_start": {'required': True},
                "report_generator": {'required': True, 'version': 'SlimApplicationList'},
                "status": {'required': True},
                "name": {},
                "config": {},
                "schedule": {'required': True, 'version': 'ReportScheduleSerialiserList'},
                "files": {'required': True, 'version': 'AttachmentSerializerList'},
            },
        },
    }

class ReportCreate(ControlModel):
    _model_name = "ReportCreate"
    name: str
    config: Any
    report_generator_id: str
    period_start: int
    period_end: int
    def __init__(
        self,
        *,
        name: str | None = None,
        config: Any | None = None,
        report_generator_id: str | None = None,
        period_start: int | None = None,
        period_end: int | None = None,
    ) -> None:
        super().__init__(
            name=name,
            config=config,
            report_generator_id=report_generator_id,
            period_start=period_start,
            period_end=period_end,
        )
    _field_defs = {
        "name": ControlField(type="string", nullable=False),
        "config": ControlField(type="json", nullable=False),
        "report_generator_id": ControlField(type="id", nullable=False),
        "period_start": ControlField(type="integer", nullable=False),
        "period_end": ControlField(type="integer", nullable=False),
    }
    _versions = {
        "ReportCreateSerialiserDetailRequest": {
            "methods": ['POST'],
            "fields": {
                "name": {},
                "config": {'required': True},
                "report_generator_id": {'required': True},
                "period_start": {'required': True},
                "period_end": {'required': True},
            },
        },
    }

class ReportSchedule(ControlModel):
    _model_name = "ReportSchedule"
    name: str
    display_name: str
    application: Application
    deployment_config: Any
    id: int
    archived: bool
    organisation: Organisation
    latest_deployment: ApplicationDeployment
    def __init__(
        self,
        *,
        name: str | None = None,
        display_name: str | None = None,
        application: Application | dict[str, Any] | str | int | None = None,
        deployment_config: Any | None = None,
        id: int | None = None,
        archived: bool | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
        latest_deployment: ApplicationDeployment | dict[str, Any] | str | int | None = None,
    ) -> None:
        super().__init__(
            name=name,
            display_name=display_name,
            application=application,
            deployment_config=deployment_config,
            id=id,
            archived=archived,
            organisation=organisation,
            latest_deployment=latest_deployment,
        )
    _field_defs = {
        "name": ControlField(type="string", nullable=False),
        "display_name": ControlField(type="string", nullable=False),
        "application": ControlField(type="resource", nullable=False, ref="Application"),
        "deployment_config": ControlField(type="json", nullable=False),
        "id": ControlField(type="SnowflakeId", nullable=False),
        "archived": ControlField(type="boolean", nullable=False),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
        "latest_deployment": ControlField(type="resource", nullable=False, ref="ApplicationDeployment"),
    }
    _versions = {
        "PatchedReportScheduleSerialiserDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "name": {},
                "display_name": {},
                "application": {'output_id': 'application_id'},
                "deployment_config": {},
            },
        },
        "ReportScheduleSerialiserDetail": {
            "fields": {
                "id": {'required': True},
                "archived": {'required': True},
                "name": {},
                "display_name": {'required': True},
                "application": {'required': True, 'version': 'SlimApplicationDetail'},
                "deployment_config": {},
                "organisation": {'required': True, 'version': 'OrganisationSuperBasicSerialiserDetail'},
                "latest_deployment": {'required': True, 'version': 'ApplicationDeploymentSerializerDetail'},
            },
        },
        "ReportScheduleSerialiserDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "name": {},
                "display_name": {'required': True},
                "application": {'required': True, 'output_id': 'application_id'},
                "deployment_config": {},
            },
        },
        "ReportScheduleSerialiserList": {
            "fields": {
                "id": {'required': True},
                "archived": {'required': True},
                "name": {},
                "display_name": {'required': True},
                "application": {'required': True, 'version': 'SlimApplicationList'},
                "deployment_config": {},
                "organisation": {'required': True, 'version': 'OrganisationSuperBasicSerialiserList'},
                "latest_deployment": {'required': True, 'version': 'ApplicationDeploymentSerializerList'},
            },
        },
    }

class SellerCustomer(ControlModel):
    _model_name = "SellerCustomer"
    group: SellerCustomerGroup
    billing_email: str | None
    stripe_customer_id: str | None
    notes: str
    id: int
    seller_organisation: SellerCustomerOrg
    has_subscription: str
    created_at: str
    updated_at: str
    def __init__(
        self,
        *,
        group: SellerCustomerGroup | dict[str, Any] | str | int | None = None,
        billing_email: str | None = None,
        stripe_customer_id: str | None = None,
        notes: str | None = None,
        id: int | None = None,
        seller_organisation: SellerCustomerOrg | dict[str, Any] | str | int | None = None,
        has_subscription: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        super().__init__(
            group=group,
            billing_email=billing_email,
            stripe_customer_id=stripe_customer_id,
            notes=notes,
            id=id,
            seller_organisation=seller_organisation,
            has_subscription=has_subscription,
            created_at=created_at,
            updated_at=updated_at,
        )
    _field_defs = {
        "group": ControlField(type="resource", nullable=False, ref="SellerCustomerGroup"),
        "billing_email": ControlField(type="string", nullable=True),
        "stripe_customer_id": ControlField(type="id", nullable=True),
        "notes": ControlField(type="string", nullable=False),
        "id": ControlField(type="SnowflakeId", nullable=False),
        "seller_organisation": ControlField(type="resource", nullable=False, ref="SellerCustomerOrg"),
        "has_subscription": ControlField(type="string", nullable=False),
        "created_at": ControlField(type="string", nullable=False),
        "updated_at": ControlField(type="string", nullable=False),
    }
    _versions = {
        "PatchedSellerCustomerSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "group": {'output_id': 'group_id'},
                "billing_email": {},
                "stripe_customer_id": {},
                "notes": {},
            },
        },
        "SellerCustomerSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "group": {'required': True, 'version': 'SellerCustomerGroupSerializerDetail'},
                "seller_organisation": {'required': True, 'version': 'SellerCustomerOrgSerializerDetail'},
                "billing_email": {},
                "stripe_customer_id": {},
                "has_subscription": {'required': True},
                "notes": {},
                "created_at": {'required': True},
                "updated_at": {'required': True},
            },
        },
        "SellerCustomerSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "group": {'required': True, 'output_id': 'group_id'},
                "billing_email": {},
                "stripe_customer_id": {},
                "notes": {},
            },
        },
        "SellerCustomerSerializerList": {
            "fields": {
                "id": {'required': True},
                "group": {'required': True, 'version': 'SellerCustomerGroupSerializerList'},
                "seller_organisation": {'required': True, 'version': 'SellerCustomerOrgSerializerList'},
                "billing_email": {},
                "stripe_customer_id": {},
                "has_subscription": {'required': True},
                "created_at": {'required': True},
            },
        },
    }

class SellerCustomerGroup(ControlModel):
    _model_name = "SellerCustomerGroup"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "SellerCustomerGroupSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "SellerCustomerGroupSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class SellerCustomerOrg(ControlModel):
    _model_name = "SellerCustomerOrg"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "SellerCustomerOrgSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "SellerCustomerOrgSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class SharedDevice(ControlModel):
    _model_name = "SharedDevice"
    id: int
    device: str
    group: Group
    shared_profile: OrganisationSharedReceiveProfile
    organisation: Organisation
    def __init__(
        self,
        *,
        id: int | None = None,
        device: str | None = None,
        group: Group | dict[str, Any] | str | int | None = None,
        shared_profile: OrganisationSharedReceiveProfile | dict[str, Any] | str | int | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
    ) -> None:
        super().__init__(
            id=id,
            device=device,
            group=group,
            shared_profile=shared_profile,
            organisation=organisation,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "device": ControlField(type="string", nullable=False),
        "group": ControlField(type="resource", nullable=False, ref="Group"),
        "shared_profile": ControlField(type="resource", nullable=False, ref="OrganisationSharedReceiveProfile"),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
    }
    _versions = {
        "PatchedSharedDeviceSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "id": {},
                "device": {'output_id': 'device_id'},
                "group": {'output_id': 'group_id'},
                "shared_profile": {'output_id': 'shared_profile_id'},
            },
        },
        "SharedDeviceSerializerDetail": {
            "fields": {
                "id": {},
                "device": {'required': True},
                "organisation": {'version': 'BasicOrganisationDetail'},
                "group": {'required': True, 'version': 'GroupSerializerDetail'},
                "shared_profile": {'required': True, 'version': 'OrganisationSharedReceiveProfileSerializerDetail'},
            },
        },
        "SharedDeviceSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "id": {},
                "device": {'required': True, 'output_id': 'device_id'},
                "group": {'required': True, 'output_id': 'group_id'},
                "shared_profile": {'required': True, 'output_id': 'shared_profile_id'},
            },
        },
        "SharedDeviceSerializerList": {
            "fields": {
                "id": {},
                "device": {'required': True},
                "organisation": {'version': 'BasicOrganisationList'},
                "group": {'required': True, 'version': 'GroupSerializerList'},
                "shared_profile": {'required': True, 'version': 'OrganisationSharedReceiveProfileSerializerList'},
            },
        },
    }

class SharedGroup(ControlModel):
    _model_name = "SharedGroup"
    id: int
    group: Group
    shared_profile: OrganisationSharedReceiveProfile
    shared_group: str
    organisation: Organisation
    def __init__(
        self,
        *,
        id: int | None = None,
        group: Group | dict[str, Any] | str | int | None = None,
        shared_profile: OrganisationSharedReceiveProfile | dict[str, Any] | str | int | None = None,
        shared_group: str | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
    ) -> None:
        super().__init__(
            id=id,
            group=group,
            shared_profile=shared_profile,
            shared_group=shared_group,
            organisation=organisation,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "group": ControlField(type="resource", nullable=False, ref="Group"),
        "shared_profile": ControlField(type="resource", nullable=False, ref="OrganisationSharedReceiveProfile"),
        "shared_group": ControlField(type="string", nullable=False),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
    }
    _versions = {
        "PatchedSharedGroupSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "id": {},
                "group": {'output_id': 'group_id'},
                "shared_profile": {'output_id': 'shared_profile_id'},
                "shared_group": {'output_id': 'shared_group_id'},
            },
        },
        "SharedGroupSerializerDetail": {
            "fields": {
                "id": {},
                "organisation": {'version': 'BasicOrganisationDetail'},
                "group": {'required': True, 'version': 'GroupSerializerDetail'},
                "shared_profile": {'required': True, 'version': 'OrganisationSharedReceiveProfileSerializerDetail'},
                "shared_group": {'required': True, 'output_id': 'shared_group_id'},
            },
        },
        "SharedGroupSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "id": {},
                "group": {'required': True, 'output_id': 'group_id'},
                "shared_profile": {'required': True, 'output_id': 'shared_profile_id'},
                "shared_group": {'required': True, 'output_id': 'shared_group_id'},
            },
        },
        "SharedGroupSerializerList": {
            "fields": {
                "id": {},
                "organisation": {'version': 'BasicOrganisationList'},
                "group": {'required': True, 'version': 'GroupSerializerList'},
                "shared_profile": {'required': True, 'version': 'OrganisationSharedReceiveProfileSerializerList'},
                "shared_group": {'required': True, 'output_id': 'shared_group_id'},
            },
        },
    }

class Solution(ControlModel):
    _model_name = "Solution"
    display_name: str
    description: str
    jinja_template: str
    config_schema: Any
    config: Any
    id: int
    archived: bool
    application_templates: list[ApplicationTemplate]
    organisation: Organisation
    def __init__(
        self,
        *,
        display_name: str | None = None,
        description: str | None = None,
        jinja_template: str | None = None,
        config_schema: Any | None = None,
        config: Any | None = None,
        id: int | None = None,
        archived: bool | None = None,
        application_templates: list[ApplicationTemplate | dict[str, Any] | str | int] | None = None,
        organisation: Organisation | dict[str, Any] | str | int | None = None,
    ) -> None:
        super().__init__(
            display_name=display_name,
            description=description,
            jinja_template=jinja_template,
            config_schema=config_schema,
            config=config,
            id=id,
            archived=archived,
            application_templates=application_templates,
            organisation=organisation,
        )
    _field_defs = {
        "display_name": ControlField(type="string", nullable=False),
        "description": ControlField(type="string", nullable=False),
        "jinja_template": ControlField(type="string", nullable=False),
        "config_schema": ControlField(type="json", nullable=False),
        "config": ControlField(type="json", nullable=False),
        "id": ControlField(type="SnowflakeId", nullable=False),
        "archived": ControlField(type="boolean", nullable=False),
        "application_templates": ControlField(type="resource", nullable=False, is_array=True, ref="ApplicationTemplate"),
        "organisation": ControlField(type="resource", nullable=False, ref="Organisation"),
    }
    _versions = {
        "PatchedSolutionSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "display_name": {},
                "description": {},
                "jinja_template": {},
                "config_schema": {},
                "config": {},
            },
        },
        "SolutionSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "archived": {'required': True},
                "display_name": {'required': True},
                "description": {},
                "jinja_template": {},
                "config_schema": {},
                "config": {},
                "application_templates": {'required': True, 'version': 'ApplicationTemplateSerializerDetail'},
                "organisation": {'required': True, 'version': 'BasicOrganisationDetail'},
            },
        },
        "SolutionSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "display_name": {'required': True},
                "description": {},
                "jinja_template": {},
                "config_schema": {},
                "config": {},
            },
        },
        "SolutionSerializerList": {
            "fields": {
                "id": {'required': True},
                "archived": {'required': True},
                "display_name": {'required': True},
                "description": {},
                "jinja_template": {},
                "config_schema": {},
                "config": {},
                "application_templates": {'required': True, 'version': 'ApplicationTemplateSerializerList'},
                "organisation": {'required': True, 'version': 'BasicOrganisationList'},
            },
        },
    }

class SolutionInstallation(ControlModel):
    _model_name = "SolutionInstallation"
    display_name: str
    device: Device
    solution: Solution
    deployment_config: Any
    id: int
    deployed_at: str
    status: str
    application_installs: list[ApplicationInstallation]
    def __init__(
        self,
        *,
        display_name: str | None = None,
        device: Device | dict[str, Any] | str | int | None = None,
        solution: Solution | dict[str, Any] | str | int | None = None,
        deployment_config: Any | None = None,
        id: int | None = None,
        deployed_at: str | None = None,
        status: str | None = None,
        application_installs: list[ApplicationInstallation | dict[str, Any] | str | int] | None = None,
    ) -> None:
        super().__init__(
            display_name=display_name,
            device=device,
            solution=solution,
            deployment_config=deployment_config,
            id=id,
            deployed_at=deployed_at,
            status=status,
            application_installs=application_installs,
        )
    _field_defs = {
        "display_name": ControlField(type="string", nullable=False),
        "device": ControlField(type="resource", nullable=False, ref="Device"),
        "solution": ControlField(type="resource", nullable=False, ref="Solution"),
        "deployment_config": ControlField(type="json", nullable=False),
        "id": ControlField(type="SnowflakeId", nullable=False),
        "deployed_at": ControlField(type="string", nullable=False),
        "status": ControlField(type="string", nullable=False),
        "application_installs": ControlField(type="resource", nullable=False, is_array=True, ref="ApplicationInstallation"),
    }
    _versions = {
        "PatchedSolutionInstallationSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "display_name": {},
                "device": {'output_id': 'device_id'},
                "solution": {'output_id': 'solution_id'},
                "deployment_config": {},
            },
        },
        "SolutionInstallationSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "display_name": {'required': True},
                "device": {'required': True, 'version': 'DeviceSerializerDetail'},
                "deployed_at": {'required': True},
                "status": {'required': True},
                "application_installs": {'required': True, 'version': 'ApplicationInstallationSerializerDetail'},
                "solution": {'required': True, 'version': 'SolutionSerializerDetail'},
                "deployment_config": {},
            },
        },
        "SolutionInstallationSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "display_name": {'required': True},
                "device": {'required': True, 'output_id': 'device_id'},
                "solution": {'required': True, 'output_id': 'solution_id'},
                "deployment_config": {},
            },
        },
        "SolutionInstallationSerializerList": {
            "fields": {
                "id": {'required': True},
                "display_name": {'required': True},
                "device": {'required': True, 'version': 'DeviceSerializerList'},
                "deployed_at": {'required': True},
                "status": {'required': True},
                "application_installs": {'required': True, 'version': 'ApplicationInstallationSerializerList'},
                "solution": {'required': True, 'version': 'SolutionSerializerList'},
                "deployment_config": {},
            },
        },
    }

class Theme(ControlModel):
    _model_name = "Theme"
    accent_colour: str
    brand_logo_colour: str
    navbar_colour: str
    navbar_text_colour: str
    sidebar_colour: str
    sidebar_text_colour: str
    banner_image: str | None
    login_banner: str | None
    sidebar_banner_image: str | None
    site_logo: str | None
    id: int
    def __init__(
        self,
        *,
        accent_colour: str | None = None,
        brand_logo_colour: str | None = None,
        navbar_colour: str | None = None,
        navbar_text_colour: str | None = None,
        sidebar_colour: str | None = None,
        sidebar_text_colour: str | None = None,
        banner_image: str | None = None,
        login_banner: str | None = None,
        sidebar_banner_image: str | None = None,
        site_logo: str | None = None,
        id: int | None = None,
    ) -> None:
        super().__init__(
            accent_colour=accent_colour,
            brand_logo_colour=brand_logo_colour,
            navbar_colour=navbar_colour,
            navbar_text_colour=navbar_text_colour,
            sidebar_colour=sidebar_colour,
            sidebar_text_colour=sidebar_text_colour,
            banner_image=banner_image,
            login_banner=login_banner,
            sidebar_banner_image=sidebar_banner_image,
            site_logo=site_logo,
            id=id,
        )
    _field_defs = {
        "accent_colour": ControlField(type="string", nullable=False),
        "brand_logo_colour": ControlField(type="string", nullable=False),
        "navbar_colour": ControlField(type="string", nullable=False),
        "navbar_text_colour": ControlField(type="string", nullable=False),
        "sidebar_colour": ControlField(type="string", nullable=False),
        "sidebar_text_colour": ControlField(type="string", nullable=False),
        "banner_image": ControlField(type="string", nullable=True),
        "login_banner": ControlField(type="string", nullable=True),
        "sidebar_banner_image": ControlField(type="string", nullable=True),
        "site_logo": ControlField(type="string", nullable=True),
        "id": ControlField(type="SnowflakeId", nullable=False),
    }
    _versions = {
        "PatchedThemeSerializerWithIdDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "accent_colour": {},
                "brand_logo_colour": {},
                "navbar_colour": {},
                "navbar_text_colour": {},
                "sidebar_colour": {},
                "sidebar_text_colour": {},
                "banner_image": {},
                "login_banner": {},
                "sidebar_banner_image": {},
                "site_logo": {},
            },
        },
        "ThemeSerializerDetail": {
            "fields": {
                "accent_colour": {'required': True},
                "brand_logo_colour": {'required': True},
                "navbar_colour": {'required': True},
                "navbar_text_colour": {'required': True},
                "sidebar_colour": {'required': True},
                "sidebar_text_colour": {'required': True},
                "banner_image": {},
                "login_banner": {},
                "sidebar_banner_image": {},
                "site_logo": {},
            },
        },
        "ThemeSerializerDetailRequest": {
            "fields": {
                "accent_colour": {'required': True},
                "brand_logo_colour": {'required': True},
                "navbar_colour": {'required': True},
                "navbar_text_colour": {'required': True},
                "sidebar_colour": {'required': True},
                "sidebar_text_colour": {'required': True},
                "banner_image": {},
                "login_banner": {},
                "sidebar_banner_image": {},
                "site_logo": {},
            },
        },
        "ThemeSerializerList": {
            "fields": {
                "accent_colour": {'required': True},
                "brand_logo_colour": {'required': True},
                "navbar_colour": {'required': True},
                "navbar_text_colour": {'required': True},
                "sidebar_colour": {'required': True},
                "sidebar_text_colour": {'required': True},
                "banner_image": {},
                "login_banner": {},
                "sidebar_banner_image": {},
                "site_logo": {},
            },
        },
        "ThemeSerializerWithIdDetail": {
            "fields": {
                "id": {'required': True},
                "accent_colour": {'required': True},
                "brand_logo_colour": {'required': True},
                "navbar_colour": {'required': True},
                "navbar_text_colour": {'required': True},
                "sidebar_colour": {'required': True},
                "sidebar_text_colour": {'required': True},
                "banner_image": {},
                "login_banner": {},
                "sidebar_banner_image": {},
                "site_logo": {},
            },
        },
        "ThemeSerializerWithIdDetailRequest": {
            "methods": ['PUT'],
            "fields": {
                "accent_colour": {'required': True},
                "brand_logo_colour": {'required': True},
                "navbar_colour": {'required': True},
                "navbar_text_colour": {'required': True},
                "sidebar_colour": {'required': True},
                "sidebar_text_colour": {'required': True},
                "banner_image": {},
                "login_banner": {},
                "sidebar_banner_image": {},
                "site_logo": {},
            },
        },
        "ThemeSerializerWithIdList": {
            "fields": {
                "id": {'required': True},
                "accent_colour": {'required': True},
                "brand_logo_colour": {'required': True},
                "navbar_colour": {'required': True},
                "navbar_text_colour": {'required': True},
                "sidebar_colour": {'required': True},
                "sidebar_text_colour": {'required': True},
                "banner_image": {},
                "login_banner": {},
                "sidebar_banner_image": {},
                "site_logo": {},
            },
        },
    }

class Tunnel(ControlModel):
    _model_name = "Tunnel"
    name: str
    device: Device
    hostname: str
    port: int
    protocol: str
    username: str | None
    password: str | None
    timeout: int
    ip_restricted: bool
    disable_tls_verification: bool
    ip_whitelist: Any
    is_favourite: bool
    id: int
    endpoint: str
    is_active: bool
    def __init__(
        self,
        *,
        name: str | None = None,
        device: Device | dict[str, Any] | str | int | None = None,
        hostname: str | None = None,
        port: int | None = None,
        protocol: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: int | None = None,
        ip_restricted: bool | None = None,
        disable_tls_verification: bool | None = None,
        ip_whitelist: Any | None = None,
        is_favourite: bool | None = None,
        id: int | None = None,
        endpoint: str | None = None,
        is_active: bool | None = None,
    ) -> None:
        super().__init__(
            name=name,
            device=device,
            hostname=hostname,
            port=port,
            protocol=protocol,
            username=username,
            password=password,
            timeout=timeout,
            ip_restricted=ip_restricted,
            disable_tls_verification=disable_tls_verification,
            ip_whitelist=ip_whitelist,
            is_favourite=is_favourite,
            id=id,
            endpoint=endpoint,
            is_active=is_active,
        )
    _field_defs = {
        "name": ControlField(type="string", nullable=False),
        "device": ControlField(type="resource", nullable=False, ref="Device"),
        "hostname": ControlField(type="string", nullable=False),
        "port": ControlField(type="integer", nullable=False),
        "protocol": ControlField(type="string", nullable=False),
        "username": ControlField(type="string", nullable=True),
        "password": ControlField(type="string", nullable=True),
        "timeout": ControlField(type="integer", nullable=False),
        "ip_restricted": ControlField(type="boolean", nullable=False),
        "disable_tls_verification": ControlField(type="boolean", nullable=False),
        "ip_whitelist": ControlField(type="json", nullable=False),
        "is_favourite": ControlField(type="boolean", nullable=False),
        "id": ControlField(type="SnowflakeId", nullable=False),
        "endpoint": ControlField(type="string", nullable=False),
        "is_active": ControlField(type="boolean", nullable=False),
    }
    _versions = {
        "PatchedTunnelSerializerDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "name": {},
                "device": {'output_id': 'device_id'},
                "hostname": {},
                "port": {},
                "protocol": {},
                "username": {},
                "password": {},
                "timeout": {},
                "ip_restricted": {},
                "disable_tls_verification": {},
                "ip_whitelist": {},
                "is_favourite": {},
            },
        },
        "TunnelSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "device": {'required': True, 'version': 'DeviceSuperBasicSerialiserDetail'},
                "endpoint": {'required': True, 'output_id': 'endpoint_id'},
                "is_active": {'required': True},
                "hostname": {'required': True},
                "port": {'required': True},
                "protocol": {'required': True},
                "username": {},
                "password": {},
                "timeout": {},
                "ip_restricted": {},
                "disable_tls_verification": {},
                "ip_whitelist": {},
                "is_favourite": {},
            },
        },
        "TunnelSerializerDetailRequest": {
            "methods": ['POST', 'PUT'],
            "fields": {
                "name": {'required': True},
                "device": {'output_id': 'device_id'},
                "hostname": {'required': True},
                "port": {'required': True},
                "protocol": {'required': True},
                "username": {},
                "password": {},
                "timeout": {},
                "ip_restricted": {},
                "disable_tls_verification": {},
                "ip_whitelist": {},
                "is_favourite": {},
            },
        },
        "TunnelSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
                "device": {'required': True, 'version': 'DeviceSuperBasicSerialiserList'},
                "endpoint": {'required': True, 'output_id': 'endpoint_id'},
                "is_active": {'required': True},
                "hostname": {'required': True},
                "port": {'required': True},
                "protocol": {'required': True},
                "username": {},
                "password": {},
                "timeout": {},
                "ip_restricted": {},
                "disable_tls_verification": {},
                "ip_whitelist": {},
                "is_favourite": {},
            },
        },
    }

class UsageMeteringRun(ControlModel):
    _model_name = "UsageMeteringRun"
    id: int
    organisation: MeteringRunOrg
    started_at: str
    completed_at: str | None
    status: str
    devices_metered: int
    app_installs_metered: int
    agent_items_metered: int
    errors_count: int
    seller_customers_metered: int
    seller_usage_errors_count: int
    log_output: str
    def __init__(
        self,
        *,
        id: int | None = None,
        organisation: MeteringRunOrg | dict[str, Any] | str | int | None = None,
        started_at: str | None = None,
        completed_at: str | None = None,
        status: str | None = None,
        devices_metered: int | None = None,
        app_installs_metered: int | None = None,
        agent_items_metered: int | None = None,
        errors_count: int | None = None,
        seller_customers_metered: int | None = None,
        seller_usage_errors_count: int | None = None,
        log_output: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            organisation=organisation,
            started_at=started_at,
            completed_at=completed_at,
            status=status,
            devices_metered=devices_metered,
            app_installs_metered=app_installs_metered,
            agent_items_metered=agent_items_metered,
            errors_count=errors_count,
            seller_customers_metered=seller_customers_metered,
            seller_usage_errors_count=seller_usage_errors_count,
            log_output=log_output,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "organisation": ControlField(type="resource", nullable=False, ref="MeteringRunOrg"),
        "started_at": ControlField(type="string", nullable=False),
        "completed_at": ControlField(type="string", nullable=True),
        "status": ControlField(type="string", nullable=False),
        "devices_metered": ControlField(type="integer", nullable=False),
        "app_installs_metered": ControlField(type="integer", nullable=False),
        "agent_items_metered": ControlField(type="integer", nullable=False),
        "errors_count": ControlField(type="integer", nullable=False),
        "seller_customers_metered": ControlField(type="integer", nullable=False),
        "seller_usage_errors_count": ControlField(type="integer", nullable=False),
        "log_output": ControlField(type="string", nullable=False),
    }
    _versions = {
        "UsageMeteringRunSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "organisation": {'required': True, 'version': 'MeteringRunOrgSerializerDetail'},
                "started_at": {'required': True},
                "completed_at": {'required': True},
                "status": {'required': True},
                "devices_metered": {'required': True},
                "app_installs_metered": {'required': True},
                "agent_items_metered": {'required': True},
                "errors_count": {'required': True},
                "seller_customers_metered": {'required': True},
                "seller_usage_errors_count": {'required': True},
                "log_output": {'required': True},
            },
        },
        "UsageMeteringRunSerializerList": {
            "fields": {
                "id": {'required': True},
                "organisation": {'required': True, 'version': 'MeteringRunOrgSerializerList'},
                "started_at": {'required': True},
                "completed_at": {'required': True},
                "status": {'required': True},
                "devices_metered": {'required': True},
                "app_installs_metered": {'required': True},
                "agent_items_metered": {'required': True},
                "errors_count": {'required': True},
                "seller_customers_metered": {'required': True},
                "seller_usage_errors_count": {'required': True},
            },
        },
    }

class UsageRecord(ControlModel):
    _model_name = "UsageRecord"
    id: int
    metering_run: str
    organisation: UsageRecordOrg
    subscription_item: str | None
    record_type: str
    device: UsageRecordDevice
    app_install: UsageRecordAppInstall
    agent_billing_item: str | None
    seller_customer: str
    billing_product: UsageRecordBillingProduct
    quantity: int
    revenue_target: str
    developer_amount_cents: int
    platform_fee_cents: int
    device_online: bool | None
    unit_amount_cents: int
    created_at: str
    def __init__(
        self,
        *,
        id: int | None = None,
        metering_run: str | None = None,
        organisation: UsageRecordOrg | dict[str, Any] | str | int | None = None,
        subscription_item: str | None = None,
        record_type: str | None = None,
        device: UsageRecordDevice | dict[str, Any] | str | int | None = None,
        app_install: UsageRecordAppInstall | dict[str, Any] | str | int | None = None,
        agent_billing_item: str | None = None,
        seller_customer: str | None = None,
        billing_product: UsageRecordBillingProduct | dict[str, Any] | str | int | None = None,
        quantity: int | None = None,
        revenue_target: str | None = None,
        developer_amount_cents: int | None = None,
        platform_fee_cents: int | None = None,
        device_online: bool | None = None,
        unit_amount_cents: int | None = None,
        created_at: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            metering_run=metering_run,
            organisation=organisation,
            subscription_item=subscription_item,
            record_type=record_type,
            device=device,
            app_install=app_install,
            agent_billing_item=agent_billing_item,
            seller_customer=seller_customer,
            billing_product=billing_product,
            quantity=quantity,
            revenue_target=revenue_target,
            developer_amount_cents=developer_amount_cents,
            platform_fee_cents=platform_fee_cents,
            device_online=device_online,
            unit_amount_cents=unit_amount_cents,
            created_at=created_at,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "metering_run": ControlField(type="string", nullable=False),
        "organisation": ControlField(type="resource", nullable=False, ref="UsageRecordOrg"),
        "subscription_item": ControlField(type="string", nullable=True),
        "record_type": ControlField(type="string", nullable=False),
        "device": ControlField(type="resource", nullable=False, ref="UsageRecordDevice"),
        "app_install": ControlField(type="resource", nullable=False, ref="UsageRecordAppInstall"),
        "agent_billing_item": ControlField(type="string", nullable=True),
        "seller_customer": ControlField(type="string", nullable=False),
        "billing_product": ControlField(type="resource", nullable=False, ref="UsageRecordBillingProduct"),
        "quantity": ControlField(type="integer", nullable=False),
        "revenue_target": ControlField(type="string", nullable=False),
        "developer_amount_cents": ControlField(type="integer", nullable=False),
        "platform_fee_cents": ControlField(type="integer", nullable=False),
        "device_online": ControlField(type="boolean", nullable=True),
        "unit_amount_cents": ControlField(type="integer", nullable=False),
        "created_at": ControlField(type="string", nullable=False),
    }
    _versions = {
        "UsageRecordSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "metering_run": {'required': True},
                "organisation": {'required': True, 'version': 'UsageRecordOrgSerializerDetail'},
                "subscription_item": {'required': True},
                "record_type": {'required': True},
                "device": {'required': True, 'version': 'UsageRecordDeviceSerializerDetail'},
                "app_install": {'required': True, 'version': 'UsageRecordAppInstallSerializerDetail'},
                "agent_billing_item": {'required': True},
                "seller_customer": {'required': True},
                "billing_product": {'required': True, 'version': 'UsageRecordBillingProductSerializerDetail'},
                "quantity": {'required': True},
                "revenue_target": {'required': True},
                "developer_amount_cents": {'required': True},
                "platform_fee_cents": {'required': True},
                "device_online": {'required': True},
                "unit_amount_cents": {'required': True},
                "created_at": {'required': True},
            },
        },
        "UsageRecordSerializerList": {
            "fields": {
                "id": {'required': True},
                "metering_run": {'required': True},
                "organisation": {'required': True, 'version': 'UsageRecordOrgSerializerList'},
                "subscription_item": {'required': True},
                "record_type": {'required': True},
                "device": {'required': True, 'version': 'UsageRecordDeviceSerializerList'},
                "app_install": {'required': True, 'version': 'UsageRecordAppInstallSerializerList'},
                "agent_billing_item": {'required': True},
                "seller_customer": {'required': True},
                "billing_product": {'required': True, 'version': 'UsageRecordBillingProductSerializerList'},
                "quantity": {'required': True},
                "revenue_target": {'required': True},
                "developer_amount_cents": {'required': True},
                "platform_fee_cents": {'required': True},
                "device_online": {'required': True},
                "unit_amount_cents": {'required': True},
                "created_at": {'required': True},
            },
        },
    }

class UsageRecordAppInstall(ControlModel):
    _model_name = "UsageRecordAppInstall"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "UsageRecordAppInstallSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "UsageRecordAppInstallSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class UsageRecordBillingProduct(ControlModel):
    _model_name = "UsageRecordBillingProduct"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "UsageRecordBillingProductSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "UsageRecordBillingProductSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class UsageRecordDevice(ControlModel):
    _model_name = "UsageRecordDevice"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "UsageRecordDeviceSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "UsageRecordDeviceSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class UsageRecordOrg(ControlModel):
    _model_name = "UsageRecordOrg"
    id: int
    name: str
    def __init__(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )
    _field_defs = {
        "id": ControlField(type="SnowflakeId", nullable=False),
        "name": ControlField(type="string", nullable=False),
    }
    _versions = {
        "UsageRecordOrgSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
        "UsageRecordOrgSerializerList": {
            "fields": {
                "id": {'required': True},
                "name": {'required': True},
            },
        },
    }

class User(ControlModel):
    _model_name = "User"
    custom_data: Any | None
    id: int
    email: str
    first_name: str
    last_name: str
    fusionauth_id: str | None
    username: str
    is_superuser: bool
    organisation_info: str
    def __init__(
        self,
        *,
        custom_data: Any | None = None,
        id: int | None = None,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        fusionauth_id: str | None = None,
        username: str | None = None,
        is_superuser: bool | None = None,
        organisation_info: str | None = None,
    ) -> None:
        super().__init__(
            custom_data=custom_data,
            id=id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            fusionauth_id=fusionauth_id,
            username=username,
            is_superuser=is_superuser,
            organisation_info=organisation_info,
        )
    _field_defs = {
        "custom_data": ControlField(type="json", nullable=True),
        "id": ControlField(type="SnowflakeId", nullable=False),
        "email": ControlField(type="string", nullable=False),
        "first_name": ControlField(type="string", nullable=False),
        "last_name": ControlField(type="string", nullable=False),
        "fusionauth_id": ControlField(type="id", nullable=True),
        "username": ControlField(type="string", nullable=False),
        "is_superuser": ControlField(type="boolean", nullable=False),
        "organisation_info": ControlField(type="string", nullable=False),
    }
    _versions = {
        "PatchedUserSerialiserDetailRequest": {
            "methods": ['PATCH'],
            "fields": {
                "custom_data": {},
            },
        },
        "UserBasicSerializerDetail": {
            "fields": {
                "id": {'required': True},
                "email": {'required': True},
                "first_name": {'required': True},
                "last_name": {'required': True},
            },
        },
        "UserBasicSerializerList": {
            "fields": {
                "id": {'required': True},
                "email": {'required': True},
                "first_name": {'required': True},
                "last_name": {'required': True},
            },
        },
        "UserSerialiserDetail": {
            "fields": {
                "id": {'required': True},
                "fusionauth_id": {'required': True},
                "username": {'required': True},
                "email": {'required': True},
                "first_name": {'required': True},
                "last_name": {'required': True},
                "is_superuser": {'required': True},
                "organisation_info": {'required': True},
                "custom_data": {},
            },
        },
        "UserSerialiserDetailRequest": {
            "methods": ['PUT'],
            "fields": {
                "custom_data": {},
            },
        },
        "UserSerialiserList": {
            "fields": {
                "id": {'required': True},
                "fusionauth_id": {'required': True},
                "username": {'required': True},
                "email": {'required': True},
                "first_name": {'required': True},
                "last_name": {'required': True},
                "is_superuser": {'required': True},
                "organisation_info": {'required': True},
                "custom_data": {},
            },
        },
    }

CONTROL_SCHEMA_REGISTRY = {'AIChatMessageSerializerDetail': {'kind': 'model', 'model': 'AIChatMessage', 'version': 'AIChatMessageSerializerDetail'}, 'AIChatMessageSerializerList': {'kind': 'model', 'model': 'AIChatMessage', 'version': 'AIChatMessageSerializerList'}, 'AIChatSessionDetailSerializerDetail': {'kind': 'model', 'model': 'AIChatSession', 'version': 'AIChatSessionDetailSerializerDetail'}, 'AIChatSessionSerializerList': {'kind': 'model', 'model': 'AIChatSession', 'version': 'AIChatSessionSerializerList'}, 'AgentBillingItemSerializerDetail': {'kind': 'model', 'model': 'AgentBillingItem', 'version': 'AgentBillingItemSerializerDetail'}, 'AgentBillingItemSerializerDetailRequest': {'kind': 'model', 'model': 'AgentBillingItem', 'version': 'AgentBillingItemSerializerDetailRequest'}, 'AgentBillingItemSerializerList': {'kind': 'model', 'model': 'AgentBillingItem', 'version': 'AgentBillingItemSerializerList'}, 'PatchedAgentBillingItemSerializerDetailRequest': {'kind': 'model', 'model': 'AgentBillingItem', 'version': 'PatchedAgentBillingItemSerializerDetailRequest'}, 'AgentItemDeviceSerializerDetail': {'kind': 'model', 'model': 'AgentItemDevice', 'version': 'AgentItemDeviceSerializerDetail'}, 'AgentItemDeviceSerializerList': {'kind': 'model', 'model': 'AgentItemDevice', 'version': 'AgentItemDeviceSerializerList'}, 'AgentItemOrgSerializerDetail': {'kind': 'model', 'model': 'AgentItemOrg', 'version': 'AgentItemOrgSerializerDetail'}, 'AgentItemOrgSerializerList': {'kind': 'model', 'model': 'AgentItemOrg', 'version': 'AgentItemOrgSerializerList'}, 'AgentItemProductSerializerDetail': {'kind': 'model', 'model': 'AgentItemProduct', 'version': 'AgentItemProductSerializerDetail'}, 'AgentItemProductSerializerList': {'kind': 'model', 'model': 'AgentItemProduct', 'version': 'AgentItemProductSerializerList'}, 'AppBillingConfigAppSerializerDetail': {'kind': 'model', 'model': 'AppBillingConfigApp', 'version': 'AppBillingConfigAppSerializerDetail'}, 'AppBillingConfigAppSerializerList': {'kind': 'model', 'model': 'AppBillingConfigApp', 'version': 'AppBillingConfigAppSerializerList'}, 'AppBillingConfigOwnerOrgSerializerDetail': {'kind': 'model', 'model': 'AppBillingConfigOwnerOrg', 'version': 'AppBillingConfigOwnerOrgSerializerDetail'}, 'AppBillingConfigOwnerOrgSerializerList': {'kind': 'model', 'model': 'AppBillingConfigOwnerOrg', 'version': 'AppBillingConfigOwnerOrgSerializerList'}, 'AppBillingConfigProductSerializerDetail': {'kind': 'model', 'model': 'AppBillingConfigProduct', 'version': 'AppBillingConfigProductSerializerDetail'}, 'AppBillingConfigProductSerializerList': {'kind': 'model', 'model': 'AppBillingConfigProduct', 'version': 'AppBillingConfigProductSerializerList'}, 'AppBillingConfigSerializerDetail': {'kind': 'model', 'model': 'AppBillingConfig', 'version': 'AppBillingConfigSerializerDetail'}, 'AppBillingConfigSerializerDetailRequest': {'kind': 'model', 'model': 'AppBillingConfig', 'version': 'AppBillingConfigSerializerDetailRequest'}, 'AppBillingConfigSerializerList': {'kind': 'model', 'model': 'AppBillingConfig', 'version': 'AppBillingConfigSerializerList'}, 'PatchedAppBillingConfigSerializerDetailRequest': {'kind': 'model', 'model': 'AppBillingConfig', 'version': 'PatchedAppBillingConfigSerializerDetailRequest'}, 'ApplicationConfigProfileSerializerDetail': {'kind': 'model', 'model': 'ApplicationConfigProfile', 'version': 'ApplicationConfigProfileSerializerDetail'}, 'ApplicationConfigProfileSerializerDetailRequest': {'kind': 'model', 'model': 'ApplicationConfigProfile', 'version': 'ApplicationConfigProfileSerializerDetailRequest'}, 'ApplicationConfigProfileSerializerList': {'kind': 'model', 'model': 'ApplicationConfigProfile', 'version': 'ApplicationConfigProfileSerializerList'}, 'PatchedApplicationConfigProfileSerializerDetailRequest': {'kind': 'model', 'model': 'ApplicationConfigProfile', 'version': 'PatchedApplicationConfigProfileSerializerDetailRequest'}, 'SlimApplicationConfigProfileSerializerDetail': {'kind': 'model', 'model': 'ApplicationConfigProfile', 'version': 'SlimApplicationConfigProfileSerializerDetail'}, 'SlimApplicationConfigProfileSerializerDetailRequest': {'kind': 'model', 'model': 'ApplicationConfigProfile', 'version': 'SlimApplicationConfigProfileSerializerDetailRequest'}, 'SlimApplicationConfigProfileSerializerList': {'kind': 'model', 'model': 'ApplicationConfigProfile', 'version': 'SlimApplicationConfigProfileSerializerList'}, 'ApplicationDeploymentSerializerDetail': {'kind': 'model', 'model': 'ApplicationDeployment', 'version': 'ApplicationDeploymentSerializerDetail'}, 'ApplicationDeploymentSerializerDetailRequest': {'kind': 'model', 'model': 'ApplicationDeployment', 'version': 'ApplicationDeploymentSerializerDetailRequest'}, 'ApplicationDeploymentSerializerList': {'kind': 'model', 'model': 'ApplicationDeployment', 'version': 'ApplicationDeploymentSerializerList'}, 'ApplicationInstallationSerializerDetail': {'kind': 'model', 'model': 'ApplicationInstallation', 'version': 'ApplicationInstallationSerializerDetail'}, 'ApplicationInstallationSerializerDetailRequest': {'kind': 'model', 'model': 'ApplicationInstallation', 'version': 'ApplicationInstallationSerializerDetailRequest'}, 'ApplicationInstallationSerializerList': {'kind': 'model', 'model': 'ApplicationInstallation', 'version': 'ApplicationInstallationSerializerList'}, 'PatchedApplicationInstallationSerializerDetailRequest': {'kind': 'model', 'model': 'ApplicationInstallation', 'version': 'PatchedApplicationInstallationSerializerDetailRequest'}, 'ApplicationSerializerDetail': {'kind': 'model', 'model': 'Application', 'version': 'ApplicationSerializerDetail'}, 'ApplicationSerializerDetailRequest': {'kind': 'model', 'model': 'Application', 'version': 'ApplicationSerializerDetailRequest'}, 'ApplicationSerializerList': {'kind': 'model', 'model': 'Application', 'version': 'ApplicationSerializerList'}, 'PatchedApplicationSerializerDetailRequest': {'kind': 'model', 'model': 'Application', 'version': 'PatchedApplicationSerializerDetailRequest'}, 'PublicApplicationSerializerList': {'kind': 'model', 'model': 'Application', 'version': 'PublicApplicationSerializerList'}, 'SlimApplicationDetail': {'kind': 'model', 'model': 'Application', 'version': 'SlimApplicationDetail'}, 'SlimApplicationList': {'kind': 'model', 'model': 'Application', 'version': 'SlimApplicationList'}, 'ApplicationTemplateSerializerDetail': {'kind': 'model', 'model': 'ApplicationTemplate', 'version': 'ApplicationTemplateSerializerDetail'}, 'ApplicationTemplateSerializerDetailRequest': {'kind': 'model', 'model': 'ApplicationTemplate', 'version': 'ApplicationTemplateSerializerDetailRequest'}, 'ApplicationTemplateSerializerList': {'kind': 'model', 'model': 'ApplicationTemplate', 'version': 'ApplicationTemplateSerializerList'}, 'PatchedApplicationTemplateSerializerDetailRequest': {'kind': 'model', 'model': 'ApplicationTemplate', 'version': 'PatchedApplicationTemplateSerializerDetailRequest'}, 'AttachmentSerializerDetail': {'kind': 'model', 'model': 'Attachment', 'version': 'AttachmentSerializerDetail'}, 'AttachmentSerializerList': {'kind': 'model', 'model': 'Attachment', 'version': 'AttachmentSerializerList'}, 'BasicGroupRoleDetail': {'kind': 'model', 'model': 'GroupRole', 'version': 'BasicGroupRoleDetail'}, 'BasicGroupRoleList': {'kind': 'model', 'model': 'GroupRole', 'version': 'BasicGroupRoleList'}, 'GroupRoleSerializerDetail': {'kind': 'model', 'model': 'GroupRole', 'version': 'GroupRoleSerializerDetail'}, 'GroupRoleSerializerDetailRequest': {'kind': 'model', 'model': 'GroupRole', 'version': 'GroupRoleSerializerDetailRequest'}, 'GroupRoleSerializerList': {'kind': 'model', 'model': 'GroupRole', 'version': 'GroupRoleSerializerList'}, 'PatchedGroupRoleSerializerDetailRequest': {'kind': 'model', 'model': 'GroupRole', 'version': 'PatchedGroupRoleSerializerDetailRequest'}, 'BasicOrganisationDetail': {'kind': 'model', 'model': 'Organisation', 'version': 'BasicOrganisationDetail'}, 'BasicOrganisationList': {'kind': 'model', 'model': 'Organisation', 'version': 'BasicOrganisationList'}, 'OrganisationBasicSerializerDetail': {'kind': 'model', 'model': 'Organisation', 'version': 'OrganisationBasicSerializerDetail'}, 'OrganisationBasicSerializerList': {'kind': 'model', 'model': 'Organisation', 'version': 'OrganisationBasicSerializerList'}, 'OrganisationSerializerDetail': {'kind': 'model', 'model': 'Organisation', 'version': 'OrganisationSerializerDetail'}, 'OrganisationSerializerDetailRequest': {'kind': 'model', 'model': 'Organisation', 'version': 'OrganisationSerializerDetailRequest'}, 'OrganisationSerializerList': {'kind': 'model', 'model': 'Organisation', 'version': 'OrganisationSerializerList'}, 'OrganisationSimpleSerialiserDetail': {'kind': 'model', 'model': 'Organisation', 'version': 'OrganisationSimpleSerialiserDetail'}, 'OrganisationSimpleSerialiserList': {'kind': 'model', 'model': 'Organisation', 'version': 'OrganisationSimpleSerialiserList'}, 'OrganisationSuperBasicSerialiserDetail': {'kind': 'model', 'model': 'Organisation', 'version': 'OrganisationSuperBasicSerialiserDetail'}, 'OrganisationSuperBasicSerialiserList': {'kind': 'model', 'model': 'Organisation', 'version': 'OrganisationSuperBasicSerialiserList'}, 'PatchedOrganisationSerializerDetailRequest': {'kind': 'model', 'model': 'Organisation', 'version': 'PatchedOrganisationSerializerDetailRequest'}, 'BillingAccountSerializerDetail': {'kind': 'model', 'model': 'BillingAccount', 'version': 'BillingAccountSerializerDetail'}, 'BillingAccountSerializerDetailRequest': {'kind': 'model', 'model': 'BillingAccount', 'version': 'BillingAccountSerializerDetailRequest'}, 'BillingAccountSerializerList': {'kind': 'model', 'model': 'BillingAccount', 'version': 'BillingAccountSerializerList'}, 'PatchedBillingAccountSerializerDetailRequest': {'kind': 'model', 'model': 'BillingAccount', 'version': 'PatchedBillingAccountSerializerDetailRequest'}, 'BillingProductOrgSerializerDetail': {'kind': 'model', 'model': 'BillingProductOrg', 'version': 'BillingProductOrgSerializerDetail'}, 'BillingProductSerializerDetail': {'kind': 'model', 'model': 'BillingProduct', 'version': 'BillingProductSerializerDetail'}, 'BillingProductSerializerDetailRequest': {'kind': 'model', 'model': 'BillingProduct', 'version': 'BillingProductSerializerDetailRequest'}, 'BillingProductSerializerList': {'kind': 'model', 'model': 'BillingProduct', 'version': 'BillingProductSerializerList'}, 'PatchedBillingProductSerializerDetailRequest': {'kind': 'model', 'model': 'BillingProduct', 'version': 'PatchedBillingProductSerializerDetailRequest'}, 'BillingSubscriptionItemSerializerDetail': {'kind': 'model', 'model': 'BillingSubscriptionItem', 'version': 'BillingSubscriptionItemSerializerDetail'}, 'BillingSubscriptionSerializerDetail': {'kind': 'model', 'model': 'BillingSubscription', 'version': 'BillingSubscriptionSerializerDetail'}, 'BillingSubscriptionSerializerList': {'kind': 'model', 'model': 'BillingSubscription', 'version': 'BillingSubscriptionSerializerList'}, 'ContainerRegistryProfileSeraliserDetail': {'kind': 'model', 'model': 'ContainerRegistryProfile', 'version': 'ContainerRegistryProfileSeraliserDetail'}, 'ContainerRegistryProfileSeraliserDetailRequest': {'kind': 'model', 'model': 'ContainerRegistryProfile', 'version': 'ContainerRegistryProfileSeraliserDetailRequest'}, 'ContainerRegistryProfileSeraliserList': {'kind': 'model', 'model': 'ContainerRegistryProfile', 'version': 'ContainerRegistryProfileSeraliserList'}, 'PatchedContainerRegistryProfileSeraliserDetailRequest': {'kind': 'model', 'model': 'ContainerRegistryProfile', 'version': 'PatchedContainerRegistryProfileSeraliserDetailRequest'}, 'CustomerSiteSerializerDetail': {'kind': 'model', 'model': 'CustomerSite', 'version': 'CustomerSiteSerializerDetail'}, 'DTBillingConfigDeviceTypeSerializerDetail': {'kind': 'model', 'model': 'DTBillingConfigDeviceType', 'version': 'DTBillingConfigDeviceTypeSerializerDetail'}, 'DTBillingConfigDeviceTypeSerializerList': {'kind': 'model', 'model': 'DTBillingConfigDeviceType', 'version': 'DTBillingConfigDeviceTypeSerializerList'}, 'DTBillingConfigOwnerOrgSerializerDetail': {'kind': 'model', 'model': 'DTBillingConfigOwnerOrg', 'version': 'DTBillingConfigOwnerOrgSerializerDetail'}, 'DTBillingConfigOwnerOrgSerializerList': {'kind': 'model', 'model': 'DTBillingConfigOwnerOrg', 'version': 'DTBillingConfigOwnerOrgSerializerList'}, 'DTBillingConfigProductSerializerDetail': {'kind': 'model', 'model': 'DTBillingConfigProduct', 'version': 'DTBillingConfigProductSerializerDetail'}, 'DTBillingConfigProductSerializerList': {'kind': 'model', 'model': 'DTBillingConfigProduct', 'version': 'DTBillingConfigProductSerializerList'}, 'DeviceBillingConfigSerializerDetail': {'kind': 'model', 'model': 'DeviceBillingConfig', 'version': 'DeviceBillingConfigSerializerDetail'}, 'DeviceBillingConfigSerializerDetailRequest': {'kind': 'model', 'model': 'DeviceBillingConfig', 'version': 'DeviceBillingConfigSerializerDetailRequest'}, 'DeviceBillingConfigSerializerList': {'kind': 'model', 'model': 'DeviceBillingConfig', 'version': 'DeviceBillingConfigSerializerList'}, 'PatchedDeviceBillingConfigSerializerDetailRequest': {'kind': 'model', 'model': 'DeviceBillingConfig', 'version': 'PatchedDeviceBillingConfigSerializerDetailRequest'}, 'DeviceSerializerDetail': {'kind': 'model', 'model': 'Device', 'version': 'DeviceSerializerDetail'}, 'DeviceSerializerDetailRequest': {'kind': 'model', 'model': 'Device', 'version': 'DeviceSerializerDetailRequest'}, 'DeviceSerializerList': {'kind': 'model', 'model': 'Device', 'version': 'DeviceSerializerList'}, 'DeviceSuperBasicSerialiserDetail': {'kind': 'model', 'model': 'Device', 'version': 'DeviceSuperBasicSerialiserDetail'}, 'DeviceSuperBasicSerialiserList': {'kind': 'model', 'model': 'Device', 'version': 'DeviceSuperBasicSerialiserList'}, 'PatchedDeviceSerializerDetailRequest': {'kind': 'model', 'model': 'Device', 'version': 'PatchedDeviceSerializerDetailRequest'}, 'DeviceTypeBillingConfigSerializerDetail': {'kind': 'model', 'model': 'DeviceTypeBillingConfig', 'version': 'DeviceTypeBillingConfigSerializerDetail'}, 'DeviceTypeBillingConfigSerializerDetailRequest': {'kind': 'model', 'model': 'DeviceTypeBillingConfig', 'version': 'DeviceTypeBillingConfigSerializerDetailRequest'}, 'DeviceTypeBillingConfigSerializerList': {'kind': 'model', 'model': 'DeviceTypeBillingConfig', 'version': 'DeviceTypeBillingConfigSerializerList'}, 'PatchedDeviceTypeBillingConfigSerializerDetailRequest': {'kind': 'model', 'model': 'DeviceTypeBillingConfig', 'version': 'PatchedDeviceTypeBillingConfigSerializerDetailRequest'}, 'DeviceTypeSerializerDetail': {'kind': 'model', 'model': 'DeviceType', 'version': 'DeviceTypeSerializerDetail'}, 'DeviceTypeSerializerDetailRequest': {'kind': 'model', 'model': 'DeviceType', 'version': 'DeviceTypeSerializerDetailRequest'}, 'DeviceTypeSerializerList': {'kind': 'model', 'model': 'DeviceType', 'version': 'DeviceTypeSerializerList'}, 'PatchedDeviceTypeSerializerDetailRequest': {'kind': 'model', 'model': 'DeviceType', 'version': 'PatchedDeviceTypeSerializerDetailRequest'}, 'GroupBasicSerialiserDetail': {'kind': 'model', 'model': 'Group', 'version': 'GroupBasicSerialiserDetail'}, 'GroupBasicSerialiserList': {'kind': 'model', 'model': 'Group', 'version': 'GroupBasicSerialiserList'}, 'GroupChildrenSerialiserDetail': {'kind': 'model', 'model': 'Group', 'version': 'GroupChildrenSerialiserDetail'}, 'GroupParentSerialiserDetail': {'kind': 'model', 'model': 'Group', 'version': 'GroupParentSerialiserDetail'}, 'GroupSerializerDetail': {'kind': 'model', 'model': 'Group', 'version': 'GroupSerializerDetail'}, 'GroupSerializerDetailRequest': {'kind': 'model', 'model': 'Group', 'version': 'GroupSerializerDetailRequest'}, 'GroupSerializerList': {'kind': 'model', 'model': 'Group', 'version': 'GroupSerializerList'}, 'PatchedGroupSerializerDetailRequest': {'kind': 'model', 'model': 'Group', 'version': 'PatchedGroupSerializerDetailRequest'}, 'GroupPermissionSerializerDetail': {'kind': 'model', 'model': 'GroupPermission', 'version': 'GroupPermissionSerializerDetail'}, 'GroupPermissionSerializerDetailRequest': {'kind': 'model', 'model': 'GroupPermission', 'version': 'GroupPermissionSerializerDetailRequest'}, 'GroupPermissionSerializerList': {'kind': 'model', 'model': 'GroupPermission', 'version': 'GroupPermissionSerializerList'}, 'PatchedGroupPermissionSerializerDetailRequest': {'kind': 'model', 'model': 'GroupPermission', 'version': 'PatchedGroupPermissionSerializerDetailRequest'}, 'GroupRoleAssignmentSerializerDetailRequest': {'kind': 'model', 'model': 'GroupRoleAssignment', 'version': 'GroupRoleAssignmentSerializerDetailRequest'}, 'IngestionEndpointSerializerDetail': {'kind': 'model', 'model': 'IngestionEndpoint', 'version': 'IngestionEndpointSerializerDetail'}, 'IngestionEndpointSerializerDetailRequest': {'kind': 'model', 'model': 'IngestionEndpoint', 'version': 'IngestionEndpointSerializerDetailRequest'}, 'IngestionEndpointSerializerList': {'kind': 'model', 'model': 'IngestionEndpoint', 'version': 'IngestionEndpointSerializerList'}, 'IntegrationSerializerDetail': {'kind': 'model', 'model': 'Integration', 'version': 'IntegrationSerializerDetail'}, 'IntegrationSerializerDetailRequest': {'kind': 'model', 'model': 'Integration', 'version': 'IntegrationSerializerDetailRequest'}, 'IntegrationSerializerList': {'kind': 'model', 'model': 'Integration', 'version': 'IntegrationSerializerList'}, 'PatchedIntegrationSerializerDetailRequest': {'kind': 'model', 'model': 'Integration', 'version': 'PatchedIntegrationSerializerDetailRequest'}, 'MeteringRunOrgSerializerDetail': {'kind': 'model', 'model': 'MeteringRunOrg', 'version': 'MeteringRunOrgSerializerDetail'}, 'MeteringRunOrgSerializerList': {'kind': 'model', 'model': 'MeteringRunOrg', 'version': 'MeteringRunOrgSerializerList'}, 'OrganisationDomainSerializerDetail': {'kind': 'model', 'model': 'OrganisationDomain', 'version': 'OrganisationDomainSerializerDetail'}, 'OrganisationDomainSerializerDetailRequest': {'kind': 'model', 'model': 'OrganisationDomain', 'version': 'OrganisationDomainSerializerDetailRequest'}, 'OrganisationDomainSerializerList': {'kind': 'model', 'model': 'OrganisationDomain', 'version': 'OrganisationDomainSerializerList'}, 'PatchedOrganisationDomainSerializerDetailRequest': {'kind': 'model', 'model': 'OrganisationDomain', 'version': 'PatchedOrganisationDomainSerializerDetailRequest'}, 'OrganisationRoleSerializerDetail': {'kind': 'model', 'model': 'OrganisationRole', 'version': 'OrganisationRoleSerializerDetail'}, 'OrganisationRoleSerializerDetailRequest': {'kind': 'model', 'model': 'OrganisationRole', 'version': 'OrganisationRoleSerializerDetailRequest'}, 'OrganisationRoleSerializerList': {'kind': 'model', 'model': 'OrganisationRole', 'version': 'OrganisationRoleSerializerList'}, 'PatchedOrganisationRoleSerializerDetailRequest': {'kind': 'model', 'model': 'OrganisationRole', 'version': 'PatchedOrganisationRoleSerializerDetailRequest'}, 'OrganisationSharedReceiveProfileSerializerDetail': {'kind': 'model', 'model': 'OrganisationSharedReceiveProfile', 'version': 'OrganisationSharedReceiveProfileSerializerDetail'}, 'OrganisationSharedReceiveProfileSerializerDetailRequest': {'kind': 'model', 'model': 'OrganisationSharedReceiveProfile', 'version': 'OrganisationSharedReceiveProfileSerializerDetailRequest'}, 'OrganisationSharedReceiveProfileSerializerList': {'kind': 'model', 'model': 'OrganisationSharedReceiveProfile', 'version': 'OrganisationSharedReceiveProfileSerializerList'}, 'PatchedOrganisationSharedReceiveProfileSerializerDetailRequest': {'kind': 'model', 'model': 'OrganisationSharedReceiveProfile', 'version': 'PatchedOrganisationSharedReceiveProfileSerializerDetailRequest'}, 'OrganisationSharingProfileSerializerDetail': {'kind': 'model', 'model': 'OrganisationSharingProfile', 'version': 'OrganisationSharingProfileSerializerDetail'}, 'OrganisationSharingProfileSerializerDetailRequest': {'kind': 'model', 'model': 'OrganisationSharingProfile', 'version': 'OrganisationSharingProfileSerializerDetailRequest'}, 'OrganisationSharingProfileSerializerList': {'kind': 'model', 'model': 'OrganisationSharingProfile', 'version': 'OrganisationSharingProfileSerializerList'}, 'PatchedOrganisationSharingProfileSerializerDetailRequest': {'kind': 'model', 'model': 'OrganisationSharingProfile', 'version': 'PatchedOrganisationSharingProfileSerializerDetailRequest'}, 'OrganisationUserSerializerDetail': {'kind': 'model', 'model': 'OrganisationUser', 'version': 'OrganisationUserSerializerDetail'}, 'OrganisationUserSerializerDetailRequest': {'kind': 'model', 'model': 'OrganisationUser', 'version': 'OrganisationUserSerializerDetailRequest'}, 'OrganisationUserSerializerList': {'kind': 'model', 'model': 'OrganisationUser', 'version': 'OrganisationUserSerializerList'}, 'PatchedOrganisationUserSerializerDetailRequest': {'kind': 'model', 'model': 'OrganisationUser', 'version': 'PatchedOrganisationUserSerializerDetailRequest'}, 'PatchedPendingUserSerializerDetailRequest': {'kind': 'model', 'model': 'PendingUser', 'version': 'PatchedPendingUserSerializerDetailRequest'}, 'PendingUserSerializerDetail': {'kind': 'model', 'model': 'PendingUser', 'version': 'PendingUserSerializerDetail'}, 'PendingUserSerializerDetailRequest': {'kind': 'model', 'model': 'PendingUser', 'version': 'PendingUserSerializerDetailRequest'}, 'PendingUserSerializerList': {'kind': 'model', 'model': 'PendingUser', 'version': 'PendingUserSerializerList'}, 'PatchedReportScheduleSerialiserDetailRequest': {'kind': 'model', 'model': 'ReportSchedule', 'version': 'PatchedReportScheduleSerialiserDetailRequest'}, 'ReportScheduleSerialiserDetail': {'kind': 'model', 'model': 'ReportSchedule', 'version': 'ReportScheduleSerialiserDetail'}, 'ReportScheduleSerialiserDetailRequest': {'kind': 'model', 'model': 'ReportSchedule', 'version': 'ReportScheduleSerialiserDetailRequest'}, 'ReportScheduleSerialiserList': {'kind': 'model', 'model': 'ReportSchedule', 'version': 'ReportScheduleSerialiserList'}, 'PatchedSellerCustomerSerializerDetailRequest': {'kind': 'model', 'model': 'SellerCustomer', 'version': 'PatchedSellerCustomerSerializerDetailRequest'}, 'SellerCustomerSerializerDetail': {'kind': 'model', 'model': 'SellerCustomer', 'version': 'SellerCustomerSerializerDetail'}, 'SellerCustomerSerializerDetailRequest': {'kind': 'model', 'model': 'SellerCustomer', 'version': 'SellerCustomerSerializerDetailRequest'}, 'SellerCustomerSerializerList': {'kind': 'model', 'model': 'SellerCustomer', 'version': 'SellerCustomerSerializerList'}, 'PatchedSharedDeviceSerializerDetailRequest': {'kind': 'model', 'model': 'SharedDevice', 'version': 'PatchedSharedDeviceSerializerDetailRequest'}, 'SharedDeviceSerializerDetail': {'kind': 'model', 'model': 'SharedDevice', 'version': 'SharedDeviceSerializerDetail'}, 'SharedDeviceSerializerDetailRequest': {'kind': 'model', 'model': 'SharedDevice', 'version': 'SharedDeviceSerializerDetailRequest'}, 'SharedDeviceSerializerList': {'kind': 'model', 'model': 'SharedDevice', 'version': 'SharedDeviceSerializerList'}, 'PatchedSharedGroupSerializerDetailRequest': {'kind': 'model', 'model': 'SharedGroup', 'version': 'PatchedSharedGroupSerializerDetailRequest'}, 'SharedGroupSerializerDetail': {'kind': 'model', 'model': 'SharedGroup', 'version': 'SharedGroupSerializerDetail'}, 'SharedGroupSerializerDetailRequest': {'kind': 'model', 'model': 'SharedGroup', 'version': 'SharedGroupSerializerDetailRequest'}, 'SharedGroupSerializerList': {'kind': 'model', 'model': 'SharedGroup', 'version': 'SharedGroupSerializerList'}, 'PatchedSolutionInstallationSerializerDetailRequest': {'kind': 'model', 'model': 'SolutionInstallation', 'version': 'PatchedSolutionInstallationSerializerDetailRequest'}, 'SolutionInstallationSerializerDetail': {'kind': 'model', 'model': 'SolutionInstallation', 'version': 'SolutionInstallationSerializerDetail'}, 'SolutionInstallationSerializerDetailRequest': {'kind': 'model', 'model': 'SolutionInstallation', 'version': 'SolutionInstallationSerializerDetailRequest'}, 'SolutionInstallationSerializerList': {'kind': 'model', 'model': 'SolutionInstallation', 'version': 'SolutionInstallationSerializerList'}, 'PatchedSolutionSerializerDetailRequest': {'kind': 'model', 'model': 'Solution', 'version': 'PatchedSolutionSerializerDetailRequest'}, 'SolutionSerializerDetail': {'kind': 'model', 'model': 'Solution', 'version': 'SolutionSerializerDetail'}, 'SolutionSerializerDetailRequest': {'kind': 'model', 'model': 'Solution', 'version': 'SolutionSerializerDetailRequest'}, 'SolutionSerializerList': {'kind': 'model', 'model': 'Solution', 'version': 'SolutionSerializerList'}, 'PatchedThemeSerializerWithIdDetailRequest': {'kind': 'model', 'model': 'Theme', 'version': 'PatchedThemeSerializerWithIdDetailRequest'}, 'ThemeSerializerDetail': {'kind': 'model', 'model': 'Theme', 'version': 'ThemeSerializerDetail'}, 'ThemeSerializerDetailRequest': {'kind': 'model', 'model': 'Theme', 'version': 'ThemeSerializerDetailRequest'}, 'ThemeSerializerList': {'kind': 'model', 'model': 'Theme', 'version': 'ThemeSerializerList'}, 'ThemeSerializerWithIdDetail': {'kind': 'model', 'model': 'Theme', 'version': 'ThemeSerializerWithIdDetail'}, 'ThemeSerializerWithIdDetailRequest': {'kind': 'model', 'model': 'Theme', 'version': 'ThemeSerializerWithIdDetailRequest'}, 'ThemeSerializerWithIdList': {'kind': 'model', 'model': 'Theme', 'version': 'ThemeSerializerWithIdList'}, 'PatchedTunnelSerializerDetailRequest': {'kind': 'model', 'model': 'Tunnel', 'version': 'PatchedTunnelSerializerDetailRequest'}, 'TunnelSerializerDetail': {'kind': 'model', 'model': 'Tunnel', 'version': 'TunnelSerializerDetail'}, 'TunnelSerializerDetailRequest': {'kind': 'model', 'model': 'Tunnel', 'version': 'TunnelSerializerDetailRequest'}, 'TunnelSerializerList': {'kind': 'model', 'model': 'Tunnel', 'version': 'TunnelSerializerList'}, 'PatchedUserSerialiserDetailRequest': {'kind': 'model', 'model': 'User', 'version': 'PatchedUserSerialiserDetailRequest'}, 'UserBasicSerializerDetail': {'kind': 'model', 'model': 'User', 'version': 'UserBasicSerializerDetail'}, 'UserBasicSerializerList': {'kind': 'model', 'model': 'User', 'version': 'UserBasicSerializerList'}, 'UserSerialiserDetail': {'kind': 'model', 'model': 'User', 'version': 'UserSerialiserDetail'}, 'UserSerialiserDetailRequest': {'kind': 'model', 'model': 'User', 'version': 'UserSerialiserDetailRequest'}, 'UserSerialiserList': {'kind': 'model', 'model': 'User', 'version': 'UserSerialiserList'}, 'PermissionUserSerializerDetail': {'kind': 'model', 'model': 'PermissionUser', 'version': 'PermissionUserSerializerDetail'}, 'PermissionUserSerializerDetailRequest': {'kind': 'model', 'model': 'PermissionUser', 'version': 'PermissionUserSerializerDetailRequest'}, 'PermissionUserSerializerList': {'kind': 'model', 'model': 'PermissionUser', 'version': 'PermissionUserSerializerList'}, 'ReportCreateSerialiserDetailRequest': {'kind': 'model', 'model': 'ReportCreate', 'version': 'ReportCreateSerialiserDetailRequest'}, 'ReportSerialiserDetail': {'kind': 'model', 'model': 'Report', 'version': 'ReportSerialiserDetail'}, 'ReportSerialiserList': {'kind': 'model', 'model': 'Report', 'version': 'ReportSerialiserList'}, 'SellerCustomerGroupSerializerDetail': {'kind': 'model', 'model': 'SellerCustomerGroup', 'version': 'SellerCustomerGroupSerializerDetail'}, 'SellerCustomerGroupSerializerList': {'kind': 'model', 'model': 'SellerCustomerGroup', 'version': 'SellerCustomerGroupSerializerList'}, 'SellerCustomerOrgSerializerDetail': {'kind': 'model', 'model': 'SellerCustomerOrg', 'version': 'SellerCustomerOrgSerializerDetail'}, 'SellerCustomerOrgSerializerList': {'kind': 'model', 'model': 'SellerCustomerOrg', 'version': 'SellerCustomerOrgSerializerList'}, 'SlimContainerRegistryDetail': {'kind': 'model', 'model': 'ContainerRegistry', 'version': 'SlimContainerRegistryDetail'}, 'SlimContainerRegistryList': {'kind': 'model', 'model': 'ContainerRegistry', 'version': 'SlimContainerRegistryList'}, 'UsageMeteringRunSerializerDetail': {'kind': 'model', 'model': 'UsageMeteringRun', 'version': 'UsageMeteringRunSerializerDetail'}, 'UsageMeteringRunSerializerList': {'kind': 'model', 'model': 'UsageMeteringRun', 'version': 'UsageMeteringRunSerializerList'}, 'UsageRecordAppInstallSerializerDetail': {'kind': 'model', 'model': 'UsageRecordAppInstall', 'version': 'UsageRecordAppInstallSerializerDetail'}, 'UsageRecordAppInstallSerializerList': {'kind': 'model', 'model': 'UsageRecordAppInstall', 'version': 'UsageRecordAppInstallSerializerList'}, 'UsageRecordBillingProductSerializerDetail': {'kind': 'model', 'model': 'UsageRecordBillingProduct', 'version': 'UsageRecordBillingProductSerializerDetail'}, 'UsageRecordBillingProductSerializerList': {'kind': 'model', 'model': 'UsageRecordBillingProduct', 'version': 'UsageRecordBillingProductSerializerList'}, 'UsageRecordDeviceSerializerDetail': {'kind': 'model', 'model': 'UsageRecordDevice', 'version': 'UsageRecordDeviceSerializerDetail'}, 'UsageRecordDeviceSerializerList': {'kind': 'model', 'model': 'UsageRecordDevice', 'version': 'UsageRecordDeviceSerializerList'}, 'UsageRecordOrgSerializerDetail': {'kind': 'model', 'model': 'UsageRecordOrg', 'version': 'UsageRecordOrgSerializerDetail'}, 'UsageRecordOrgSerializerList': {'kind': 'model', 'model': 'UsageRecordOrg', 'version': 'UsageRecordOrgSerializerList'}, 'UsageRecordSerializerDetail': {'kind': 'model', 'model': 'UsageRecord', 'version': 'UsageRecordSerializerDetail'}, 'UsageRecordSerializerList': {'kind': 'model', 'model': 'UsageRecord', 'version': 'UsageRecordSerializerList'}, 'PaginatedAIChatMessageSerializerListList': {'kind': 'page', 'model': 'AIChatMessage', 'version': 'AIChatMessageSerializerList'}, 'PaginatedAIChatSessionSerializerListList': {'kind': 'page', 'model': 'AIChatSession', 'version': 'AIChatSessionSerializerList'}, 'PaginatedAgentBillingItemSerializerListList': {'kind': 'page', 'model': 'AgentBillingItem', 'version': 'AgentBillingItemSerializerList'}, 'PaginatedAppBillingConfigSerializerListList': {'kind': 'page', 'model': 'AppBillingConfig', 'version': 'AppBillingConfigSerializerList'}, 'PaginatedApplicationConfigProfileSerializerListList': {'kind': 'page', 'model': 'ApplicationConfigProfile', 'version': 'ApplicationConfigProfileSerializerList'}, 'PaginatedApplicationDeploymentSerializerListList': {'kind': 'page', 'model': 'ApplicationDeployment', 'version': 'ApplicationDeploymentSerializerList'}, 'PaginatedApplicationInstallationSerializerListList': {'kind': 'page', 'model': 'ApplicationInstallation', 'version': 'ApplicationInstallationSerializerList'}, 'PaginatedApplicationSerializerListList': {'kind': 'page', 'model': 'Application', 'version': 'ApplicationSerializerList'}, 'PaginatedApplicationTemplateSerializerListList': {'kind': 'page', 'model': 'ApplicationTemplate', 'version': 'ApplicationTemplateSerializerList'}, 'PaginatedBillingAccountSerializerListList': {'kind': 'page', 'model': 'BillingAccount', 'version': 'BillingAccountSerializerList'}, 'PaginatedBillingProductSerializerListList': {'kind': 'page', 'model': 'BillingProduct', 'version': 'BillingProductSerializerList'}, 'PaginatedBillingSubscriptionSerializerListList': {'kind': 'page', 'model': 'BillingSubscription', 'version': 'BillingSubscriptionSerializerList'}, 'PaginatedContainerRegistryProfileSeraliserListList': {'kind': 'page', 'model': 'ContainerRegistryProfile', 'version': 'ContainerRegistryProfileSeraliserList'}, 'PaginatedDeviceBillingConfigSerializerListList': {'kind': 'page', 'model': 'DeviceBillingConfig', 'version': 'DeviceBillingConfigSerializerList'}, 'PaginatedDeviceSerializerListList': {'kind': 'page', 'model': 'Device', 'version': 'DeviceSerializerList'}, 'PaginatedDeviceTypeBillingConfigSerializerListList': {'kind': 'page', 'model': 'DeviceTypeBillingConfig', 'version': 'DeviceTypeBillingConfigSerializerList'}, 'PaginatedDeviceTypeSerializerListList': {'kind': 'page', 'model': 'DeviceType', 'version': 'DeviceTypeSerializerList'}, 'PaginatedGroupPermissionSerializerListList': {'kind': 'page', 'model': 'GroupPermission', 'version': 'GroupPermissionSerializerList'}, 'PaginatedGroupRoleSerializerListList': {'kind': 'page', 'model': 'GroupRole', 'version': 'GroupRoleSerializerList'}, 'PaginatedGroupSerializerListList': {'kind': 'page', 'model': 'Group', 'version': 'GroupSerializerList'}, 'PaginatedIntegrationSerializerListList': {'kind': 'page', 'model': 'Integration', 'version': 'IntegrationSerializerList'}, 'PaginatedOrganisationDomainSerializerListList': {'kind': 'page', 'model': 'OrganisationDomain', 'version': 'OrganisationDomainSerializerList'}, 'PaginatedOrganisationRoleSerializerListList': {'kind': 'page', 'model': 'OrganisationRole', 'version': 'OrganisationRoleSerializerList'}, 'PaginatedOrganisationSerializerListList': {'kind': 'page', 'model': 'Organisation', 'version': 'OrganisationSerializerList'}, 'PaginatedOrganisationSharedReceiveProfileSerializerListList': {'kind': 'page', 'model': 'OrganisationSharedReceiveProfile', 'version': 'OrganisationSharedReceiveProfileSerializerList'}, 'PaginatedOrganisationSharingProfileSerializerListList': {'kind': 'page', 'model': 'OrganisationSharingProfile', 'version': 'OrganisationSharingProfileSerializerList'}, 'PaginatedOrganisationUserSerializerListList': {'kind': 'page', 'model': 'OrganisationUser', 'version': 'OrganisationUserSerializerList'}, 'PaginatedPendingUserSerializerListList': {'kind': 'page', 'model': 'PendingUser', 'version': 'PendingUserSerializerList'}, 'PaginatedPublicApplicationSerializerListList': {'kind': 'page', 'model': 'Application', 'version': 'PublicApplicationSerializerList'}, 'PaginatedReportScheduleSerialiserListList': {'kind': 'page', 'model': 'ReportSchedule', 'version': 'ReportScheduleSerialiserList'}, 'PaginatedSellerCustomerSerializerListList': {'kind': 'page', 'model': 'SellerCustomer', 'version': 'SellerCustomerSerializerList'}, 'PaginatedSharedDeviceSerializerListList': {'kind': 'page', 'model': 'SharedDevice', 'version': 'SharedDeviceSerializerList'}, 'PaginatedSharedGroupSerializerListList': {'kind': 'page', 'model': 'SharedGroup', 'version': 'SharedGroupSerializerList'}, 'PaginatedSolutionInstallationSerializerListList': {'kind': 'page', 'model': 'SolutionInstallation', 'version': 'SolutionInstallationSerializerList'}, 'PaginatedSolutionSerializerListList': {'kind': 'page', 'model': 'Solution', 'version': 'SolutionSerializerList'}, 'PaginatedThemeSerializerWithIdListList': {'kind': 'page', 'model': 'Theme', 'version': 'ThemeSerializerWithIdList'}, 'PaginatedTunnelSerializerListList': {'kind': 'page', 'model': 'Tunnel', 'version': 'TunnelSerializerList'}, 'PaginatedUsageMeteringRunSerializerListList': {'kind': 'page', 'model': 'UsageMeteringRun', 'version': 'UsageMeteringRunSerializerList'}, 'PaginatedUsageRecordSerializerListList': {'kind': 'page', 'model': 'UsageRecord', 'version': 'UsageRecordSerializerList'}, 'PaginatedUserSerialiserListList': {'kind': 'page', 'model': 'User', 'version': 'UserSerialiserList'}}

__all__ = [
    "CONTROL_SCHEMA_REGISTRY",
    "Location",
    "AIChatMessage",
    "AIChatSession",
    "AgentBillingItem",
    "AgentItemDevice",
    "AgentItemOrg",
    "AgentItemProduct",
    "AppBillingConfig",
    "AppBillingConfigApp",
    "AppBillingConfigOwnerOrg",
    "AppBillingConfigProduct",
    "Application",
    "ApplicationConfigProfile",
    "ApplicationDeployment",
    "ApplicationInstallation",
    "ApplicationTemplate",
    "Attachment",
    "BillingAccount",
    "BillingProduct",
    "BillingProductOrg",
    "BillingSubscription",
    "BillingSubscriptionItem",
    "ContainerRegistry",
    "ContainerRegistryProfile",
    "CustomerSite",
    "DTBillingConfigDeviceType",
    "DTBillingConfigOwnerOrg",
    "DTBillingConfigProduct",
    "Device",
    "DeviceBillingConfig",
    "DeviceType",
    "DeviceTypeBillingConfig",
    "Group",
    "GroupPermission",
    "GroupRole",
    "GroupRoleAssignment",
    "IngestionEndpoint",
    "Integration",
    "MeteringRunOrg",
    "Organisation",
    "OrganisationDomain",
    "OrganisationRole",
    "OrganisationSharedReceiveProfile",
    "OrganisationSharingProfile",
    "OrganisationUser",
    "PendingUser",
    "PermissionUser",
    "Report",
    "ReportCreate",
    "ReportSchedule",
    "SellerCustomer",
    "SellerCustomerGroup",
    "SellerCustomerOrg",
    "SharedDevice",
    "SharedGroup",
    "Solution",
    "SolutionInstallation",
    "Theme",
    "Tunnel",
    "UsageMeteringRun",
    "UsageRecord",
    "UsageRecordAppInstall",
    "UsageRecordBillingProduct",
    "UsageRecordDevice",
    "UsageRecordOrg",
    "User",
]
