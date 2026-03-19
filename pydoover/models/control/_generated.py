from __future__ import annotations

from ._base import ControlField, ControlModel, ObjectFieldType


class Location(ObjectFieldType):
    _structure = {
        "latitude": ControlField(type="float", nullable=False),
        "longitude": ControlField(type="float", nullable=False),
    }

class AIChatMessage(ControlModel):
    _model_name = "AIChatMessage"
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
