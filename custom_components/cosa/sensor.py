"""COSA Sensor Platform."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, BATTERY_LEVELS, WEATHER_ICONS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sensor platformunu kur."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry_data.get("coordinator")
    
    if not coordinator:
        return
    
    entities = [
        CosaTemperatureSensor(coordinator, config_entry),
        CosaHumiditySensor(coordinator, config_entry),
        CosaTargetTemperatureSensor(coordinator, config_entry),
        CosaBatteryVoltageSensor(coordinator, config_entry),
        CosaBatteryPercentSensor(coordinator, config_entry),
        CosaRssiSensor(coordinator, config_entry),
        CosaCombiStateSensor(coordinator, config_entry),
        CosaModeSensor(coordinator, config_entry),
        CosaOptionSensor(coordinator, config_entry),
        CosaOutdoorTemperatureSensor(coordinator, config_entry),
        CosaOutdoorHumiditySensor(coordinator, config_entry),
        CosaWeatherSensor(coordinator, config_entry),
        CosaHomeTemperatureSensor(coordinator, config_entry),
        CosaAwayTemperatureSensor(coordinator, config_entry),
        CosaSleepTemperatureSensor(coordinator, config_entry),
        CosaCustomTemperatureSensor(coordinator, config_entry),
        CosaFirmwareVersionSensor(coordinator, config_entry),
        CosaCalibrationSensor(coordinator, config_entry),
    ]
    
    async_add_entities(entities)


class CosaBaseSensor(CoordinatorEntity, SensorEntity):
    """COSA Base Sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, config_entry: ConfigEntry, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
        )

    @property
    def _endpoint(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("endpoint", {})
        return {}

    @property
    def _forecast(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("forecast", {})
        return {}


class CosaTemperatureSensor(CosaBaseSensor):
    """Oda Sıcaklığı Sensörü."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "temperature", "Oda Sıcaklığı")

    @property
    def native_value(self) -> float | None:
        return self._endpoint.get("temperature")


class CosaHumiditySensor(CosaBaseSensor):
    """Nem Sensörü."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "humidity", "Nem")

    @property
    def native_value(self) -> float | None:
        return self._endpoint.get("humidity")


class CosaTargetTemperatureSensor(CosaBaseSensor):
    """Hedef Sıcaklık Sensörü."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "target_temperature", "Hedef Sıcaklık")

    @property
    def native_value(self) -> float | None:
        return self._endpoint.get("targetTemperature")


class CosaBatteryVoltageSensor(CosaBaseSensor):
    """Batarya Voltajı Sensörü."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "battery_voltage", "Batarya Voltajı")

    @property
    def native_value(self) -> float | None:
        return self._endpoint.get("batteryVoltage")


class CosaBatteryPercentSensor(CosaBaseSensor):
    """Batarya Yüzdesi Sensörü."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "battery_percent", "Batarya")

    @property
    def native_value(self) -> int | None:
        power_state = self._endpoint.get("powerState")
        return BATTERY_LEVELS.get(power_state)


class CosaRssiSensor(CosaBaseSensor):
    """WiFi Sinyal Gücü Sensörü."""

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "rssi", "WiFi Sinyal Gücü")

    @property
    def native_value(self) -> int | None:
        return self._endpoint.get("rssi")


class CosaCombiStateSensor(CosaBaseSensor):
    """Kombi Durumu Sensörü."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "combi_state", "Kombi Durumu")
        self._attr_icon = "mdi:fire"

    @property
    def native_value(self) -> str | None:
        state = self._endpoint.get("combiState")
        if state == "on":
            return "Çalışıyor"
        return "Beklemede"


class CosaModeSensor(CosaBaseSensor):
    """Mod Sensörü."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "mode", "Mod")
        self._attr_icon = "mdi:thermostat"

    @property
    def native_value(self) -> str | None:
        mode = self._endpoint.get("mode")
        modes = {"manual": "Manuel", "auto": "Otomatik", "schedule": "Program"}
        return modes.get(mode, mode)


class CosaOptionSensor(CosaBaseSensor):
    """Option Sensörü."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "option", "Seçenek")
        self._attr_icon = "mdi:home-thermometer"

    @property
    def native_value(self) -> str | None:
        option = self._endpoint.get("option")
        options = {
            "home": "Evde",
            "away": "Dışarıda",
            "sleep": "Uyku",
            "custom": "Özel",
            "frozen": "Kapalı",
        }
        return options.get(option, option)


class CosaOutdoorTemperatureSensor(CosaBaseSensor):
    """Dış Mekan Sıcaklık Sensörü."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "outdoor_temperature", "Dış Mekan Sıcaklığı")

    @property
    def native_value(self) -> float | None:
        hourly = self._forecast.get("hourly", [])
        if hourly:
            return hourly[0].get("temperature")
        return None


class CosaOutdoorHumiditySensor(CosaBaseSensor):
    """Dış Mekan Nem Sensörü."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "outdoor_humidity", "Dış Mekan Nemi")

    @property
    def native_value(self) -> float | None:
        hourly = self._forecast.get("hourly", [])
        if hourly:
            humidity = hourly[0].get("humidity")
            if humidity:
                return int(humidity * 100)
        return None


class CosaWeatherSensor(CosaBaseSensor):
    """Hava Durumu Sensörü."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "weather", "Hava Durumu")
        self._attr_icon = "mdi:weather-partly-cloudy"

    @property
    def native_value(self) -> str | None:
        hourly = self._forecast.get("hourly", [])
        if hourly:
            icon = hourly[0].get("icon", "")
            icons = {
                "clear-day": "Güneşli",
                "clear-night": "Açık",
                "partly-cloudy-day": "Parçalı Bulutlu",
                "partly-cloudy-night": "Parçalı Bulutlu",
                "cloudy": "Bulutlu",
                "rain": "Yağmurlu",
                "snow": "Karlı",
                "wind": "Rüzgarlı",
                "fog": "Sisli",
            }
            return icons.get(icon, icon)
        return None


class CosaHomeTemperatureSensor(CosaBaseSensor):
    """Evde Modu Sıcaklık Sensörü."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "home_temp", "Evde Sıcaklığı")

    @property
    def native_value(self) -> float | None:
        return self._endpoint.get("homeTemperature")


class CosaAwayTemperatureSensor(CosaBaseSensor):
    """Dışarıda Modu Sıcaklık Sensörü."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "away_temp", "Dışarıda Sıcaklığı")

    @property
    def native_value(self) -> float | None:
        return self._endpoint.get("awayTemperature")


class CosaSleepTemperatureSensor(CosaBaseSensor):
    """Uyku Modu Sıcaklık Sensörü."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "sleep_temp", "Uyku Sıcaklığı")

    @property
    def native_value(self) -> float | None:
        return self._endpoint.get("sleepTemperature")


class CosaCustomTemperatureSensor(CosaBaseSensor):
    """Özel Mod Sıcaklık Sensörü."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "custom_temp", "Özel Sıcaklık")

    @property
    def native_value(self) -> float | None:
        return self._endpoint.get("customTemperature")


class CosaFirmwareVersionSensor(CosaBaseSensor):
    """Firmware Versiyon Sensörü."""

    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "firmware", "Firmware Versiyonu")
        self._attr_icon = "mdi:chip"

    @property
    def native_value(self) -> str | None:
        device = self._endpoint.get("device", {})
        return device.get("version")


class CosaCalibrationSensor(CosaBaseSensor):
    """Kalibrasyon Sensörü."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, "calibration", "Kalibrasyon")

    @property
    def native_value(self) -> float | None:
        return self._endpoint.get("calibration")
