# YT Downloader (Tkinter + yt-dlp)

Aplikasi desktop downloader YouTube/video dengan Python, Tkinter, dan `yt-dlp`.

## Fitur
- Input URL video
- Mode download:
- Video (`.mp4`)
- Audio only (`.mp3`)
- Pilihan resolusi (`best`, `1080p`, `720p`, dll.)
- Pilihan FPS (jika tersedia)
- Progress bar + status
- Pilih folder output
- Nama file aman untuk Windows

## Prasyarat
- Python 3.10+ (disarankan)
- `ffmpeg` dan `ffprobe`, salah satu:
- Ada di `PATH`
- Atau simpan di `ffmpeg/bin/ffmpeg.exe` dan `ffmpeg/bin/ffprobe.exe`

## Virtual Environment (`.venv`)
```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Menjalankan Aplikasi
```powershell
python main.py
```

## Build EXE (Windows)
```powershell
pyinstaller --noconfirm --clean --onefile --noconsole --name "YtDownloader" --collect-all yt_dlp --add-data "ffmpeg;ffmpeg" main.py
```

Hasil build:
- `dist/YtDownloader.exe`

## File `.env`
Project ini mendukung konfigurasi lewat `.env`:
- `.env.example` untuk contoh
- `.env` untuk local config

Variabel yang dipakai:
- `DEFAULT_DOWNLOAD_DIR` untuk folder download default di UI
- `FFMPEG_DIR` untuk lokasi ffmpeg (folder `bin` atau path langsung ke `ffmpeg.exe`)

## Troubleshooting
- `ffmpeg not found`
- Pastikan `ffmpeg.exe` + `ffprobe.exe` ada di `ffmpeg/bin` atau `PATH`.
- `pip` tidak ada di `.venv`
- Jalankan `python -m ensurepip --upgrade` lalu `python -m pip install --upgrade pip`.
- EXE dianggap berbahaya antivirus
- Ini kadang terjadi pada mode `--onefile`. Coba build `--onedir` saat testing.
