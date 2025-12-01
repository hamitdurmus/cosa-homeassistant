"""COSA Smart Thermostat API Client.

Bu modül COSA termostat API'si ile iletişimi sağlar.
Tüm endpoint'ler ve request body yapıları gerçek mobil uygulama
trafiğinden alınmıştır.

API Endpoint'leri:
- POST /api/users/login → JWT Token alma
- POST /api/users/getInfo → Kullanıcı bilgisi ve endpoint'ler
- POST /api/endpoints/setMode → Mod değiştirme
- POST /api/endpoints/setTargetTemperatures → Sıcaklık ayarı
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import aiohttp

from .const import (
    API_BASE_URL,
    API_TIMEOUT,
    ENDPOINT_LOGIN,
    ENDPOINT_GET_INFO,
    ENDPOINT_SET_MODE,
    ENDPOINT_SET_TARGET_TEMPERATURES,
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
    """COSA Termostat API İstemcisi.
    
    Gerçek mobil uygulama trafiğine %100 uyumlu API istemcisi.
    
    Kullanım:
        api = CosaAPI(session)
        token = await api.login(email, password)
        info = await api.get_user_info(token)
        await api.set_mode(token, endpoint_id, "manual", "home")
        await api.set_target_temperatures(token, endpoint_id, {...})
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """API istemcisini başlat.
        
        Args:
            session: Home Assistant'ın aiohttp oturumu (async_get_clientsession)
        """
        self._session = session

    def _get_base_headers(self) -> dict[str, str]:
        """Temel HTTP header'larını döndür.
        
        Returns:
            Gerçek Cosa uygulamasının kullandığı header'lar
        """
        return {
            "User-Agent": HEADER_USER_AGENT,
            "Content-Type": HEADER_CONTENT_TYPE,
            "provider": HEADER_PROVIDER,
        }

    def _get_auth_headers(self, token: str) -> dict[str, str]:
        """Kimlik doğrulamalı header'ları döndür.
        
        Args:
            token: JWT auth token
            
        Returns:
            authtoken header'ı eklenmiş header'lar
        """
        headers = self._get_base_headers()
        headers["authtoken"] = token
        return headers

    async def login(self, email: str, password: str) -> str:
        """Kullanıcı girişi yap ve JWT token al.
        
        API Request:
            POST https://kiwi-api.nuvia.com.tr/api/users/login
            Body: {"email": "<email>", "password": "<password>"}
        
        Args:
            email: Kullanıcı e-posta adresi
            password: Kullanıcı şifresi
            
        Returns:
            JWT auth token
            
        Raises:
            CosaAuthError: Geçersiz kimlik bilgileri
            CosaAPIError: API hatası
        """
        url = f"{API_BASE_URL}{ENDPOINT_LOGIN}"
        
        # Gerçek API body yapısı - email kullanıyor
        payload = {
            "email": email,
            "password": password,
        }
        
        _LOGGER.debug("Login isteği gönderiliyor: %s", url)
        
        try:
            async with self._session.post(
                url,
                json=payload,
                headers=self._get_base_headers(),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                response_text = await response.text()
                _LOGGER.debug("Login yanıtı: status=%s", response.status)
                
                if response.status == 401:
                    _LOGGER.error("Geçersiz kimlik bilgileri")
                    raise CosaAuthError("Geçersiz e-posta veya şifre")
                
                if response.status != 200:
                    _LOGGER.error("Login hatası: %s - %s", response.status, response_text)
                    raise CosaAPIError(f"Login başarısız: HTTP {response.status}")
                
                data = await response.json()
                
                # Token'ı yanıttan çıkar
                token = self._extract_token(data)
                if not token:
                    _LOGGER.error("Token yanıtta bulunamadı: %s", data)
                    raise CosaAPIError("Token yanıtta bulunamadı")
                
                _LOGGER.info("COSA API'ye başarıyla giriş yapıldı")
                return token
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Bağlantı hatası: %s", err)
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    def _extract_token(self, data: dict) -> Optional[str]:
        """API yanıtından token'ı çıkar.
        
        Args:
            data: API yanıtı
            
        Returns:
            JWT token veya None
        """
        # Olası token alanları
        token_keys = ["authtoken", "authToken", "token", "accessToken", "access_token"]
        
        # Doğrudan üst seviyede ara
        for key in token_keys:
            if key in data and isinstance(data[key], str):
                return data[key]
        
        # data wrapper içinde ara
        if "data" in data and isinstance(data["data"], dict):
            for key in token_keys:
                if key in data["data"] and isinstance(data["data"][key], str):
                    return data["data"][key]
        
        return None

    async def get_user_info(self, token: str) -> dict[str, Any]:
        """Kullanıcı bilgilerini ve endpoint'leri al.
        
        API Request:
            POST https://kiwi-api.nuvia.com.tr/api/users/getInfo
            Header: authtoken: <token>
        
        Bu çağrıdan dönen veriler:
        - endpoint id'leri
        - cihaz bilgileri (sıcaklık, nem, mod, option, targetTemperatures)
        - cihaz adları
        
        Args:
            token: JWT auth token
            
        Returns:
            Kullanıcı bilgileri ve endpoint verileri
            
        Raises:
            CosaAuthError: Token geçersiz/süresi dolmuş
            CosaAPIError: API hatası
        """
        url = f"{API_BASE_URL}{ENDPOINT_GET_INFO}"
        
        _LOGGER.debug("GetInfo isteği gönderiliyor: %s", url)
        
        try:
            async with self._session.post(
                url,
                json={},
                headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 401:
                    _LOGGER.warning("Token geçersiz veya süresi dolmuş")
                    raise CosaAuthError("Token geçersiz veya süresi dolmuş")
                
                if response.status != 200:
                    response_text = await response.text()
                    _LOGGER.error("GetInfo hatası: %s - %s", response.status, response_text)
                    raise CosaAPIError(f"GetInfo başarısız: HTTP {response.status}")
                
                data = await response.json()
                _LOGGER.debug("GetInfo yanıtı alındı")
                return data
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Bağlantı hatası: %s", err)
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def set_mode(
        self,
        token: str,
        endpoint_id: str,
        mode: str,
        option: Optional[str] = None,
    ) -> bool:
        """Termostat modunu değiştir.
        
        API Request:
            POST https://kiwi-api.nuvia.com.tr/api/endpoints/setMode
            Header: authtoken: <token>, provider: cosa
            
        Body Yapıları:
        
        1. Haftalık Program:
           {"endpoint": "<id>", "mode": "schedule"}
           
        2. Otomatik Kontrol:
           {"endpoint": "<id>", "mode": "auto"}
           
        3. Manuel - Ev Modu:
           {"endpoint": "<id>", "mode": "manual", "option": "home"}
           
        4. Manuel - Uyku Modu:
           {"endpoint": "<id>", "mode": "manual", "option": "sleep"}
           
        5. Manuel - Dışarı Modu:
           {"endpoint": "<id>", "mode": "manual", "option": "away"}
           
        6. Manuel - Kullanıcı Modu:
           {"endpoint": "<id>", "mode": "manual", "option": "custom"}
           
        7. Kapalı (Frozen):
           {"endpoint": "<id>", "mode": "manual", "option": "frozen"}
        
        Args:
            token: JWT auth token
            endpoint_id: Termostat endpoint ID'si
            mode: "schedule", "auto", veya "manual"
            option: Manual mod için: "home", "sleep", "away", "custom", "frozen"
            
        Returns:
            True başarılı ise
            
        Raises:
            CosaAuthError: Token geçersiz
            CosaAPIError: API hatası
        """
        url = f"{API_BASE_URL}{ENDPOINT_SET_MODE}"
        
        # Request body oluştur
        payload: dict[str, Any] = {
            "endpoint": endpoint_id,
            "mode": mode,
        }
        
        # Manual mod için option ekle
        if mode == "manual" and option:
            payload["option"] = option
        
        _LOGGER.debug("SetMode isteği: %s - payload=%s", url, payload)
        
        try:
            async with self._session.post(
                url,
                json=payload,
                headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 401:
                    raise CosaAuthError("Token geçersiz veya süresi dolmuş")
                
                if response.status != 200:
                    response_text = await response.text()
                    _LOGGER.error("SetMode hatası: %s - %s", response.status, response_text)
                    raise CosaAPIError(f"SetMode başarısız: HTTP {response.status}")
                
                _LOGGER.info("Mod başarıyla değiştirildi: mode=%s, option=%s", mode, option)
                return True
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Bağlantı hatası: %s", err)
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err

    async def set_target_temperatures(
        self,
        token: str,
        endpoint_id: str,
        home: float,
        away: float,
        sleep: float,
        custom: float,
    ) -> bool:
        """Hedef sıcaklıkları ayarla.
        
        API Request:
            POST https://kiwi-api.nuvia.com.tr/api/endpoints/setTargetTemperatures
            Header: authtoken: <token>, provider: cosa
            
        Body:
            {
                "endpoint": "<id>",
                "targetTemperatures": {
                    "home": <float>,
                    "away": <float>,
                    "sleep": <float>,
                    "custom": <float>
                }
            }
        
        Args:
            token: JWT auth token
            endpoint_id: Termostat endpoint ID'si
            home: Ev modu sıcaklığı
            away: Dışarı modu sıcaklığı
            sleep: Uyku modu sıcaklığı
            custom: Kullanıcı modu sıcaklığı
            
        Returns:
            True başarılı ise
            
        Raises:
            CosaAuthError: Token geçersiz
            CosaAPIError: API hatası
        """
        url = f"{API_BASE_URL}{ENDPOINT_SET_TARGET_TEMPERATURES}"
        
        payload = {
            "endpoint": endpoint_id,
            "targetTemperatures": {
                "home": home,
                "away": away,
                "sleep": sleep,
                "custom": custom,
            },
        }
        
        _LOGGER.debug("SetTargetTemperatures isteği: %s - payload=%s", url, payload)
        
        try:
            async with self._session.post(
                url,
                json=payload,
                headers=self._get_auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 401:
                    raise CosaAuthError("Token geçersiz veya süresi dolmuş")
                
                if response.status != 200:
                    response_text = await response.text()
                    _LOGGER.error("SetTargetTemperatures hatası: %s - %s", response.status, response_text)
                    raise CosaAPIError(f"SetTargetTemperatures başarısız: HTTP {response.status}")
                
                _LOGGER.info(
                    "Hedef sıcaklıklar ayarlandı: home=%.1f, away=%.1f, sleep=%.1f, custom=%.1f",
                    home, away, sleep, custom
                )
                return True
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Bağlantı hatası: %s", err)
            raise CosaAPIError(f"Bağlantı hatası: {err}") from err


def parse_endpoint_data(user_info: dict[str, Any]) -> list[dict[str, Any]]:
    """GetInfo yanıtından endpoint verilerini çıkar.
    
    Args:
        user_info: GetInfo API yanıtı
        
    Returns:
        Endpoint listesi
    """
    endpoints = []
    
    # Olası yapılar
    if isinstance(user_info, dict):
        # data.endpoints yapısı
        if "data" in user_info and isinstance(user_info["data"], dict):
            data = user_info["data"]
            if "endpoints" in data and isinstance(data["endpoints"], list):
                endpoints = data["endpoints"]
            elif "endpoint" in data:
                ep = data["endpoint"]
                endpoints = ep if isinstance(ep, list) else [ep]
        # endpoints doğrudan
        elif "endpoints" in user_info and isinstance(user_info["endpoints"], list):
            endpoints = user_info["endpoints"]
        elif "endpoint" in user_info:
            ep = user_info["endpoint"]
            endpoints = ep if isinstance(ep, list) else [ep]
    elif isinstance(user_info, list):
        endpoints = user_info
    
    return endpoints


def extract_endpoint_state(endpoint: dict[str, Any]) -> dict[str, Any]:
    """Endpoint verisinden durum bilgilerini çıkar.
    
    Args:
        endpoint: Endpoint verisi
        
    Returns:
        Normalize edilmiş durum bilgisi
    """
    target_temps = endpoint.get("targetTemperatures", {})
    option = endpoint.get("option", "home")
    mode = endpoint.get("mode", "manual")
    
    # Aktif preset'e göre hedef sıcaklığı belirle
    if mode in ("auto", "schedule"):
        # Auto/schedule modunda home sıcaklığını kullan
        current_target = target_temps.get("home")
    else:
        # Manual modda aktif option'a göre sıcaklık
        current_target = target_temps.get(option, target_temps.get("home"))
    
    return {
        "endpoint_id": endpoint.get("_id") or endpoint.get("id") or endpoint.get("endpoint"),
        "name": endpoint.get("name", "COSA Termostat"),
        "temperature": endpoint.get("temperature"),
        "humidity": endpoint.get("humidity"),
        "target_temperature": current_target,
        "mode": mode,
        "option": option,
        "combi_state": endpoint.get("combiState", "off"),
        "target_temperatures": {
            "home": target_temps.get("home", 20.0),
            "away": target_temps.get("away", 15.0),
            "sleep": target_temps.get("sleep", 18.0),
            "custom": target_temps.get("custom", 20.0),
        },
    }
