"""COSA Switch Platform."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Switch platformunu kur."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    entities = [
        CosaChildLockSwitch(coordinator, config_entry),
        CosaOpenWindowSwitch(coordinator, config_entry),
    ]
    
    async_add_entities(entities)


class CosaChildLockSwitch(CoordinatorEntity, SwitchEntity):
    """Çocuk Kilidi Switch."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_icon = "mdi:lock-outline"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_child_lock"
        self._attr_name = "Çocuk Kilidi"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
        )
        self._optimistic_state: bool | None = None

    @property
    def _combi_settings(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("endpoint", {}).get("combiSettings", {})
        return {}

    @property
    def is_on(self) -> bool:
        """Switch açık mı."""
        if self._optimistic_state is not None:
            return self._optimistic_state
        return self._combi_settings.get("childLock", False)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Coordinator güncellemesini işle."""
        real_state = self._combi_settings.get("childLock", False)
        if self._optimistic_state is not None and real_state == self._optimistic_state:
            self._optimistic_state = None
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Çocuk kilidini aç."""
        self._optimistic_state = True
        self.async_write_ha_state()
        result = await self.coordinator.async_set_child_lock(True)
        if not result:
            self._optimistic_state = None
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Çocuk kilidini kapat."""
        self._optimistic_state = False
        self.async_write_ha_state()
        result = await self.coordinator.async_set_child_lock(False)
        if not result:
            self._optimistic_state = None
            self.async_write_ha_state()


class CosaOpenWindowSwitch(CoordinatorEntity, SwitchEntity):
    """Açık Pencere Algılama Switch."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_icon = "mdi:window-open-variant"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_open_window_enable"
        self._attr_name = "Açık Pencere Algılama"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
        )
        self._optimistic_state: bool | None = None

    @property
    def _endpoint(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("endpoint", {})
        return {}

    @property
    def is_on(self) -> bool:
        """Switch açık mı."""
        if self._optimistic_state is not None:
            return self._optimistic_state
        return self._endpoint.get("openWindowEnable", False)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Coordinator güncellemesini işle."""
        real_state = self._endpoint.get("openWindowEnable", False)
        if self._optimistic_state is not None and real_state == self._optimistic_state:
            self._optimistic_state = None
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Açık pencere algılamayı aç."""
        self._optimistic_state = True
        self.async_write_ha_state()
        result = await self.coordinator.async_set_open_window(True)
        if not result:
            self._optimistic_state = None
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Açık pencere algılamayı kapat."""
        self._optimistic_state = False
        self.async_write_ha_state()
        result = await self.coordinator.async_set_open_window(False)
        if not result:
            self._optimistic_state = None
            self.async_write_ha_state()
