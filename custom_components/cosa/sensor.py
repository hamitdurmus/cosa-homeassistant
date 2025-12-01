"""COSA Smart Thermostat Sensor Platform.

Bu modül COSA termostat için sensör entity'leri oluşturur.
Climate entity ile aynı DataUpdateCoordinator'ı kullanır.

Sensörler:
- Sıcaklık sensörü (°C)
- Nem sensörü (%)
- Kombi durumu sensörü (on/off)
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .climate import CosaCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sensor platformunu kur.
    
    Climate entity tarafından oluşturulan coordinator'ı kullanır.
    """
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: CosaCoordinator = entry_data["coordinator"]
    device_name = entry_data.get("device_name", "COSA Termostat")
    
    # Sensörleri oluştur
    entities = [
        CosaTemperatureSensor(coordinator, config_entry, device_name),
        CosaHumiditySensor(coordinator, config_entry, device_name),
        CosaCombiStateSensor(coordinator, config_entry, device_name),
    ]
    
    async_add_entities(entities)
    _LOGGER.info("COSA sensör entity'leri oluşturuldu")


class CosaBaseSensor(CoordinatorEntity[CosaCoordinator], SensorEntity):
    """COSA sensör base class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CosaCoordinator,
        config_entry: ConfigEntry,
        device_name: str,
    ) -> None:
        """Sensörü başlat."""
        super().__init__(coordinator)
        
        self._config_entry = config_entry
        self._device_name = device_name
        
        # Cihaz bilgisi - climate entity ile aynı cihaza bağlı
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=device_name,
            manufacturer="COSA",
            model="Smart Thermostat",
        )


class CosaTemperatureSensor(CosaBaseSensor):
    """Sıcaklık sensörü.
    
    API'den gelen "temperature" değerini gösterir.
    Oda sıcaklığı (°C).
    """

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: CosaCoordinator,
        config_entry: ConfigEntry,
        device_name: str,
    ) -> None:
        """Sıcaklık sensörünü başlat."""
        super().__init__(coordinator, config_entry, device_name)
        
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_temperature"
        self._attr_name = "Sıcaklık"

    @property
    def native_value(self) -> float | None:
        """Mevcut sıcaklık değeri."""
        if self.coordinator.data:
            return self.coordinator.data.get("temperature")
        return None


class CosaHumiditySensor(CosaBaseSensor):
    """Nem sensörü.
    
    API'den gelen "humidity" değerini gösterir.
    Oda nem oranı (%).
    """

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self,
        coordinator: CosaCoordinator,
        config_entry: ConfigEntry,
        device_name: str,
    ) -> None:
        """Nem sensörünü başlat."""
        super().__init__(coordinator, config_entry, device_name)
        
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_humidity"
        self._attr_name = "Nem"

    @property
    def native_value(self) -> int | None:
        """Mevcut nem değeri."""
        if self.coordinator.data:
            humidity = self.coordinator.data.get("humidity")
            if humidity is not None:
                return int(humidity)
        return None


class CosaCombiStateSensor(CosaBaseSensor):
    """Kombi durumu sensörü.
    
    API'den gelen "combiState" değerini gösterir.
    Kombi çalışıyor mu? (on/off)
    """

    def __init__(
        self,
        coordinator: CosaCoordinator,
        config_entry: ConfigEntry,
        device_name: str,
    ) -> None:
        """Kombi durumu sensörünü başlat."""
        super().__init__(coordinator, config_entry, device_name)
        
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_combi_state"
        self._attr_name = "Kombi Durumu"
        self._attr_icon = "mdi:water-boiler"

    @property
    def native_value(self) -> str | None:
        """Mevcut kombi durumu."""
        if self.coordinator.data:
            state = self.coordinator.data.get("combi_state")
            if state == "on":
                return "Çalışıyor"
            elif state == "off":
                return "Kapalı"
            return state
        return None

    @property
    def icon(self) -> str:
        """Duruma göre ikon."""
        if self.coordinator.data:
            state = self.coordinator.data.get("combi_state")
            if state == "on":
                return "mdi:water-boiler"
            return "mdi:water-boiler-off"
        return "mdi:water-boiler-off"
