# OdakGrupPersonaMakinasi

## 🚀 Proje Amacı

Bu proje, **odak grup tartışmalarını** simüle eden, yapay zekâ destekli, modern ve görsel olarak zengin bir web uygulamasıdır. Kullanıcılar, farklı persona profilleriyle gerçekçi tartışmalar başlatabilir, tartışma akışını yönetebilir, analiz raporu alabilir ve tüm süreci PDF olarak indirebilir.

---

## 📸 Ekran Görüntüsü

> (Buraya uygulamanın bir ekran görüntüsünü ekleyebilirsiniz.)

---

## 🛠️ Özellikler

- **Çoklu Persona Desteği:** Her biri farklı geçmiş, bilgi, tarz ve profil fotoğrafına sahip katılımcılar.
- **Gündem Yükleme:** CSV veya Excel dosyasından tartışma gündemleri yüklenebilir.
- **Simülasyon Akışı:** Moderatör ve katılımcılar arasında gerçekçi, çok turlu tartışma.
- **Durdur & Devam Ettir:** Simülasyon istenildiği anda durdurulabilir.
- **Canlı Tartışma Görüntüleme:** Modern, karanlık temalı, profil fotoğraflı ve zaman damgalı mesaj kutuları.
- **Analiz Raporu:** Tartışma sonunda otomatik olarak detaylı analiz raporu oluşturulur.
- **PDF İndir:** Tüm tartışma ve analiz, modern formatta PDF olarak indirilebilir.
- **API Anahtarı Yönetimi:** (Gerekirse) LLM API anahtarı değişimi ve rate limit yönetimi.
- **Kapsamlı Hata Yönetimi:** Kullanıcı dostu hata ve durum mesajları.

---

## 📂 Dosya ve Klasör Yapısı

```
OdakGrupPersonaMakinasi/
├── main.py                # Simülasyonun çekirdeği, persona ve tartışma yönetimi
├── streamlit_app.py       # Streamlit tabanlı modern web arayüzü
├── requirements.txt       # Gerekli Python kütüphaneleri
├── .env                   # (Varsa) API anahtarları ve gizli bilgiler
├── .gitignore             # Git için gereksiz dosya filtreleri
├── data/
│   ├── DATA TUTMA MAKİNASI.csv
│   └── DATA TUTMA MAKİNASI.xlsx
├── personas/
│   ├── elif.json
│   ├── hatice_teyze.json
│   ├── kenan_bey.json
│   └── tugrul_bey.json
├── personas_pp/
│   ├── elif.jpg
│   ├── hatice_teyze.jpg
│   ├── kenan_bey.jpg
│   └── tugrul_bey.jpg
└── venv/                  # Sanal Python ortamı (git'e eklenmez)
```

---

## ⚙️ Kurulum

1. **Projeyi klonla:**
   ```bash
   git clone git@github.com:barancanercan/OdakGrupPersonaMakinasi.git
   cd OdakGrupPersonaMakinasi
   ```

2. **Sanal ortamı oluştur ve aktif et:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Gerekli kütüphaneleri yükle:**
   ```bash
   pip install -r requirements.txt
   ```

4. **(Varsa) .env dosyasını oluştur ve API anahtarlarını ekle:**
   ```
   GEMINI_API_KEY=...
   GEMINI_API_KEY_2=...
   ```

5. **Profil fotoğraflarını ve persona JSON dosyalarını kontrol et.**

---

## 🚦 Kullanım

1. **Uygulamayı başlat:**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Tarayıcıda açılan arayüzde:**
   - Gündem dosyasını yükle (CSV/Excel)
   - "Odak Grup Makinasını Başlat" butonuna tıkla
   - Tartışmayı canlı takip et, durdurmak istersen "Durdur" butonunu kullan
   - Tartışma sonunda analiz raporunu ve PDF çıktısını indir

---

## 👤 Persona Tanımı

Her persona için `personas/` klasöründe bir JSON dosyası bulunur. Örnek:
```json
{
  "name": "Elif",
  "bio": ["Üniversite öğrencisi", "İstanbul'da yaşıyor"],
  "lore": ["Gezi olaylarına katıldı", "Sosyal medya aktif"],
  "knowledge": ["Siyaset", "Ekonomi"],
  "topics": ["Gündem", "Gençlik"],
  "style": {"type": "chat", "adjectives": ["samimi", "doğal"]},
  "adjectives": ["meraklı", "duygusal"],
  "role": "Katılımcı",
  "personality": "Dışa dönük"
}
```
Profil fotoğrafı ise `personas_pp/elif.jpg` veya `personas_pp/elif.png` olarak eklenmelidir.

---

## 📝 Gündem Dosyası Formatı

- CSV veya Excel dosyası olmalı.
- Her satır bir gündem maddesini temsil etmeli.
- Örnek başlıklar: `type, link, title, content, comments`

---

## 🖨️ PDF Çıktısı

- Tüm tartışma ve analiz, Unicode destekli, modern bir PDF olarak indirilebilir.
- PDF'de profil fotoğrafları, isimler, saat, konuşma balonları ve analiz bölümü yer alır.

---

## 🧩 Bağımlılıklar

- `streamlit`
- `pandas`
- `fpdf2`
- `python-dotenv`

Ek olarak, profil fotoğrafları için `personas_pp/` klasöründe uygun görseller bulunmalıdır.

---

## 🛡️ Güvenlik ve Gizlilik

- `.env` dosyanızı ve API anahtarlarınızı asla repoya eklemeyin.
- `.gitignore` dosyası bu dosyaları otomatik olarak hariç tutar.

---

## 🧑‍💻 Katkı ve Geliştirme

- Pull request ve issue açabilirsiniz.
- Yeni persona eklemek için `personas/` klasörüne JSON, `personas_pp/` klasörüne görsel ekleyin.

---

## 📄 Lisans

MIT
