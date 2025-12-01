# GitHub'a Yükleme Talimatları

## 1. GitHub Kullanıcı Adınızı ve Repository Adınızı Belirleyin

Örneğin:
- GitHub kullanıcı adı: `ahamitd`
- Repository adı: `cosa-homeassistant`

## 2. GitHub'da Repository Oluşturun

1. https://github.com/new adresine gidin
2. Repository adını girin (örn: `cosa-homeassistant`)
3. Public veya Private seçin
4. **ÖNEMLİ:** "Initialize this repository with a README" seçeneğini işaretlemeyin (zaten README'miz var)
5. "Create repository" butonuna tıklayın

## 3. Git Konfigürasyonu (İlk kez yapıyorsanız)

```bash
git config --global user.name "Adınız Soyadınız"
git config --global user.email "email@example.com"
```

## 4. Manifest.json Dosyasını Güncelleyin

`custom_components/cosa/manifest.json` dosyasındaki `YOUR_USERNAME` yerine GitHub kullanıcı adınızı yazın.

## 5. GitHub'a Push Edin

Terminal'de şu komutları çalıştırın (YOUR_USERNAME ve REPO_NAME'i değiştirin):

```bash
# Remote ekle
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Branch'i main olarak ayarla
git branch -M main

# GitHub'a push et
git push -u origin main
```

## 6. HACS'a Ekleme

GitHub'a yükledikten sonra:

1. Home Assistant'ta HACS'ı açın
2. "Entegrasyonlar" sekmesine gidin
3. Sağ üstteki **⋮** menüsünden **"Özel Depolar"**ı seçin
4. Depo URL'sini ekleyin: `https://github.com/YOUR_USERNAME/REPO_NAME`
5. Kategori olarak **"Integration"** seçin
6. "COSA Termostat" entegrasyonunu arayın ve yükleyin

## Not

Eğer GitHub CLI kuruluysa, daha kolay bir yöntem:

```bash
# GitHub CLI kurulumu (macOS)
brew install gh

# GitHub'a login
gh auth login

# Repository oluştur ve push et
gh repo create cosa-homeassistant --public --source=. --remote=origin --push
```

