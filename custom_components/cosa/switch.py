"""COSA Switch Platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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

    @property
    def _endpoint(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("endpoint", {})
        return {}

    @property
    def is_on(self) -> bool:
        return self._endpoint.get("childLock", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Çocuk kilidini aç."""
        await self.coordinator.async_set_child_lock(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Çocuk kilidini kapat."""
        await self.coordinator.async_set_child_lock(False)
