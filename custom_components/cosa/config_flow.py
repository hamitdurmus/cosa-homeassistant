"""COSA Smart Thermostat Config Flow.

Bu modül Home Assistant için COSA entegrasyonunun kurulum akışını yönetir.
Kullanıcı e-posta ve şifre girer, API'den token alınır ve endpoint tespit edilir.

Kurulum Akışı:
1. Kullanıcı e-posta ve şifre girer
2. API'ye login isteği gönderilir
3. Token alınır
4. getInfo ile endpoint bilgileri alınır
5. Config entry oluşturulur
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CosaAPI, CosaAPIError, CosaAuthError, parse_endpoint_data
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Kullanıcı giriş formu şeması
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("email", description="E-posta adresi"): str,
        vol.Required("password", description="Şifre"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Kullanıcı girişini doğrula ve bağlantıyı test et.
    
    Args:
        hass: Home Assistant instance
        data: Kullanıcı tarafından girilen veriler (email, password)
        
    Returns:
        Başarılı doğrulama sonucu (title, token, endpoint_id, device_name)
        
    Raises:
        InvalidAuth: Geçersiz kimlik bilgileri
        CannotConnect: Bağlantı hatası
    """
    session = async_get_clientsession(hass)
    api = CosaAPI(session)
    
    email = data["email"]
    password = data["password"]
    
    try:
        # 1. Login yap ve token al
        _LOGGER.debug("Login denemesi: %s", email)
        token = await api.login(email, password)
        
        # 2. Kullanıcı bilgilerini al (endpoint'ler dahil)
        _LOGGER.debug("Kullanıcı bilgileri alınıyor...")
        user_info = await api.get_user_info(token)
        
        # 3. Endpoint'leri parse et
        endpoints = parse_endpoint_data(user_info)
        
        if not endpoints:
            _LOGGER.error("Kullanıcıya ait endpoint bulunamadı")
            raise CannotConnect("Cihaz bulunamadı")
        
        # İlk endpoint'i kullan
        first_endpoint = endpoints[0]
        endpoint_id = (
            first_endpoint.get("_id") 
            or first_endpoint.get("id") 
            or first_endpoint.get("endpoint")
        )
        device_name = first_endpoint.get("name", "COSA Termostat")
        
        _LOGGER.info(
            "Doğrulama başarılı: endpoint_id=%s, device_name=%s",
            endpoint_id,
            device_name,
        )
        
        return {
            "title": f"COSA Termostat ({email})",
            "token": token,
            "endpoint_id": endpoint_id,
            "device_name": device_name,
        }
        
    except CosaAuthError as err:
        _LOGGER.error("Kimlik doğrulama hatası: %s", err)
        raise InvalidAuth from err
        
    except CosaAPIError as err:
        _LOGGER.error("API hatası: %s", err)
        raise CannotConnect from err
        
    except Exception as err:
        _LOGGER.exception("Beklenmeyen hata: %s", err)
        raise CannotConnect from err


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """COSA entegrasyonu için config flow handler."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """İlk kurulum adımını yönet.
        
        Kullanıcıdan e-posta ve şifre alır, doğrulama yapar.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Girişi doğrula
                info = await validate_input(self.hass, user_input)
                
                # Benzersiz ID olarak e-posta kullan
                await self.async_set_unique_id(user_input["email"])
                self._abort_if_unique_id_configured()
                
                # Config entry verilerini hazırla
                entry_data = {
                    "email": user_input["email"],
                    "password": user_input["password"],
                    "token": info["token"],
                    "endpoint_id": info["endpoint_id"],
                    "device_name": info["device_name"],
                }
                
                return self.async_create_entry(
                    title=info["title"],
                    data=entry_data,
                )
                
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Beklenmeyen hata")
                errors["base"] = "unknown"

        # Formu göster
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Bağlantı kurulamadı hatası."""


class InvalidAuth(HomeAssistantError):
    """Geçersiz kimlik bilgileri hatası."""
