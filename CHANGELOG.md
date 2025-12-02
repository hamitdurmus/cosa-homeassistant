# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-12-02

### Added
- **Rapor Sensörleri (Son 24 Saat İstatistikleri)**
  - Toplam Çalışma Süresi (saat)
  - Evde Modu Çalışma Süresi
  - Uyku Modu Çalışma Süresi
  - Ortalama Sıcaklık
  - Maksimum/Minimum Sıcaklık
  - Maksimum/Minimum Nem
  - Dış Ortam Ortalama Sıcaklık
  - Ağ Kalitesi
- **Çocuk Kilidi Switch** - Çocuk kilidi özelliğini açıp kapama
- **Açık Pencere Algılama Switch** - Açık pencere algılama özelliğini açıp kapama
- **Kalibrasyon Number** - Sıcaklık kalibrasyonu (-5°C ile +5°C arası)
- **Preset Sıcaklık Kontrolleri** - Evde, Dışarı, Uyku ve Manuel sıcaklıkları ayarlama

### Improved
- Optimistik güncellemeler ile daha hızlı UI yanıtı
- HVAC ve preset mod değişikliklerinde anlık görsel güncelleme
- API isteklerinde daha iyi hata yönetimi
- Kod optimizasyonları ve performans iyileştirmeleri

### Fixed
- UPDATE_INTERVAL import hatası düzeltildi
- Coordinator metodları düzeltildi
- openWindowEnable API parametresi düzeltildi

## [1.0.0] - 2024-01-01

### Added
- Initial release of COSA Home Assistant integration
- Support for COSA thermostat control
- Temperature control (5-32°C)
- Preset modes: Home, Away, Sleep, Custom
- HVAC mode control (Heat/Off)
- Humidity and temperature sensors
- Automatic updates every 10 seconds
- Config flow for easy setup
- Turkish language support for configuration

### Features
- Full thermostat control via Home Assistant
- Real-time temperature and humidity monitoring
- Multiple preset modes for different scenarios
- Secure authentication with COSA API
- Automatic endpoint detection
- Error handling and reconnection support
