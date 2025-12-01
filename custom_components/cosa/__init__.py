"""COSA Smart Thermostat Integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CosaAPI, CosaAPIError, CosaAuthError
from .const import DOMAIN, PLATFORMS, CONF_ENDPOINT_ID, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class CosaCoordinator(DataUpdateCoordinator):
    """COSA Veri Koordinatörü."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: CosaAPI,
        email: str,
        password: str,
        token: str,
        endpoint_id: str,
        place_id: str | None,
        device_name: str,
    ) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        
        self.api = api
        self._email = email
        self._password = password
        self._token = token
        self._endpoint_id = endpoint_id
        self._place_id = place_id
        self.device_name = device_name

    @property
    def endpoint_id(self) -> str:
        return self._endpoint_id

    @property
    def token(self) -> str:
        return self._token

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            detail = await self.api.get_endpoint_detail(self._endpoint_id, self._token)
            
            forecast = {}
            if self._place_id:
                forecast = await self.api.get_forecast(self._place_id, self._token)
            
            return {
                "endpoint": detail,
                "forecast": forecast,
            }
            
        except CosaAuthError:
            login_result = await self.api.login(self._email, self._password)
            if login_result.get("ok"):
                self._token = login_result.get("token")
                detail = await self.api.get_endpoint_detail(self._endpoint_id, self._token)
                return {"endpoint": detail, "forecast": {}}
            raise UpdateFailed("Giriş başarısız")
            
        except CosaAPIError as err:
            raise UpdateFailed(f"API hatası: {err}") from err

    async def async_set_mode(self, mode: str, option: str | None = None) -> None:
        try:
            await self.api.set_mode(self._endpoint_id, mode, option, self._token)
            await self.async_request_refresh()
        except CosaAuthError:
            login_result = await self.api.login(self._email, self._password)
            if login_result.get("ok"):
                self._token = login_result.get("token")
                await self.api.set_mode(self._endpoint_id, mode, option, self._token)
                await self.async_request_refresh()

    async def async_set_temperatures(self, home: float, away: float, sleep: float, custom: float) -> None:
        try:
            await self.api.set_target_temperatures(self._endpoint_id, home, away, sleep, custom, self._token)
            await self.async_request_refresh()
        except CosaAuthError:
            login_result = await self.api.login(self._email, self._password)
            if login_result.get("ok"):
                self._token = login_result.get("token")
                await self.api.set_target_temperatures(self._endpoint_id, home, away, sleep, custom, self._token)
                await self.async_request_refresh()

    async def async_set_child_lock(self, enabled: bool) -> None:
        try:
            await self.api.set_child_lock(self._endpoint_id, enabled, self._token)
            await self.async_request_refresh()
        except CosaAuthError:
            login_result = await self.api.login(self._email, self._password)
            if login_result.get("ok"):
                self._token = login_result.get("token")
                await self.api.set_child_lock(self._endpoint_id, enabled, self._token)
                await self.async_request_refresh()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entegrasyonu kur."""
    hass.data.setdefault(DOMAIN, {})
    
    session = async_get_clientsession(hass)
    api = CosaAPI(session)
    
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    endpoint_id = entry.data.get(CONF_ENDPOINT_ID)
    
    try:
        # Login
        login_result = await api.login(email, password)
        if not login_result.get("ok"):
            _LOGGER.error("Giriş başarısız")
            return False
        
        token = login_result.get("token")
        
        # Endpoint ID yoksa ilk cihazı al
        if not endpoint_id:
            endpoints = await api.get_endpoints(token)
            if not endpoints:
                _LOGGER.error("Cihaz bulunamadı")
                return False
            endpoint_id = endpoints[0].get("id")
        
        # Detaylı bilgi al
        detail = await api.get_endpoint_detail(endpoint_id, token)
        
        # Hava durumu için place_id al
        place_id = detail.get("place")
        
        # Coordinator oluştur
        coordinator = CosaCoordinator(
            hass=hass,
            api=api,
            email=email,
            password=password,
            token=token,
            endpoint_id=endpoint_id,
            place_id=place_id,
            device_name=detail.get("name", "COSA Termostat"),
        )
        
        # İlk veri yüklemesi
        await coordinator.async_config_entry_first_refresh()
        
        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "api": api,
        }
        
    except CosaAPIError as err:
        _LOGGER.error("API hatası: %s", err)
        return False
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entegrasyonu kaldır."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
