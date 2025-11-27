# COSA Home Assistant Entegrasyonu

COSA termostatınızı Home Assistant'a entegre edin ve akıllı ev sisteminizin bir parçası haline getirin.

## 🎯 Özellikler

- ✅ **Termostat Kontrolü**: Kombiyi açıp kapatabilirsiniz
- ✅ **Sıcaklık Ayarı**: 5-32°C arası sıcaklık kontrolü
- ✅ **Preset Modları**: Ev, Dışarıda, Gece ve Özel modlar
- ✅ **Sensör Desteği**: Oda sıcaklığı ve nem sensörleri
- ✅ **Otomatik Güncelleme**: Her 60 saniyede bir otomatik veri güncelleme
- ✅ **Config Flow**: Kolay kurulum arayüzü
- ✅ **Türkçe Dil Desteği**: Tam Türkçe arayüz

## 📋 Gereksinimler

- Home Assistant 2023.1 veya üzeri
- Python 3.9 veya üzeri
- COSA uygulamasında aktif hesap
- İnternet bağlantısı

## 🚀 HACS ile Kurulum

1. HACS'ı açın
2. "Entegrasyonlar" sekmesine gidin
3. Sağ üstteki "..." menüsünden "Özel Depolar"ı seçin
4. Depo URL'sini ekleyin: `https://github.com/yourusername/cosa-homeassistant`
5. Kategori olarak "Integration" seçin
6. "COSA Termostat" entegrasyonunu arayın ve yükleyin
7. Home Assistant'ı yeniden başlatın

## ⚙️ Manuel Kurulum

1. `custom_components` klasörünü Home Assistant'ın `config` klasörüne kopyalayın
2. Home Assistant'ı yeniden başlatın
3. Ayarlar > Cihazlar ve Hizmetler > Entegrasyon Ekle
4. "COSA Termostat" entegrasyonunu arayın ve ekleyin
5. COSA uygulamasındaki kullanıcı adı ve şifrenizi girin

## 📖 Kullanım

### Termostat Kontrolü

- **Açık/Kapalı**: HVAC modunu değiştirerek kombiyi açıp kapatabilirsiniz
- **Sıcaklık Ayarı**: Hedef sıcaklığı ayarlayabilirsiniz
- **Preset Modları**: 
  - **Ev (Home)**: Ev modu
  - **Dışarıda (Away)**: Dışarıda modu
  - **Gece (Sleep)**: Gece modu
  - **Kullanıcı (Custom)**: Özel mod

### Sensörler

Entegrasyon aşağıdaki bilgileri sağlar:

- Mevcut Sıcaklık
- Hedef Sıcaklık
- Nem Oranı
- Kombi Durumu
- Aktif Mod

## 🔧 Sorun Giderme

### Bağlantı Hatası
- İnternet bağlantınızı kontrol edin
- COSA API'sinin erişilebilir olduğundan emin olun
- Firewall ayarlarınızı kontrol edin

### Kimlik Doğrulama Hatası
- Kullanıcı adı ve şifrenizin doğru olduğundan emin olun
- COSA uygulamasında giriş yapabildiğinizi kontrol edin

### Endpoint ID Bulunamadı
- Endpoint ID'yi manuel olarak girebilirsiniz
- COSA uygulamasından cihaz bilgilerinizi kontrol edin

## 📝 Notlar

- Entegrasyon COSA API'sini kullanarak çalışır
- Veriler 60 saniyede bir otomatik olarak güncellenir
- Token otomatik olarak yönetilir ve gerektiğinde yenilenir

## 🤝 Katkıda Bulunma

Hata bildirimi veya özellik istekleri için GitHub Issues kullanabilirsiniz.

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

