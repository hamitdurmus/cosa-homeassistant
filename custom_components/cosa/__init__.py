"""COSA Smart Thermostat Entegrasyonu.

Bu entegrasyon COSA akıllı termostatları Home Assistant'a ekler.
HACS üzerinden kurulabilir.

Desteklenen Platformlar:
- climate: Termostat kontrolü (mod, sıcaklık, preset)
- sensor: Sıcaklık, nem, kombi durumu sensörleri

API Endpoint'leri (kiwi-api.nuvia.com.tr):
- POST /api/users/login → JWT Token
- POST /api/users/getInfo → Kullanıcı bilgisi + cihazlar
- POST /api/endpoints/setMode → Mod değiştirme
- POST /api/endpoints/setTargetTemperatures → Sıcaklık ayarı
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Desteklenen platformlar
PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """COSA entegrasyonunu config entry'den kur.
    
    Bu fonksiyon Home Assistant tarafından entegrasyon kurulduğunda çağrılır.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry (kullanıcı bilgileri, token, endpoint_id içerir)
        
    Returns:
        True başarılı ise
    """
    _LOGGER.info("COSA entegrasyonu kuruluyor: %s", entry.entry_id)
    
    # Domain için veri yapısını oluştur
    hass.data.setdefault(DOMAIN, {})
    
    # Entry verileri (email, password, token, endpoint_id)
    hass.data[DOMAIN][entry.entry_id] = {
        "email": entry.data.get("email"),
        "password": entry.data.get("password"),
        "token": entry.data.get("token"),
        "endpoint_id": entry.data.get("endpoint_id"),
        "device_name": entry.data.get("device_name", "COSA Termostat"),
    }
    
    # Platformları kur (climate ve sensor)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("COSA entegrasyonu başarıyla kuruldu")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """COSA entegrasyonunu kaldır.
    
    Args:
        hass: Home Assistant instance
        entry: Kaldırılacak config entry
        
    Returns:
        True başarılı ise
    """
    _LOGGER.info("COSA entegrasyonu kaldırılıyor: %s", entry.entry_id)
    
    # Platformları kaldır
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Entry verisini temizle
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.info("COSA entegrasyonu başarıyla kaldırıldı")
    
    return unload_ok
