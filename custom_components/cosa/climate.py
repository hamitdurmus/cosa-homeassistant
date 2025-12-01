"""COSA Climate Platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import CosaAPI, CosaAPIError, CosaAuthError
from .const import (
    DOMAIN, SCAN_INTERVAL, MIN_TEMP, MAX_TEMP, TEMP_STEP,
    MODE_MANUAL, MODE_AUTO, MODE_SCHEDULE,
    OPTION_HOME, OPTION_SLEEP, OPTION_AWAY, OPTION_CUSTOM, OPTION_FROZEN,
    PRESET_HOME, PRESET_SLEEP, PRESET_AWAY, PRESET_CUSTOM, PRESET_AUTO, PRESET_SCHEDULE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Climate platformunu kur."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    
    coordinator = CosaCoordinator(hass, config_entry, entry_data)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][config_entry.entry_id]["coordinator"] = coordinator
    
    async_add_entities([CosaClimate(coordinator, config_entry)])


class CosaCoordinator(DataUpdateCoordinator):
    """COSA Koordinatör."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, entry_data: dict) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        
        self.config_entry = config_entry
        self._email = entry_data["email"]
        self._password = entry_data["password"]
        self._token = entry_data["token"]
        self._endpoint_id = entry_data["endpoint_id"]
        self._device_name = entry_data.get("device_name", "COSA Termostat")
        self._place_id = entry_data.get("place_id")
        
        self._api = CosaAPI(async_get_clientsession(hass))

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            detail = await self._api.get_endpoint_detail(self._token, self._endpoint_id)
            
            # Hava durumu
            forecast = {}
            if self._place_id:
                forecast = await self._api.get_forecast(self._token, self._place_id)
            
            return {
                "endpoint": detail,
                "forecast": forecast,
            }
            
        except CosaAuthError:
            self._token = await self._api.login(self._email, self._password)
            detail = await self._api.get_endpoint_detail(self._token, self._endpoint_id)
            return {"endpoint": detail, "forecast": {}}
            
        except CosaAPIError as err:
            raise UpdateFailed(f"API hatası: {err}") from err

    async def async_set_mode(self, mode: str, option: str | None = None) -> None:
        try:
            await self._api.set_mode(self._token, self._endpoint_id, mode, option)
            await self.async_request_refresh()
        except CosaAuthError:
            self._token = await self._api.login(self._email, self._password)
            await self._api.set_mode(self._token, self._endpoint_id, mode, option)
            await self.async_request_refresh()

    async def async_set_temperatures(self, home: float, away: float, sleep: float, custom: float) -> None:
        try:
            await self._api.set_target_temperatures(self._token, self._endpoint_id, home, away, sleep, custom)
            await self.async_request_refresh()
        except CosaAuthError:
            self._token = await self._api.login(self._email, self._password)
            await self._api.set_target_temperatures(self._token, self._endpoint_id, home, away, sleep, custom)
            await self.async_request_refresh()


class CosaClimate(CoordinatorEntity[CosaCoordinator], ClimateEntity):
    """COSA Climate Entity."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = TEMP_STEP
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = [PRESET_HOME, PRESET_SLEEP, PRESET_AWAY, PRESET_CUSTOM, PRESET_AUTO, PRESET_SCHEDULE]

    def __init__(self, coordinator: CosaCoordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_climate"
        self._attr_name = "Termostat"
        self._last_preset = PRESET_HOME
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=coordinator._device_name,
            manufacturer="COSA",
            model="Smart Thermostat",
        )

    @property
    def _endpoint(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("endpoint", {})
        return {}

    @property
    def current_temperature(self) -> float | None:
        return self._endpoint.get("temperature")

    @property
    def target_temperature(self) -> float | None:
        return self._endpoint.get("targetTemperature")

    @property
    def current_humidity(self) -> int | None:
        humidity = self._endpoint.get("humidity")
        return int(humidity) if humidity else None

    @property
    def hvac_mode(self) -> HVACMode:
        mode = self._endpoint.get("mode")
        option = self._endpoint.get("option")
        if mode == MODE_MANUAL and option == OPTION_FROZEN:
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        if self._endpoint.get("combiState") == "on":
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def preset_mode(self) -> str | None:
        mode = self._endpoint.get("mode")
        option = self._endpoint.get("option")
        
        if mode == MODE_AUTO:
            return PRESET_AUTO
        if mode == MODE_SCHEDULE:
            return PRESET_SCHEDULE
        if mode == MODE_MANUAL:
            return {
                OPTION_HOME: PRESET_HOME,
                OPTION_SLEEP: PRESET_SLEEP,
                OPTION_AWAY: PRESET_AWAY,
                OPTION_CUSTOM: PRESET_CUSTOM,
            }.get(option)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        ep = self._endpoint
        device = ep.get("device", {})
        
        return {
            "mode": ep.get("mode"),
            "option": ep.get("option"),
            "combi_state": ep.get("combiState"),
            "operation_mode": ep.get("operationMode"),
            "is_connected": ep.get("device", {}).get("isConnected", device.get("isConnected")),
            "home_temperature": ep.get("homeTemperature"),
            "away_temperature": ep.get("awayTemperature"),
            "sleep_temperature": ep.get("sleepTemperature"),
            "custom_temperature": ep.get("customTemperature"),
            "firmware_version": device.get("version"),
            "hardware_version": device.get("hardwareVersion"),
            "mac_address": device.get("macAddress"),
            "serial_number": device.get("serialNo"),
            "battery_voltage": ep.get("batteryVoltage"),
            "power_source": ep.get("powerSource"),
            "power_state": ep.get("powerState"),
            "rssi": ep.get("rssi"),
            "child_lock": ep.get("childLock"),
            "open_window_state": ep.get("openWindowState"),
            "calibration": ep.get("calibration"),
        }

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_set_mode(MODE_MANUAL, OPTION_FROZEN)
        else:
            preset = self._last_preset or PRESET_HOME
            await self.async_set_preset_mode(preset)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode not in (None, OPTION_FROZEN):
            self._last_preset = preset_mode
        
        if preset_mode == PRESET_AUTO:
            await self.coordinator.async_set_mode(MODE_AUTO)
        elif preset_mode == PRESET_SCHEDULE:
            await self.coordinator.async_set_mode(MODE_SCHEDULE)
        else:
            option = {
                PRESET_HOME: OPTION_HOME,
                PRESET_SLEEP: OPTION_SLEEP,
                PRESET_AWAY: OPTION_AWAY,
                PRESET_CUSTOM: OPTION_CUSTOM,
            }.get(preset_mode, OPTION_HOME)
            await self.coordinator.async_set_mode(MODE_MANUAL, option)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        ep = self._endpoint
        home = ep.get("homeTemperature", 20.0)
        away = ep.get("awayTemperature", 15.0)
        sleep = ep.get("sleepTemperature", 18.0)
        custom = ep.get("customTemperature", 20.0)
        
        preset = self.preset_mode or PRESET_HOME
        if preset == PRESET_HOME:
            home = temperature
        elif preset == PRESET_AWAY:
            away = temperature
        elif preset == PRESET_SLEEP:
            sleep = temperature
        elif preset == PRESET_CUSTOM:
            custom = temperature
        else:
            home = temperature
        
        await self.coordinator.async_set_temperatures(home, away, sleep, custom)

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.preset_mode and self.preset_mode != OPTION_FROZEN:
            self._last_preset = self.preset_mode
        self.async_write_ha_state()
