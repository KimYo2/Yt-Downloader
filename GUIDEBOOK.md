# 📘 YtDownloader — Guidebook Lengkap

> Panduan lengkap penggunaan, konfigurasi, build, dan pengembangan aplikasi **YtDownloader**.

---

## Daftar Isi

1. [Pengenalan](#1-pengenalan)
2. [Prasyarat & Instalasi](#2-prasyarat--instalasi)
3. [Konfigurasi Awal](#3-konfigurasi-awal)
4. [Cara Menggunakan Aplikasi](#4-cara-menggunakan-aplikasi)
5. [Pengaturan (Settings)](#5-pengaturan-settings)
6. [Sistem Queue (Antrian)](#6-sistem-queue-antrian)
7. [Cookie & Konten Private](#7-cookie--konten-private)
8. [Build ke File EXE](#8-build-ke-file-exe)
9. [Struktur Kode (Developer Guide)](#9-struktur-kode-developer-guide)
10. [Troubleshooting](#10-troubleshooting)
11. [FAQ](#11-faq)

---

## 1. Pengenalan

**YtDownloader** adalah aplikasi desktop Windows untuk mendownload video dan audio dari berbagai platform media sosial dan situs video populer, antara lain:

- **YouTube** (video, audio, playlist)
- **TikTok**
- **Instagram** (Reels, video post)
- **X / Twitter**
- **Facebook**
- **Dan ratusan situs lain** yang didukung oleh [yt-dlp](https://github.com/yt-dlp/yt-dlp)

### Teknologi yang Digunakan

| Komponen | Teknologi |
|----------|-----------|
| Bahasa | Python 3.10+ |
| GUI | PySide6 (Qt6) |
| Download Engine | yt-dlp |
| Audio/Video Processing | ffmpeg |
| Konfigurasi | python-dotenv |
| Build EXE | PyInstaller |

---

## 2. Prasyarat & Instalasi

### 2.1 Install Python

Download Python 3.10 atau lebih baru dari https://www.python.org/downloads/

Saat instalasi, **centang** opsi **"Add Python to PATH"**.

Verifikasi:
```powershell
python --version
# Python 3.11.x (atau lebih baru)
```

### 2.2 Clone / Download Proyek

```powershell
git clone https://github.com/KimYo2/Yt-Downloader.git
cd Yt-Downloader
```

Atau download ZIP dari halaman GitHub lalu ekstrak.

### 2.3 Buat Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Setelah aktif, prompt terminal akan berubah menjadi:
```
(.venv) PS C:\...\Yt-Downloader>
```

### 2.4 Install Dependensi Python

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Paket yang akan diinstall:

| Paket | Fungsi |
|-------|--------|
| `yt-dlp` | Engine download utama |
| `PySide6` | GUI framework Qt6 |
| `python-dotenv` | Load file `.env` |
| `pyinstaller` | Build ke EXE (opsional) |

### 2.5 Siapkan ffmpeg

ffmpeg diperlukan untuk:
- Menggabungkan (merge) stream video + audio terpisah
- Konversi format audio (mp3, m4a, aac, dll.)

**Cara install ffmpeg:**

1. Download dari https://www.gyan.dev/ffmpeg/builds/
   - Pilih: `ffmpeg-release-essentials.zip`
2. Ekstrak arsip tersebut
3. Salin `ffmpeg.exe` dan `ffprobe.exe` ke dalam folder `ffmpeg\bin\` di proyek:

```
YtDownloader/
└── ffmpeg/
    └── bin/
        ├── ffmpeg.exe    ← letakkan di sini
        └── ffprobe.exe   ← letakkan di sini
```

> Alternatif: Tambahkan folder bin ffmpeg ke PATH sistem Windows, atau set `FFMPEG_DIR` di file `.env`.

---

## 3. Konfigurasi Awal

### 3.1 File `.env`

Buat file `.env` dari template yang sudah disediakan:

```powershell
copy .env.example .env
```

Buka `.env` dengan teks editor dan sesuaikan:

```env
# Folder tujuan download default yang ditampilkan di UI
# Kosongkan untuk menggunakan folder Downloads bawaan sistem
DEFAULT_DOWNLOAD_DIR=C:\Users\NamaKamu\Downloads

# Lokasi ffmpeg — isi jika tidak menggunakan folder ffmpeg/bin di proyek
# Bisa berupa folder (yang berisi ffmpeg.exe) atau path langsung ke ffmpeg.exe
FFMPEG_DIR=C:\path\to\ffmpeg\bin
```

> **Catatan:** File `.env` tidak ikut di-commit ke Git (sudah ada di `.gitignore`).

### 3.2 File `settings.json`

File ini dibuat dan diperbarui otomatis oleh aplikasi saat kamu menyimpan pengaturan melalui menu **Settings**. Kamu tidak perlu mengeditnya secara manual.

Nilai default:

```json
{
  "default_download_dir": "<folder Downloads sistem>",
  "show_success_popup": true,
  "auto_analyze": false,
  "auto_start_queue": true,
  "default_download_playlist": false,
  "cookies_from_browser": "none",
  "cookies_file": "",
  "max_retries": 2
}
```

---

## 4. Cara Menggunakan Aplikasi

### 4.1 Menjalankan Aplikasi

Aktifkan virtual environment terlebih dahulu:

```powershell
.\.venv\Scripts\activate
python main.py
```

### 4.2 Tampilan Antarmuka

Antarmuka terdiri dari 4 bagian utama:

```
┌─────────────────────────────────────────┐
│           Social Media Downloader       │  ← Judul
├──────── Source ─────────────────────────┤
│  URL   [___________________________] [Analyze URL]
│  Title  Video title akan muncul di sini
├──────── Download Options ───────────────┤
│  Mode    ○ Video  ○ Audio
│  Resolution  [best ▼]
│  FPS         [auto ▼]
│  Video format [best ▼]
│  Audio format [mp3 ▼]
│  Save to [___path___] [Browse Folder]
├──────── Queue ──────────────────────────┤
│  [daftar antrian download]
│  [Add] [Remove] [Start] [Cancel] [Clear] [Settings]
├─────────────────────────────────────────┤
│  [Progress Bar]
│  Status: Ready.
└─────────────────────────────────────────┘
```

### 4.3 Langkah Download Video

**Step 1 — Paste URL**

Salin URL video dari browser, lalu paste di kolom **URL**.

**Step 2 — Analisis Format (Opsional tapi Dianjurkan)**

Klik tombol **Analyze URL** untuk mengambil informasi format yang tersedia.

- Kolom **Title** akan terisi judul video secara otomatis
- Dropdown **Resolution** akan diperbarui dengan resolusi yang tersedia
- Dropdown **FPS** akan diperbarui sesuai resolusi yang dipilih

> Jika **Auto Analyze** diaktifkan di Settings, proses ini berjalan otomatis saat URL ditempel.

**Step 3 — Pilih Opsi Download**

| Opsi | Keterangan |
|------|-----------|
| **Mode: Video** | Download video (dengan audio) |
| **Mode: Audio** | Download audio saja |
| **Resolution** | `best` = kualitas tertinggi, atau pilih spesifik (contoh: `720p`) |
| **FPS** | `auto` = otomatis, atau pilih FPS spesifik (contoh: `30 fps`) |
| **Video format** | `best`, `mp4`, `webm`, `mkv` |
| **Audio format** | `mp3`, `m4a`, `aac`, `wav`, `flac`, `opus` |
| **Save to** | Folder tujuan penyimpanan file hasil download |

**Step 4 — Tambahkan ke Antrian**

Klik **Add To Queue**. Item akan masuk ke daftar antrian dengan info:
```
[QUEUED] VIDEO | Judul Video | Est. size: 123.4 MB | https://...
```

**Step 5 — Mulai Download**

- Jika **Auto Start Queue** aktif (default), download langsung dimulai saat ditambahkan.
- Jika tidak, klik tombol **Start Queue** secara manual.

**Step 6 — Pantau Progress**

Progress bar dan status akan menampilkan:
```
Downloading... 45.2% | 2.3 MB/s | ETA 32s
```

Setelah selesai, akan muncul popup konfirmasi (jika diaktifkan di Settings).

---

## 5. Pengaturan (Settings)

Buka **Settings** dengan klik tombol **Settings** di area Queue.

| Pengaturan | Default | Keterangan |
|-----------|---------|-----------|
| **Default folder** | Downloads | Folder download yang akan digunakan saat aplikasi dibuka |
| **Max retries** | 2 | Jumlah percobaan ulang jika download gagal (0-5) |
| **Cookies from browser** | none | Ambil cookie dari browser untuk konten restricted |
| **Cookies file** | — | Path ke file cookie Netscape format (opsional) |
| **Show success popup** | ✅ | Tampilkan dialog saat download selesai |
| **Enable auto analyze** | ❌ | Otomatis analisis URL saat ditempel |
| **Auto start queue** | ✅ | Otomatis mulai download saat job ditambahkan |
| **Download playlist by default** | ❌ | Jika URL adalah playlist, download semua item |

---

## 6. Sistem Queue (Antrian)

YtDownloader memiliki sistem antrian sehingga kamu bisa menambahkan banyak URL sekaligus.

### Tombol Queue

| Tombol | Fungsi |
|--------|--------|
| **Add To Queue** | Tambahkan URL dengan opsi saat ini ke antrian |
| **Remove From Queue** | Hapus item yang dipilih dari antrian (kecuali yang sedang berjalan) |
| **Start Queue** | Mulai memproses antrian secara manual |
| **Cancel Current** | Batalkan download yang sedang berjalan |
| **Clear Done/Error** | Hapus semua item berstatus `DONE`, `ERROR`, atau `CANCELLED` dari tampilan |

### Status Item Queue

| Status | Keterangan |
|--------|-----------|
| `QUEUED` | Menunggu giliran |
| `DOWNLOADING` | Sedang didownload |
| `RETRYING` | Sedang dicoba ulang |
| `DONE` | Selesai berhasil |
| `ERROR` | Gagal setelah semua percobaan |
| `CANCELLED` | Dibatalkan oleh pengguna |

### Alur Kerja Queue

```
URL ditambahkan → [QUEUED]
       ↓
Start Queue → [DOWNLOADING]
       ↓
   Berhasil? → [DONE]
       ↓ Tidak
   Fallback → Coba format alternatif
       ↓ Masih gagal
   Retry → Coba ulang sesuai max_retries
       ↓ Semua gagal
      [ERROR]
```

---

## 7. Cookie & Konten Private

Beberapa video memerlukan autentikasi (login) untuk didownload, contohnya:
- Video YouTube age-restricted
- Konten Instagram/TikTok yang diprivate
- Video Facebook untuk teman saja

### 7.1 Cookie dari Browser

Di Settings, pilih browser yang sedang login:

```
Cookies from browser: [ chrome ▼ ]
```

Browser yang didukung:
`chrome`, `edge`, `firefox`, `brave`, `opera`, `vivaldi`, `safari`

> ⚠️ Pastikan browser **tidak sedang buka** (tertutup) saat menggunakan fitur ini, karena database cookie mungkin terkunci.
> Jika terkunci, aplikasi akan otomatis mencoba ulang **tanpa** cookie.

### 7.2 File Cookie (Netscape Format)

Untuk metode yang lebih stabil:

1. Install ekstensi browser: **Get cookies.txt LOCALLY** (Chrome/Edge) atau **cookies.txt** (Firefox)
2. Buka situs target (pastikan sudah login)
3. Ekspor cookie ke file `.txt`
4. Di Settings → **Cookies file** → Browse → pilih file `.txt` hasil ekspor
5. Klik **Save**

> File cookie format Netscape adalah standar yang digunakan yt-dlp.

---

## 8. Build ke File EXE

Kamu bisa mendistribusikan aplikasi sebagai file `.exe` tunggal tanpa perlu Python terinstall.

### 8.1 Persiapan

Pastikan:
- Virtual environment aktif
- `pyinstaller` sudah terinstall (`pip install pyinstaller`)
- `ffmpeg.exe` dan `ffprobe.exe` ada di `ffmpeg\bin\`
- `icon.ico` ada di folder `icons\`

### 8.2 Build Onefile (Satu File .exe)

```powershell
pyinstaller --noconfirm --clean YtDownloader.spec
```

- Output: `dist\YtDownloader.exe`
- Satu file portable, mudah didistribusikan
- Startup sedikit lebih lambat karena ekstrak ke temp folder

### 8.3 Build Onedir (Folder)

```powershell
pyinstaller --noconfirm --clean YtDownloaderLite.spec
```

- Output: `dist\YtDownloaderLite\YtDownloaderLite.exe`
- Startup lebih cepat
- Distribusi berupa folder (zip sebelum dibagikan)

### 8.4 Catatan Build

- File `settings.json` akan dibaca dari **folder yang sama** dengan `.exe`
- File `.env` juga dibaca dari folder `.exe`
- ffmpeg di-bundle otomatis sesuai konfigurasi `.spec`

> ⚠️ Beberapa antivirus (terutama Windows Defender) bisa menandai hasil build sebagai false positive. Ini adalah perilaku normal untuk `.exe` buatan PyInstaller. Gunakan mode `--onedir` jika menemui masalah ini.

---

## 9. Struktur Kode (Developer Guide)

### 9.1 Overview Arsitektur

```
main.py
  └── app/
       ├── windows.py    ← Jendela utama (DownloaderWindow)
       ├── dialogs.py    ← Dialog Settings (SettingsDialog)
       ├── models.py     ← Data model (DownloadJob)
       └── utils.py      ← Utilitas (ffmpeg, env, cookie, dll.)
```

### 9.2 `main.py` — Entry Point

Memuat environment (`.env`) lalu membuat instance `QApplication` dan `DownloaderWindow`.

```python
load_env()           # Load .env
app = QApplication(sys.argv)
window = DownloaderWindow()
window.show()
sys.exit(app.exec())
```

### 9.3 `app/models.py` — Data Model

`DownloadJob` adalah dataclass yang menyimpan semua konfigurasi satu job download:

```python
@dataclass
class DownloadJob:
    job_id: str          # UUID unik
    url: str             # URL video
    title: str           # Judul video
    folder: str          # Folder tujuan
    video_mode: bool     # True = video, False = audio only
    quality: str         # "best", "1080p", "720p", dst.
    fps: str             # "auto", "30 fps", "60 fps", dst.
    video_ext: str       # "best", "mp4", "webm", "mkv"
    audio_ext: str       # "mp3", "m4a", "aac", dst.
    download_playlist: bool
    retries: int
    status: str = "queued"
    attempt: int = 0
    estimated_size: int = 0
```

### 9.4 `app/utils.py` — Utilitas

| Fungsi | Deskripsi |
|--------|-----------|
| `runtime_base_dir()` | Mengembalikan base dir saat runtime (mendukung mode frozen/EXE) |
| `load_env()` | Load file `.env` menggunakan python-dotenv |
| `find_app_icon_path()` | Cari `icon.ico` / `icon.png` dari berbagai lokasi |
| `human_bytes(num)` | Konversi bytes ke string (B, KB, MB, GB, dst.) |
| `default_download_dir()` | Ambil folder download default dari env atau home |
| `detect_ffmpeg_location()` | Deteksi lokasi ffmpeg dari berbagai kandidat path |
| `is_working_ffmpeg_dir(folder)` | Verifikasi directory ffmpeg benar-benar berjalan |
| `apply_cookie_settings(opts, settings)` | Terapkan konfigurasi cookie ke opts yt-dlp |
| `strip_cookie_settings(opts)` | Hapus cookie dari opts (fallback saat terkunci) |
| `has_cookie_opts(opts)` | Cek apakah opts memiliki cookie |
| `is_cookie_copy_error(exc)` | Deteksi error akibat cookie browser terkunci |
| `is_youtube_bot_check_error(exc)` | Deteksi error bot-check YouTube |
| `apply_youtube_client_fallback(opts)` | Terapkan client Android/Safari sebagai fallback |

### 9.5 `app/windows.py` — Jendela Utama

`DownloaderWindow` mewarisi `QMainWindow`. Komunikasi antara worker thread dan UI menggunakan **thread-safe queue**.

**Alur komunikasi thread:**

```
Worker Thread
    │
    ▼ ui_queue.put({"type": "progress", ...})
    │
QTimer (100ms) → _poll_ui_queue()
    │
    ▼ Update UI (progress bar, status label, queue list)
```

**Metode penting:**

| Metode | Deskripsi |
|--------|-----------|
| `_build_ui()` | Bangun seluruh antarmuka Qt |
| `_apply_styles()` | Terapkan stylesheet dark mode |
| `on_fetch_formats()` | Trigger analisis URL (thread baru) |
| `_fetch_formats_worker()` | Worker: ambil format dari yt-dlp |
| `on_add_to_queue()` | Tambahkan DownloadJob ke antrian |
| `_process_next_job()` | Ambil job berikutnya dan mulai download |
| `_download_worker()` | Worker: download dengan retry & fallback |
| `_build_video_format_selector()` | Bangun format selector string yt-dlp |
| `_progress_hook()` | Callback progress dari yt-dlp |
| `_poll_ui_queue()` | Proses pesan dari worker ke UI (dipanggil timer) |
| `_estimate_file_size()` | Estimasi ukuran file dari format yang dianalisis |

### 9.6 `app/dialogs.py` — Dialog Settings

`SettingsDialog` adalah `QDialog` modal yang menampilkan semua opsi konfigurasi. Nilai disimpan/dimuat melalui:

```python
dialog.get_settings()  # Mengembalikan dict settings
```

### 9.7 Menambahkan Fitur Baru

**Contoh: Menambahkan pengaturan baru**

1. Tambahkan widget di `SettingsDialog.__init__()` → `dialogs.py`
2. Sertakan nilai di `get_settings()` → `dialogs.py`
3. Tambahkan default di `_load_settings()` → `windows.py`
4. Gunakan nilai dari `self.settings.get("nama_key")` di mana pun diperlukan

---

## 10. Troubleshooting

### ❌ `ffmpeg not found`

**Gejala:**
```
ffmpeg is required for merge/conversion.
Put ffmpeg in ./ffmpeg/bin or set FFMPEG_DIR in .env.
```

**Solusi:**
1. Pastikan `ffmpeg.exe` dan `ffprobe.exe` ada di `ffmpeg\bin\`
2. Atau set `FFMPEG_DIR=C:\path\to\ffmpeg\bin` di `.env`
3. Atau tambahkan folder bin ffmpeg ke PATH Windows

---

### ❌ `Sign in to confirm you're not a bot`

**Gejala:** YouTube menolak request karena dikira bot.

**Solusi:** Aplikasi otomatis mencoba ulang dengan client Android/Safari. Jika masih gagal:
- Aktifkan **Cookies from browser** di Settings (pilih browser yang login YouTube)
- Atau ekspor cookie dan gunakan **Cookies file**

---

### ❌ Cookie browser terkunci / `Could not copy Chrome cookie database`

**Gejala:** Browser sedang buka dan database cookie terkunci.

**Solusi:**
- Tutup browser lalu coba lagi, **atau**
- Ekspor cookie ke file `.txt` dan gunakan **Cookies file** di Settings

---

### ❌ `Format lookup failed` saat Analyze URL

**Gejala:** Analisis URL gagal.

**Penyebab umum:**
| Penyebab | Solusi |
|---------|--------|
| URL salah / tidak valid | Cek ulang URL dari browser |
| Konten private/restricted | Gunakan cookie browser/file |
| Rate limit dari platform | Tunggu beberapa menit dan coba lagi |
| yt-dlp outdated | Update: `pip install -U yt-dlp` |

---

### ❌ EXE diblokir antivirus

**Gejala:** Windows Defender atau antivirus menghapus/memblokir file `.exe`

**Solusi:**
- Gunakan build `--onedir` (`YtDownloaderLite.spec`) yang jarang false positive
- Tambahkan exception/exclusion di antivirus untuk folder `dist\`
- Submit file ke antivirus provider sebagai false positive report

---

### ❌ Download playlist hanya dapat 1 video

**Gejala:** Hanya video pertama yang didownload.

**Solusi:** Aktifkan **Download playlist by default** di Settings, atau centang opsi tersebut sebelum menambahkan ke queue.

---

### ❌ Virtual environment tidak bisa diaktifkan

**Gejala:**
```
.\.venv\Scripts\activate : File ... cannot be loaded because running scripts is disabled
```

**Solusi:** Jalankan PowerShell sebagai Administrator dan ketik:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 11. FAQ

**Q: Platform apa saja yang didukung?**

A: Semua platform yang didukung yt-dlp, termasuk YouTube, TikTok, Instagram, X/Twitter, Facebook, Vimeo, Dailymotion, Reddit, Twitch, dan masih banyak lagi. Lihat daftar lengkapnya di [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

---

**Q: Kenapa resolusi yang tersedia berbeda-beda tiap video?**

A: Setiap video memiliki format yang diupload berbeda. Resolusi yang tampil di dropdown adalah yang benar-benar tersedia untuk video tersebut (hasil dari analisis URL). Jika tidak ada video 1080p berarti uploader tidak mengupload dalam resolusi tersebut.

---

**Q: File disimpan di mana?**

A: Di folder yang dipilih di kolom **Save to**. Nama file mengikuti format:
```
Judul Video [video-id].ext
```
Karakter ilegal untuk Windows dihapus otomatis.

---

**Q: Apakah bisa download audio dari YouTube Music?**

A: Ya, gunakan URL dari YouTube (bukan YouTube Music) dengan mode **Audio** dan format `mp3` atau `m4a`.

---

**Q: Kenapa download lambat?**

A: Kecepatan bergantung pada:
- Koneksi internet kamu
- Server platform yang bersangkutan
- Resolusi yang dipilih (semakin tinggi, semakin besar file)

---

**Q: Apakah aman digunakan?**

A: Aplikasi ini menggunakan yt-dlp sebagai engine, tidak menyimpan data ke server manapun. Semua proses berjalan lokal di komputer kamu.

---

**Q: Bagaimana cara update yt-dlp?**

A: Aktifkan virtual environment lalu jalankan:
```powershell
pip install -U yt-dlp
```

Update rutin disarankan karena platform sering mengubah format URL / API mereka.

---

*Guidebook ini dibuat untuk YtDownloader v2.x (PySide6 edition).*
*Last updated: Maret 2026*
