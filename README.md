# YtDownloader — Social Media Video Downloader

> Aplikasi desktop untuk mendownload video/audio dari YouTube, TikTok, Instagram, X (Twitter), Facebook, dan ratusan platform lainnya.
> Dibangun dengan **Python**, **PySide6**, dan **yt-dlp**.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![PySide6](https://img.shields.io/badge/PySide6-6.8%2B-green?logo=qt)
![yt-dlp](https://img.shields.io/badge/yt--dlp-2025%2B-red)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)

---

## ✨ Fitur Utama

- **Multi-platform** — YouTube, TikTok, Instagram, X/Twitter, Facebook, dan ratusan situs lain
- **Mode Video & Audio** — Download video (`.mp4`, `.webm`, `.mkv`) atau audio saja (`.mp3`, `.m4a`, `.aac`, `.wav`, `.flac`, `.opus`)
- **Pilih Resolusi & FPS** — Analisis format tersedia secara otomatis (`best`, `1080p`, `720p`, `480p`, `360p`)
- **Queue System** — Tambahkan banyak URL ke antrian dan proses satu per satu
- **Estimasi Ukuran File** — Perkiraan ukuran sebelum download dimulai
- **Progress Real-time** — Progress bar dengan kecepatan dan estimasi waktu (ETA)
- **Download Progress Window** — Jendela terpisah yang muncul otomatis saat download berjalan, lengkap dengan status bytes dan tombol Cancel
- **Retry Otomatis** — Download gagal akan dicoba ulang dengan fallback strategy
- **Cookie Support** — Untuk konten private/restricted via browser atau file cookie
- **Bot-check Bypass** — Fallback otomatis ke YouTube client alternatif
- **Playlist Support** — Opsional download seluruh playlist
- **Validasi URL** — Validasi format URL sebelum proses analisis dimulai
- **Deteksi Duplikat** — URL yang sama tidak bisa ditambahkan ke antrian dua kali
- **Open Folder Shortcut** — Tombol "Open Folder" langsung membuka lokasi file setelah download selesai
- **Logging** — Log error dan aktivitas tersimpan otomatis ke `app.log` (rotasi 2MB)
- **Dark UI** — Antarmuka modern dark mode berbasis Qt
- **Build ke EXE** — Dukungan build standalone Windows via PyInstaller

---

## 📁 Struktur Proyek

```
YtDownloader/
├── main.py                  # Entry point aplikasi
├── requirements.txt         # Dependensi Python
├── pytest.ini               # Konfigurasi pytest
├── .env                     # Konfigurasi lokal (tidak di-commit)
├── .env.example             # Template .env
├── YtDownloader.spec        # Konfigurasi build PyInstaller (onefile)
├── YtDownloaderLite.spec    # Konfigurasi build PyInstaller (onedir)
├── app/
│   ├── __init__.py          # Package marker
│   ├── windows.py           # Jendela utama aplikasi (DownloaderWindow)
│   ├── dialogs.py           # Dialog Settings (SettingsDialog)
│   ├── models.py            # Data model DownloadJob
│   ├── progress_window.py   # Jendela progress download (DownloadProgressWindow)
│   └── utils.py             # Fungsi utilitas (ffmpeg, env, cookies, logging, dll.)
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Konfigurasi pytest (sys.path)
│   └── test_utils.py        # Unit tests untuk app/utils.py
├── ffmpeg/
│   └── bin/
│       ├── ffmpeg.exe       # (tidak di-commit, isi sendiri)
│       └── ffprobe.exe      # (tidak di-commit, isi sendiri)
└── icons/
    ├── icon.ico             # Ikon aplikasi
    └── icon_preview.png     # Preview ikon
```

---

## 🔧 Prasyarat

| Kebutuhan | Versi Minimum |
|-----------|--------------|
| Python | 3.10+ |
| pip | — |
| ffmpeg + ffprobe | Versi terbaru |

**ffmpeg** dibutuhkan untuk konversi/merge audio+video. Letakkan di:
- `ffmpeg/bin/ffmpeg.exe` dan `ffmpeg/bin/ffprobe.exe` *(direkomendasikan)*, atau
- Di `PATH` sistem, atau
- Set variabel `FFMPEG_DIR` di `.env`

> Download ffmpeg: https://www.gyan.dev/ffmpeg/builds/ (pilih `ffmpeg-release-essentials.zip`)

---

## 🚀 Instalasi & Menjalankan

### 1. Clone Repository

```powershell
git clone https://github.com/KimYo2/Yt-Downloader.git
cd Yt-Downloader
```

### 2. Buat Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Konfigurasi `.env` (Opsional)

```powershell
copy .env.example .env
# Edit .env sesuai kebutuhan
```

### 4. Siapkan ffmpeg

Letakkan `ffmpeg.exe` dan `ffprobe.exe` di folder `ffmpeg\bin\`.

### 5. Jalankan Aplikasi

```powershell
python main.py
```

---

## ⚙️ File `.env`

Salin `.env.example` ke `.env` dan sesuaikan:

```env
# Folder download default yang muncul di UI
DEFAULT_DOWNLOAD_DIR=C:\Users\YourUser\Downloads

# Lokasi ffmpeg (folder bin atau path langsung ke ffmpeg.exe)
FFMPEG_DIR=C:\path\to\ffmpeg\bin
```

---

## 🧪 Menjalankan Tests

```powershell
python -m pip install pytest
python -m pytest tests/ -v
```

Semua output pytest (`.pytest_cache/`) tidak di-commit ke repo.

---

## 🏗️ Build EXE (Windows)

### Onefile (satu file portabel)

```powershell
pyinstaller --noconfirm --clean YtDownloader.spec
# Output: dist\YtDownloader.exe
```

### Onedir (folder, lebih cepat startup)

```powershell
pyinstaller --noconfirm --clean YtDownloaderLite.spec
# Output: dist\YtDownloaderLite\YtDownloaderLite.exe
```

> ⚠️ Beberapa antivirus mendeteksi EXE `--onefile` sebagai false positive. Gunakan `--onedir` untuk testing.

---

## 🐛 Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `ffmpeg not found` | Pastikan `ffmpeg.exe` + `ffprobe.exe` ada di `ffmpeg/bin/` atau di PATH |
| `pip not found` di `.venv` | `python -m ensurepip --upgrade` lalu `python -m pip install --upgrade pip` |
| YouTube bot-check error | Aplikasi otomatis retry dengan client alternatif (android/web_safari) |
| Cookie error (browser terkunci) | Aplikasi otomatis retry tanpa cookie |
| EXE dianggap berbahaya antivirus | Gunakan mode `--onedir` saat testing |
| Video private/restricted | Gunakan fitur cookie dari browser atau file cookie `Netscape` |
| Error saat download | Lihat `app.log` di folder aplikasi untuk detail lengkap |

---

## 📦 Dependensi

| Package | Fungsi |
|---------|--------|
| `yt-dlp >= 2025.1.0` | Engine download utama |
| `PySide6 >= 6.8.0` | GUI framework (Qt6) |
| `python-dotenv >= 1.0.0` | Load konfigurasi dari `.env` |
| `pyinstaller >= 6.0` | Build ke EXE Windows |

---

## 📄 Lisensi

Proyek ini untuk keperluan pribadi dan edukasi. Pastikan penggunaan sesuai dengan Terms of Service platform yang bersangkutan.

> Aplikasi desktop untuk mendownload video/audio dari YouTube, TikTok, Instagram, X (Twitter), Facebook, dan ratusan platform lainnya.
> Dibangun dengan **Python**, **PySide6**, dan **yt-dlp**.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![PySide6](https://img.shields.io/badge/PySide6-6.8%2B-green?logo=qt)
![yt-dlp](https://img.shields.io/badge/yt--dlp-2025%2B-red)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)

---

## ✨ Fitur Utama

- **Multi-platform** — YouTube, TikTok, Instagram, X/Twitter, Facebook, dan ratusan situs lain
- **Mode Video & Audio** — Download video (`.mp4`, `.webm`, `.mkv`) atau audio saja (`.mp3`, `.m4a`, `.aac`, `.wav`, `.flac`, `.opus`)
- **Pilih Resolusi & FPS** — Analisis format tersedia secara otomatis (`best`, `1080p`, `720p`, `480p`, `360p`)
- **Queue System** — Tambahkan banyak URL ke antrian dan proses satu per satu
- **Estimasi Ukuran File** — Perkiraan ukuran sebelum download dimulai
- **Progress Real-time** — Progress bar dengan kecepatan dan estimasi waktu (ETA)
- **Retry Otomatis** — Download gagal akan dicoba ulang dengan fallback strategy
- **Cookie Support** — Untuk konten private/restricted via browser atau file cookie
- **Bot-check Bypass** — Fallback otomatis ke YouTube client alternatif
- **Playlist Support** — Opsional download seluruh playlist
- **Dark UI** — Antarmuka modern dark mode berbasis Qt
- **Build ke EXE** — Dukungan build standalone Windows via PyInstaller

---

## 📁 Struktur Proyek

```
YtDownloader/
├── main.py                  # Entry point aplikasi
├── requirements.txt         # Dependensi Python
├── settings.json            # Konfigurasi yang disimpan aplikasi
├── .env                     # Konfigurasi lokal (tidak di-commit)
├── .env.example             # Template .env
├── YtDownloader.spec        # Konfigurasi build PyInstaller (onefile)
├── YtDownloaderLite.spec    # Konfigurasi build PyInstaller (onedir)
├── app/
│   ├── __init__.py          # Package marker
│   ├── windows.py           # Jendela utama aplikasi (DownloaderWindow)
│   ├── dialogs.py           # Dialog Settings (SettingsDialog)
│   ├── models.py            # Data model DownloadJob
│   └── utils.py             # Fungsi utilitas (ffmpeg, env, cookies, dll.)
├── ffmpeg/
│   └── bin/
│       ├── ffmpeg.exe       # (tidak di-commit, isi sendiri)
│       └── ffprobe.exe      # (tidak di-commit, isi sendiri)
└── icons/
    ├── icon.ico             # Ikon aplikasi
    └── icon_preview.png     # Preview ikon
```

---

## 🔧 Prasyarat

| Kebutuhan | Versi Minimum |
|-----------|--------------|
| Python | 3.10+ |
| pip | — |
| ffmpeg + ffprobe | Versi terbaru |

**ffmpeg** dibutuhkan untuk konversi/merge audio+video. Letakkan di:
- `ffmpeg/bin/ffmpeg.exe` dan `ffmpeg/bin/ffprobe.exe` *(direkomendasikan)*, atau
- Di `PATH` sistem, atau
- Set variabel `FFMPEG_DIR` di `.env`

> Download ffmpeg: https://www.gyan.dev/ffmpeg/builds/ (pilih `ffmpeg-release-essentials.zip`)

---

## 🚀 Instalasi & Menjalankan

### 1. Clone Repository

```powershell
git clone https://github.com/KimYo2/Yt-Downloader.git
cd Yt-Downloader
```

### 2. Buat Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Konfigurasi `.env` (Opsional)

```powershell
copy .env.example .env
# Edit .env sesuai kebutuhan
```

### 4. Siapkan ffmpeg

Letakkan `ffmpeg.exe` dan `ffprobe.exe` di folder `ffmpeg\bin\`.

### 5. Jalankan Aplikasi

```powershell
python main.py
```

---

## ⚙️ File `.env`

Salin `.env.example` ke `.env` dan sesuaikan:

```env
# Folder download default yang muncul di UI
DEFAULT_DOWNLOAD_DIR=C:\Users\YourUser\Downloads

# Lokasi ffmpeg (folder bin atau path langsung ke ffmpeg.exe)
FFMPEG_DIR=C:\path\to\ffmpeg\bin
```

---

## 🏗️ Build EXE (Windows)

### Onefile (satu file portabel)

```powershell
pyinstaller --noconfirm --clean YtDownloader.spec
# Output: dist\YtDownloader.exe
```

### Onedir (folder, lebih cepat startup)

```powershell
pyinstaller --noconfirm --clean YtDownloaderLite.spec
# Output: dist\YtDownloaderLite\YtDownloaderLite.exe
```

> ⚠️ Beberapa antivirus mendeteksi EXE `--onefile` sebagai false positive. Gunakan `--onedir` untuk testing.

---

## 🐛 Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `ffmpeg not found` | Pastikan `ffmpeg.exe` + `ffprobe.exe` ada di `ffmpeg/bin/` atau di PATH |
| `pip not found` di `.venv` | `python -m ensurepip --upgrade` lalu `python -m pip install --upgrade pip` |
| YouTube bot-check error | Aplikasi otomatis retry dengan client alternatif (android/web_safari) |
| Cookie error (browser terkunci) | Aplikasi otomatis retry tanpa cookie |
| EXE dianggap berbahaya antivirus | Gunakan mode `--onedir` saat testing |
| Video private/restricted | Gunakan fitur cookie dari browser atau file cookie `Netscape` |

---

## 📦 Dependensi

| Package | Fungsi |
|---------|--------|
| `yt-dlp >= 2025.1.0` | Engine download utama |
| `PySide6 >= 6.8.0` | GUI framework (Qt6) |
| `python-dotenv >= 1.0.0` | Load konfigurasi dari `.env` |
| `pyinstaller >= 6.0` | Build ke EXE Windows |

---

## 📄 Lisensi

Proyek ini untuk keperluan pribadi dan edukasi. Pastikan penggunaan sesuai dengan Terms of Service platform yang bersangkutan.
