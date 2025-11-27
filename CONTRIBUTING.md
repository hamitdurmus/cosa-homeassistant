# Katkıda Bulunma Rehberi

Bu projeye katkıda bulunmak istediğiniz için teşekkürler! İşte nasıl başlayabileceğiniz:

## Geliştirme Ortamı Kurulumu

1. Repository'yi fork edin
2. Fork'unuzu klonlayın:
   ```bash
   git clone https://github.com/YOUR_USERNAME/cosa-homeassistant.git
   cd cosa-homeassistant
   ```
3. Home Assistant geliştirme ortamınızı hazırlayın

## Kod Standartları

- Python kodları PEP 8 standartlarına uygun olmalıdır
- Home Assistant kod stilini takip edin
- Yeni özellikler için test yazın (mümkünse)
- Dokümantasyonu güncelleyin

## Pull Request Gönderme

1. Yeni bir branch oluşturun:
   ```bash
   git checkout -b feature/amazing-feature
   ```
2. Değişikliklerinizi yapın ve commit edin:
   ```bash
   git commit -m 'Add some amazing feature'
   ```
3. Branch'inizi push edin:
   ```bash
   git push origin feature/amazing-feature
   ```
4. GitHub'da Pull Request oluşturun

## Commit Mesajları

Commit mesajlarınız açıklayıcı olmalıdır:
- `feat: Add new feature`
- `fix: Fix bug in API client`
- `docs: Update README`
- `refactor: Improve code structure`

## Hata Bildirimi

Hata bildirirken lütfen şunları ekleyin:
- Home Assistant versiyonu
- Entegrasyon versiyonu
- Hata mesajları/loglar
- Adım adım yeniden üretme talimatları

## Sorular?

Herhangi bir sorunuz varsa, lütfen bir issue açın.

