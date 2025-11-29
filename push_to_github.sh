#!/bin/bash

# GitHub'a push script'i
# Kullanım: ./push_to_github.sh

echo "🚀 GitHub'a yükleme başlıyor..."

# GitHub CLI ile login kontrolü
if ! gh auth status &>/dev/null; then
    echo "⚠️  GitHub'a giriş yapmanız gerekiyor."
    echo "Lütfen şu komutu çalıştırın: gh auth login"
    exit 1
fi

# Repository oluştur ve push et
echo "📦 Repository oluşturuluyor..."
gh repo create cosa-homeassistant --public --source=. --remote=origin --push

if [ $? -eq 0 ]; then
    echo "✅ Başarıyla GitHub'a yüklendi!"
    echo "🔗 Repository URL: https://github.com/ahamitd/cosa-homeassistant"
    echo ""
    echo "📝 HACS'a eklemek için:"
    echo "1. Home Assistant'ta HACS'ı açın"
    echo "2. Entegrasyonlar > Özel Depolar"
    echo "3. URL: https://github.com/ahamitd/cosa-homeassistant"
    echo "4. Kategori: Integration"
else
    echo "❌ Hata oluştu. Lütfen manuel olarak deneyin."
    echo ""
    echo "Manuel komutlar:"
    echo "  git remote add origin https://github.com/ahamitd/cosa-homeassistant.git"
    echo "  git push -u origin main"
fi


