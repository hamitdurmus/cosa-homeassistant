"""Config flow for COSA integration."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import CosaAPIClient, CosaAPIError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username", description="Email veya kullanıcı adı"): str,
        vol.Required("password"): str,
        vol.Optional("endpoint_id", description="Endpoint ID (opsiyonel - otomatik tespit edilebilir)"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect."""
    client = CosaAPIClient(
        username=data["username"],
        password=data["password"],
        endpoint_id=data.get("endpoint_id"),
    )

    try:
        # Try to login
        if not await client.login():
            raise InvalidAuth

        # Get endpoint status to verify connection
        if client._endpoint_id:
            status = await client.get_endpoint_status()
            endpoint_data = status.get("endpoint", {})
        else:
            # If no endpoint_id provided, try to get endpoints list
            try:
                endpoints = await client.list_endpoints()
                if endpoints and len(endpoints) > 0:
                    # Use first endpoint if available
                    first_endpoint = endpoints[0]
                    client._endpoint_id = first_endpoint.get("id") or first_endpoint.get("_id") or first_endpoint.get("endpoint")
                    if client._endpoint_id:
                        status = await client.get_endpoint_status(client._endpoint_id)
                        endpoint_data = status.get("endpoint", {})
                    else:
                        endpoint_data = {}
                else:
                    endpoint_data = {}
            except Exception:
                # If list_endpoints fails, just verify login works
                endpoint_data = {}

        await client.close()

        # Return info that will be stored in the config entry
        return {
            "title": f"COSA Termostat ({data['username']})",
            "endpoint_id": client._endpoint_id or data.get("endpoint_id", ""),
        }
    except CosaAPIError as err:
        _LOGGER.error("API error during validation: %s", err)
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.error("Unexpected error during validation: %s", err)
        raise CannotConnect from err
    finally:
        await client.close()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for COSA."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            # Check if already configured
            await self.async_set_unique_id(user_input["username"])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

