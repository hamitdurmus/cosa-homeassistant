"""COSA Smart Thermostat API Client."""

from __future__ import annotations

import logging
from typing import Any, Optional

import aiohttp

from .const import (
    API_BASE_URL,
    API_TIMEOUT,
    ENDPOINT_LOGIN,
    ENDPOINT_GET_ENDPOINTS,
    ENDPOINT_GET_ENDPOINT,
    ENDPOINT_SET_MODE,
    ENDPOINT_SET_TARGET_TEMPERATURES,
    ENDPOINT_GET_FORECAST,
    ENDPOINT_SET_COMBI_SETTINGS,
    HEADER_USER_AGENT,
    HEADER_CONTENT_TYPE,
    HEADER_PROVIDER,
)

_LOGGER = logging.getLogger(__name__)


class CosaAPIError(Exception):
    """COSA API hatası."""
    pass


class CosaAuthError(CosaAPIError):
    """Kimlik doğrulama hatası."""
    pass


class CosaAPI:
    """COSA Termostat API İstemcisi."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    def _get_base_headers(self) -> dict[str, str]:
        return {
            "User-Agent": HEADER_USER_AGENT,
            "Content-Type": HEADER_CONTENT_TYPE,
            "provider": HEADER_PROVIDER,
            "Accept": "*/*",
        }

    def _get_auth_headers(self, token: str) -> dict[str, str]:
        headers = self._get_base_headers()
        headers["authtoken"] = token
        return headers

    async def login(self, email: str, password: str) -> str:
        """Login ve token al."""
        url = f"{API_BASE_URL}{ENDPOINT_LOGIN}"
        payload = {"email": email, "password": password}
        
        try:
            async with self._session.post(
                url, json=payload, headers=self._get_base_headers(),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                
                if data.get("ok") == 0:
                    error_code = data.get("code", "unknown")
                    if error_code == 111:
                        raise CosaAuthError("Geçersiz e-posta veya şifre")
                    raise CosaAPIError(f"API hatası: code={error_code}")
                
                token = data.get("authToken")
                if not token:
                    raise CosaAPIError("Token bulunamadı")
                
                return token
                
        except aiohttp.ClientError as err:
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def get_endpoints(self, token: str) -> list[dict[str, Any]]:
        """Endpoint listesini al."""
        url = f"{API_BASE_URL}{ENDPOINT_GET_ENDPOINTS}"
        
        try:
            async with self._session.post(
                url, json={}, headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                
                if data.get("ok") == 0:
                    raise CosaAPIError(f"API hatası: {data.get('code')}")
                
                return data.get("endpoints", [])
                
        except aiohttp.ClientError as err:
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def get_endpoint_detail(self, token: str, endpoint_id: str) -> dict[str, Any]:
        """Endpoint detaylarını al."""
        url = f"{API_BASE_URL}{ENDPOINT_GET_ENDPOINT}"
        payload = {"endpoint": endpoint_id}
        
        try:
            async with self._session.post(
                url, json=payload, headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                
                if data.get("ok") == 0:
                    raise CosaAPIError(f"API hatası: {data.get('code')}")
                
                return data.get("endpoint", {})
                
        except aiohttp.ClientError as err:
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def get_forecast(self, token: str, place_id: str) -> dict[str, Any]:
        """Hava durumu tahminini al."""
        url = f"{API_BASE_URL}{ENDPOINT_GET_FORECAST}"
        payload = {"place": place_id}
        
        try:
            async with self._session.post(
                url, json=payload, headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                
                if data.get("ok") == 0:
                    return {}
                
                return data
                
        except aiohttp.ClientError:
            return {}

    async def set_mode(
        self, token: str, endpoint_id: str, mode: str, option: Optional[str] = None
    ) -> bool:
        """Mod değiştir."""
        url = f"{API_BASE_URL}{ENDPOINT_SET_MODE}"
        payload: dict[str, Any] = {"endpoint": endpoint_id, "mode": mode}
        if option:
            payload["option"] = option
        
        try:
            async with self._session.post(
                url, json=payload, headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                return data.get("ok") == 1
                
        except aiohttp.ClientError as err:
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def set_target_temperatures(
        self, token: str, endpoint_id: str,
        home: float, away: float, sleep: float, custom: float
    ) -> bool:
        """Hedef sıcaklıkları ayarla."""
        url = f"{API_BASE_URL}{ENDPOINT_SET_TARGET_TEMPERATURES}"
        payload = {
            "endpoint": endpoint_id,
            "targetTemperatures": {
                "home": home, "away": away, "sleep": sleep, "custom": custom
            }
        }
        
        try:
            async with self._session.post(
                url, json=payload, headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                return data.get("ok") == 1
                
        except aiohttp.ClientError as err:
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def set_child_lock(self, token: str, endpoint_id: str, enabled: bool) -> bool:
        """Çocuk kilidini ayarla."""
        url = f"{API_BASE_URL}{ENDPOINT_SET_COMBI_SETTINGS}"
        payload = {"endpoint": endpoint_id, "childLock": enabled}
        
        try:
            async with self._session.post(
                url, json=payload, headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                data = await response.json()
                return data.get("ok") == 1
                
        except aiohttp.ClientError:
            return False
