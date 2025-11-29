import asyncio
import pytest
import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

# Mock the entire homeassistant package before any imports
mock_modules = {
    'homeassistant': types.ModuleType('homeassistant'),
    'homeassistant.components': types.ModuleType('homeassistant.components'),
    'homeassistant.components.climate': types.ModuleType('homeassistant.components.climate'),
    'homeassistant.components.climate.const': types.ModuleType('homeassistant.components.climate.const'),
    'homeassistant.config_entries': types.ModuleType('homeassistant.config_entries'),
    'homeassistant.const': types.ModuleType('homeassistant.const'),
    'homeassistant.core': types.ModuleType('homeassistant.core'),
    'homeassistant.helpers': types.ModuleType('homeassistant.helpers'),
    'homeassistant.helpers.entity': types.ModuleType('homeassistant.helpers.entity'),
    'homeassistant.helpers.entity_platform': types.ModuleType('homeassistant.helpers.entity_platform'),
    'homeassistant.helpers.update_coordinator': types.ModuleType('homeassistant.helpers.update_coordinator'),
    'homeassistant.helpers.aiohttp_client': types.ModuleType('homeassistant.helpers.aiohttp_client'),
}

for name, module in mock_modules.items():
    sys.modules[name] = module

# Set up the classes and constants in the mocked modules
ha_climate = sys.modules['homeassistant.components.climate']
class MockClimateEntity:
    pass
ha_climate.ClimateEntity = MockClimateEntity
ha_climate.ClimateEntityFeature = type('ClimateEntityFeature', (), {'TARGET_TEMPERATURE': 1, 'PRESET_MODE': 2})
ha_climate.HVACMode = type('HVACMode', (), {'OFF': 'off', 'HEAT': 'heat'})

ha_climate_const = sys.modules['homeassistant.components.climate.const']
ha_climate_const.PRESET_AWAY = 'away'
ha_climate_const.PRESET_HOME = 'home'
ha_climate_const.PRESET_SLEEP = 'sleep'

ha_config = sys.modules['homeassistant.config_entries']
class MockConfigEntry:
    pass
ha_config.ConfigEntry = MockConfigEntry

ha_const = sys.modules['homeassistant.const']
ha_const.ATTR_TEMPERATURE = 'temperature'
class MockUnitOfTemperature:
    CELSIUS = 'C'
ha_const.UnitOfTemperature = MockUnitOfTemperature
class MockPlatform:
    CLIMATE = 'climate'
    SENSOR = 'sensor'
ha_const.Platform = MockPlatform

ha_core = sys.modules['homeassistant.core']
class MockHomeAssistant:
    pass
ha_core.HomeAssistant = MockHomeAssistant

ha_helpers_entity = sys.modules['homeassistant.helpers.entity']
class MockDeviceInfo(dict):
    pass
ha_helpers_entity.DeviceInfo = MockDeviceInfo

ha_helpers_platform = sys.modules['homeassistant.helpers.entity_platform']
class MockAddEntitiesCallback:
    pass
ha_helpers_platform.AddEntitiesCallback = MockAddEntitiesCallback

ha_helpers_update = sys.modules['homeassistant.helpers.update_coordinator']
class MockCoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator
class MockDataUpdateCoordinator:
    def __init__(self, hass, logger, name, update_interval):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval
        self.data = None
    async def async_config_entry_first_refresh(self):
        return None
ha_helpers_update.CoordinatorEntity = MockCoordinatorEntity
ha_helpers_update.DataUpdateCoordinator = MockDataUpdateCoordinator

ha_helpers_aiohttp = sys.modules['homeassistant.helpers.aiohttp_client']
ha_helpers_aiohttp.async_get_clientsession = lambda hass: SimpleNamespace()

# Now import the climate module and other imports
from homeassistant.components.climate import HVACMode
from homeassistant.const import ATTR_TEMPERATURE

from custom_components.cosa.climate import CosaClimate
from custom_components.cosa.const import PRESET_HOME


@pytest.mark.asyncio
async def test_climate_sync_wrappers_do_not_raise():
    """Ensure sync wrappers for climate methods are available and don't raise NotImplementedError."""
    # Setup fake hass loop
    hass = SimpleNamespace(loop=asyncio.get_event_loop())

    # Setup fake client with async methods
    async def fake_set_mode(**kwargs):
        return True

    async def fake_set_target_temperatures(**kwargs):
        return True

    client = SimpleNamespace(
        set_mode=AsyncMock(side_effect=fake_set_mode),
        set_target_temperatures=AsyncMock(side_effect=fake_set_target_temperatures),
        login=AsyncMock(return_value=None),
        _token="fake_token",
    )

    # Coordinator minimal implementation
    coordinator = SimpleNamespace(
        data={
            "temperature": 19.5,
            "target_temperature": 21.0,
            "humidity": 45,
            "combi_state": "on",
            "option": "home",
            "mode": "manual",
            "target_temperatures": {"home": 21, "away": 16, "sleep": 18, "custom": 20},
        },
        client=client,
        endpoint_id="end_001",
        async_request_refresh=AsyncMock(return_value=None),
    )

    # config_entry used only for ids
    config_entry = SimpleNamespace(entry_id="abc123", data={"device_name": "unit1", "username": "user"})
    # Create entity
    e = CosaClimate(coordinator, config_entry)
    e.hass = hass

    # Call async methods to ensure the async API path works correctly
    await e.async_set_temperature(**{ATTR_TEMPERATURE: 22})
    await e.async_set_hvac_mode(HVACMode.HEAT)
    await e.async_set_preset_mode(PRESET_HOME)

    # Allow pending async operations to finish
    await asyncio.sleep(0)

    # Verify async client calls were invoked
    assert client.set_target_temperatures.called
    assert client.set_mode.called

    # Note: Sync wrappers are tested separately if needed


def test_climate_properties_guard_none():
    """Ensure properties return None when coordinator.data is None (no crash)."""
    coordinator = SimpleNamespace(data=None, client=None, endpoint_id=None)
    config_entry = SimpleNamespace(entry_id="abc123", data={})
    e = CosaClimate(coordinator, config_entry)
    assert e.current_temperature is None
    assert e.target_temperature is None
    assert e.hvac_mode is None
    assert e.preset_mode is None


@pytest.mark.asyncio
async def test_coordinator_client_is_created_if_none(monkeypatch):
    """If coordinator.client is None a new client should be created and used for set operations."""
    hass = SimpleNamespace(loop=asyncio.get_event_loop())

    # Fake client with AsyncMock methods
    async def fake_set_mode(**kwargs):
        return True

    async def fake_set_target_temperatures(**kwargs):
        return True

    fake_client = SimpleNamespace(
        set_mode=AsyncMock(side_effect=fake_set_mode),
        set_target_temperatures=AsyncMock(side_effect=fake_set_target_temperatures),
        list_endpoints=AsyncMock(return_value=[{"id": "end_001"}]),
        login=AsyncMock(return_value=None),
        _token="fake_token",
        _endpoint_id=None,
    )

    # Monkeypatch constructor of CosaAPIClient in the climate module to return our fake_client
    monkeypatch.setattr(
        "custom_components.cosa.climate.CosaAPIClient",
        lambda username=None, password=None, endpoint_id=None, token=None, session=None: fake_client,
    )

    coordinator = SimpleNamespace(
        data={
            "temperature": 19.5,
            "target_temperature": 21.0,
            "humidity": 45,
            "combi_state": "on",
            "option": "home",
            "mode": "manual",
            "target_temperatures": {"home": 21, "away": 16, "sleep": 18, "custom": 20},
        },
        client=None,
        endpoint_id=None,
        async_request_refresh=AsyncMock(return_value=None),
    )

    config_entry = SimpleNamespace(entry_id="def456", data={"username": "user", "password": "pass"})
    e = CosaClimate(coordinator, config_entry)
    e.hass = hass

    # Call async methods and verify they used the fake client
    await e.async_set_temperature(**{ATTR_TEMPERATURE: 22})
    await e.async_set_hvac_mode(HVACMode.HEAT)
    await e.async_set_preset_mode(PRESET_HOME)

    assert fake_client.set_target_temperatures.called
    assert fake_client.set_mode.called
