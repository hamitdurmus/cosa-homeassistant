"""COSA Smart Termostat Entegrasyonu - Stable Polling Version."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CosaAPI, CosaAPIError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Stabil polling - WebSocket problemi çözülünce eklenecek
UPDATE_INTERVAL = timedelta(seconds=15)  # 15 saniye optimal

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entegrasyonu kur."""
    hass.data.setdefault(DOMAIN, {})
    
    session = async_get_clientsession(hass)
    api = CosaAPI(session)
    
    # Login
    email = entry.data.get("email")
    password = entry.data.get("password")
    
    login_result = await api.login(email, password)
    if not login_result.get("ok"):
        _LOGGER.error("COSA login başarısız")
        return False
    
    token = login_result.get("token")
    endpoint_id = entry.data.get("endpoint_id")
    
    # Data fetch fonksiyonu
    async def async_update_data():
        """Veriyi API'den al."""
        try:
            endpoint = await api.get_endpoint_detail(endpoint_id, token)
            
            forecast = {}
            reports = {}
            place_id = endpoint.get("place")
            if place_id:
                forecast = await api.get_forecast(place_id, token)
            
            # Rapor verilerini al
            reports = await api.get_reports(endpoint_id, token)
            
            return {"endpoint": endpoint, "forecast": forecast, "reports": reports}
            
        except CosaAPIError as err:
            raise UpdateFailed(f"API hatası: {err}") from err
    
    # Coordinator oluştur - stabil polling
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="COSA",
        update_method=async_update_data,
        update_interval=UPDATE_INTERVAL,
    )
    
    await coordinator.async_config_entry_first_refresh()
    
    # Coordinator'a yardımcı metodlar ekle
    coordinator.api = api
    coordinator.token = token
    coordinator.endpoint_id = endpoint_id
    
    def _get_current_calibration() -> float:
        """Mevcut kalibrasyon değerini al."""
        if coordinator.data:
            return coordinator.data.get("endpoint", {}).get("calibration", 0.0)
        return 0.0
    
    def _is_open_window_enabled() -> bool:
        """Açık pencere özelliğinin aktif olup olmadığını kontrol et."""
        if coordinator.data:
            return coordinator.data.get("endpoint", {}).get("openWindowEnable", False)
        return False
    
    coordinator._get_current_calibration = _get_current_calibration
    coordinator._is_open_window_enabled = _is_open_window_enabled
    
    async def async_set_mode(mode: str, option: Optional[str] = None) -> bool:
        """Mod değiştir."""
        result = await api.set_mode(endpoint_id, mode, option, token)
        if result:
            await coordinator.async_request_refresh()
        return result
    
    async def async_set_temperatures(home: float, away: float, sleep: float, custom: float) -> bool:
        """Tüm sıcaklıkları ayarla."""
        _LOGGER.info("🔧 Sıcaklık ayarlanıyor: home=%s, away=%s, sleep=%s, custom=%s", 
                     home, away, sleep, custom)
        
        try:
            result = await api.set_target_temperatures(endpoint_id, home, away, sleep, custom, token)
            _LOGGER.info("API sonuç: %s", result)
            
            if result:
                # Kısa bir bekleme sonrası refresh - API'nin işlemesi için
                await asyncio.sleep(1)
                await coordinator.async_request_refresh()
            
            return result
        except Exception as err:
            _LOGGER.error("Sıcaklık ayarlama hatası: %s", err)
            return False
    
    async def async_set_preset_temperature(preset: str, temperature: float) -> bool:
        """Preset sıcaklığını ayarla."""
        endpoint = coordinator.data.get("endpoint", {}) if coordinator.data else {}
        
        temps = {
            "home": endpoint.get("homeTemperature", 21.0),
            "away": endpoint.get("awayTemperature", 18.0),
            "sleep": endpoint.get("sleepTemperature", 19.0),
            "custom": endpoint.get("customTemperature", 22.0),
        }
        temps[preset] = temperature
        
        result = await api.set_target_temperatures(
            endpoint_id,
            temps["home"], temps["away"], temps["sleep"], temps["custom"],
            token
        )
        if result:
            await asyncio.sleep(1)
            await coordinator.async_request_refresh()
        return result
    
    async def async_set_open_window(enabled: bool) -> bool:
        """Açık pencere algılama özelliğini ayarla."""
        calibration = _get_current_calibration()
        result = await api.set_device_settings(
            endpoint_id, 
            calibration, 
            open_window_enable=enabled,
            open_window_duration=30,
            token=token
        )
        if result:
            await coordinator.async_request_refresh()
        return result
    
    async def async_set_calibration(value: float) -> bool:
        """Kalibrasyonu ayarla."""
        open_window_enabled = _is_open_window_enabled()
        result = await api.set_device_settings(
            endpoint_id, 
            value, 
            open_window_enable=open_window_enabled,
            open_window_duration=30,
            token=token
        )
        if result:
            await coordinator.async_request_refresh()
        return result
    
    coordinator.async_set_mode = async_set_mode
    coordinator.async_set_temperatures = async_set_temperatures
    coordinator.async_set_preset_temperature = async_set_preset_temperature
    coordinator.async_set_open_window = async_set_open_window
    coordinator.async_set_calibration = async_set_calibration
    
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "token": token,
    }
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entegrasyonu kaldır."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
