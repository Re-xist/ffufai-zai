<div align="center">

# `ffufai-zai`

![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

<p align="center">

**ffufai-zai** adalah fork dari [ffufai](https://github.com/jthack/ffufai) dengan tambahan dukungan **z.ai API**. Tool ini adalah wrapper berbasis AI untuk web fuzzer [ffuf](https://github.com/ffuf/ffuf) yang secara otomatis menyarankan file extension atau wordlist untuk fuzzing berdasarkan analisis URL target dan HTTP headers menggunakan AI.

</p>

</div>

---

## Apa Itu ffufai-zai?

Secara sederhana, ffufai-zai melakukan hal berikut:

1. Kamu memberikan URL target yang ingin di-fuzz
2. Tool mengambil HTTP headers dari target tersebut
3. Tool mengirim informasi target ke AI (z.ai / Anthropic / OpenAI)
4. AI menganalisis dan menghasilkan:
   - **Extension file** yang relevan (misalnya `.php`, `.bak`, `.json`) - atau -
   - **Wordlist** berisi daftar path/file yang kemungkinan ada di server
5. Hasilnya langsung diteruskan ke `ffuf` untuk fuzzing secara otomatis

**Keuntungan:** Kamu tidak perlu menebak extension atau wordlist secara manual - AI yang menganalisis teknologi server dan konteks target untuk memberikan saran yang paling relevan.

## Fitur

- Integrasi langsung dengan ffuf
- Dukungan **3 provider AI**: z.ai, Anthropic, dan OpenAI
- **Extension Suggestion** - AI menganalisis target dan menyarankan extension file yang relevan
- **Wordlist Generation** - AI membuat wordlist kontekstual berdasarkan teknologi dan konten target
- **Auto-Save Wordlist** - Wordlist otomatis tersimpan per target, bisa di-reuse untuk scan berikutnya
- **Smart Merge** - Gabung wordlist AI dengan saved wordlist dan wordlist external (misal SecLists)
- Semua parameter ffuf diteruskan langsung
- Handle redirect loop pada target SPA

---

## Panduan Instalasi Lengkap

> Ikuti langkah-langkah berikut satu per satu. Pastikan setiap langkah berhasil sebelum lanjut ke berikutnya.

### Langkah 1: Install Python 3

Cek apakah Python 3 sudah terinstall:

```bash
python3 --version
```

Jika belum ada, install terlebih dahulu:

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip -y

# macOS
brew install python3

# Arch Linux
sudo pacman -S python python-pip
```

### Langkah 2: Install Go (untuk ffuf)

Cek apakah Go sudah terinstall:

```bash
go version
```

Jika belum ada, install Go:

```bash
# Ubuntu/Debian
sudo apt install golang-go -y

# macOS
brew install go

# Atau download manual dari https://go.dev/dl/
```

### Langkah 3: Install ffuf

ffuf adalah tool fuzzing yang menjadi engine utama ffufai-zai.

```bash
go install github.com/ffuf/ffuf/v2@latest
```

Tambahkan Go bin ke PATH agar `ffuf` bisa dipanggil dari mana saja:

```bash
echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Verifikasi ffuf sudah terinstall:

```bash
ffuf -V
```

Harusnya muncul output seperti: `ffuf version: 2.1.0-dev`

> **Alternatif:** Jika tidak mau install Go, download binary ffuf langsung dari [ffuf releases](https://github.com/ffuf/ffuf/releases) dan taruh di PATH.

### Langkah 4: Clone Repository

```bash
git clone https://github.com/Re-xist/ffufai-zai.git
cd ffufai-zai
```

### Langkah 5: Install Python Dependencies

```bash
pip install requests openai anthropic beautifulsoup4
```

Jika `pip` tidak dikenali, coba:

```bash
pip3 install requests openai anthropic beautifulsoup4
```

### Langkah 6: Setup API Key

Ada **3 cara** untuk mengatur API key. Pilih yang paling nyaman.

### Cara 1: Via .env File (Paling Mudah)

Buat file `.env` di folder ffufai-zai, sekali buat dan langsung pakai tanpa perlu input ulang:

```bash
# Cara cepat: copy dari .env.example
cp .env.example .env

# Lalu edit dan isi API key kamu
nano .env
```

Atau buat manual:

```bash
cat > .env << 'EOF'
ANTHROPIC_AUTH_TOKEN=api-key-kamu
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
EOF
```

Contoh isi `.env` sesuai provider:

**Z.ai** (Direkomendasikan untuk pengguna Indonesia):

Dapatkan API key di: https://z.ai/manage-apikey/apikey-list atau beli via: https://apikuy.my.id/

```
ANTHROPIC_AUTH_TOKEN=api-key-kamu
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
```

**Anthropic (Claude):**

```
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

**OpenAI (GPT):**

```
OPENAI_API_KEY=sk-xxxxx
```

> File `.env` sudah masuk `.gitignore` jadi aman, tidak akan ter-push ke GitHub. Setelah dibuat, langsung jalankan `python3 ffufai.py` tanpa perlu tambahan apa-apa.

### Cara 2: Via Command Line

Langsung input API key saat menjalankan perintah:

```bash
# Z.ai
python3 ffufai.py --api-key 'api-key-kamu' --api-base-url 'https://api.z.ai/api/anthropic' -u https://target.com/FUZZ -w wordlist.txt -mc all -c

# Anthropic
python3 ffufai.py --api-key 'sk-ant-xxxxx' -u https://target.com/FUZZ -w wordlist.txt -mc all -c

# OpenAI
python3 ffufai.py --api-key 'sk-xxxxx' --api-type openai -u https://target.com/FUZZ -w wordlist.txt -mc all -c
```

> **Auto-detect:** Jika `--api-key` diberikan tanpa `--api-type`, tool otomatis mendeteksi:
> - Ada `--api-base-url` → z.ai
> - Tanpa `--api-base-url` → Anthropic

### Cara 3: Via Environment Variable

Set environment variable agar tidak perlu input ulang setiap kali:

```bash
# Z.ai
export ANTHROPIC_AUTH_TOKEN='paste-api-key-kamu-disini'
export ANTHROPIC_BASE_URL='https://api.z.ai/api/anthropic'

# Anthropic
export ANTHROPIC_API_KEY='paste-api-key-anthropic-kamu-disini'

# OpenAI
export OPENAI_API_KEY='paste-api-key-openai-kamu-disini'
```

**Buat permanen** (tidak hilang saat terminal ditutup):

```bash
# Contoh untuk z.ai
echo 'export ANTHROPIC_AUTH_TOKEN="api-key-kamu"' >> ~/.bashrc
echo 'export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"' >> ~/.bashrc
source ~/.bashrc
```

### Langkah 7: (Opsional) Buat Symlink

Agar `ffufai` bisa dipanggil dari direktori mana saja:

```bash
sudo ln -s $(pwd)/ffufai.py /usr/local/bin/ffufai
```

Setelah ini kamu bisa pakai `ffufai` langsung tanpa `python3 ffufai.py`.

### Langkah 8: Verifikasi Instalasi

Jalankan perintah berikut untuk memastikan semuanya berjalan:

```bash
python3 ffufai.py --help
```

Harusnya muncul output:
```
usage: ffufai.py [-h] [--ffuf-path FFUF_PATH]
                 [--max-extensions MAX_EXTENSIONS] [--wordlists]
                 [--max-wordlist-size MAX_WORDLIST_SIZE] [--include-response]
                 [--api-key API_KEY] [--api-base-url API_BASE_URL]
                 [--api-type {openai,anthropic,zai}]
                 [--merge WORDLIST_PATH]

ffufai - AI-powered ffuf wrapper
...
```

---

## Cara Menggunakan

ffufai-zai punya **2 mode** penggunaan:

### Mode 1: AI Wordlist Generation (Rekomendasi)

**Kapan dipakai:** Ingin langsung fuzzing tanpa repot cari wordlist. AI yang bikin wordlist yang sesuai target.

**Cara kerja:** AI menganalisis URL, headers, dan (opsional) konten halaman target, lalu membuat daftar path/file yang kemungkinan ada. **Tidak perlu file wordlist sama sekali.**

```bash
python3 ffufai.py --wordlists -u https://target.com/FUZZ -mc all -c
```

**Contoh nyata:**

```bash
python3 ffufai.py --wordlists --max-wordlist-size 50 -u https://target.com/api/FUZZ -mc all -c
```

Output:
```
{'wordlist': ['api', 'v1', 'v2', 'users', 'auth', 'login', 'admin', ...]}

        /'___\  /'___\
       ...
________________________________________________

 :: URL              : https://target.com/api/FUZZ
 :: Wordlist         : FUZZ: /tmp/tmpXXXXXX.txt
________________________________________________

admin                    [Status: 200, Size: 1234, Words: 45, Lines: 20]
login                    [Status: 200, Size: 890, Words: 30, Lines: 15]
v1                       [Status: 301, Size: 169, Words: 5, Lines: 8]
```

AI melihat URL `/api/` dan headers target, lalu otomatis generate wordlist berisi path yang relevan seperti `admin`, `login`, `v1`, dll. Tinggal duduk manis lihat hasilnya.

**Dengan konten halaman** (lebih akurat, AI baca isi halaman target juga):

```bash
python3 ffufai.py --wordlists --include-response -u https://target.com/FUZZ -mc all -c
```

**Atur ukuran wordlist:**

```bash
# Wordlist 50 entry (lebih cepat)
python3 ffufai.py --wordlists --max-wordlist-size 50 -u https://target.com/FUZZ -mc all -c

# Wordlist 500 entry (lebih lengkap)
python3 ffufai.py --wordlists --max-wordlist-size 500 -u https://target.com/FUZZ -mc all -c
```

**Auto-Save & Reuse:**

Wordlist yang dihasilkan AI otomatis tersimpan di folder `wordlists/` berdasarkan domain target. Scan berikutnya ke target yang sama akan otomatis menggabungkan wordlist lama dengan hasil AI baru (tanpa duplikat).

```bash
# Scan pertama → AI generate wordlist → simpan ke wordlists/target.com.txt
python3 ffufai.py --wordlists -u https://target.com/FUZZ -mc all -c

# Scan kedua → AI generate baru → merge dengan yang tersimpan → simpan → fuzzing
python3 ffufai.py --wordlists -u https://target.com/FUZZ -mc all -c
```

Struktur folder:
```
wordlists/
  target.com.txt          # wordlist gabungan (saved + AI)
  shop.example.com.txt
```

> Folder `wordlists/` sudah masuk `.gitignore` jadi tidak akan ter-push ke repository.

**Merge dengan Wordlist External:**

Gunakan `--merge` untuk menggabungkan saved wordlist dengan file wordlist external seperti SecLists:

```bash
python3 ffufai.py --wordlists --merge /usr/share/seclists/Discovery/Web-Content/common.txt -u https://target.com/FUZZ -mc all -c
```

Hasilnya: AI words + saved words + SecLists → digabung tanpa duplikat → disimpan ke `wordlists/target.com.txt` → langsung fuzzing.

### Mode 2: AI Extension Suggestion

**Kapan dipakai:** Kamu sudah punya wordlist sendiri dan ingin AI menyarankan extension file yang relevan (misal `.php`, `.bak`, `.json`) untuk fuzzing yang lebih lengkap.

**Cara kerja:** AI menganalisis URL + headers target, lalu menyarankan extension yang paling mungkin ada di server. Extension ini otomatis ditambahkan ke setiap kata di wordlist kamu saat fuzzing.

```bash
python3 ffufai.py -u https://target.com/FUZZ -w wordlist.txt -mc all -c
```

**Contoh nyata:**

```bash
python3 ffufai.py -u https://target.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt -mc all -c
```

Output yang muncul:
```
{'extensions': ['.json', '.js', '.bak', '.sql']}

        /'___\  /'___\           /'___\
       /\ \__/ /\ \__/  __  __  /\ \__/
       ...
________________________________________________

 :: URL              : https://target.com/FUZZ
 :: Wordlist         : FUZZ: /usr/share/seclists/Discovery/Web-Content/common.txt
 :: Extensions       : .json,.js,.bak,.sql
________________________________________________
...hasil fuzzing...
```

AI mendeteksi bahwa extension `.json`, `.js`, `.bak`, `.sql` paling relevan untuk target ini. ffuf otomatis fuzzing setiap kata di wordlist + keempat extension tersebut.

**Tambah jumlah extension:**

```bash
python3 ffufai.py --max-extensions 8 -u https://target.com/FUZZ -w wordlist.txt -mc all -c
```

### Tips: Target SPA (React, Vue, dll)

Jika target adalah Single Page Application, semua path biasanya mengembalikan status 200 dengan ukuran yang sama. Gunakan `-fs` untuk memfilter:

```bash
# -fs 10018 artinya: filter response yang ukurannya 10018 bytes (SPA catch-all)
python3 ffufai.py --wordlists -u https://target.com/FUZZ -mc all -fs 10018 -c
```

Cara mengetahui size yang harus difilter: jalankan tanpa `-fs` dulu, lihat size yang berulang-ulang, lalu tambahkan `-fs <size>`.

---

## Contoh Penggunaan Lengkap

> Jika sudah buat file `.env`, tidak perlu `--api-key` lagi. Langsung jalankan perintah di bawah.

```bash
# === AI Wordlist Generation (tidak perlu wordlist file) ===

# AI bikin wordlist, langsung fuzzing
python3 ffufai.py --wordlists -u https://target.com/FUZZ -mc all -c

# Wordlist lebih banyak (100 entry)
python3 ffufai.py --wordlists --max-wordlist-size 100 -u https://target.com/FUZZ -mc all -c

# AI baca konten halaman untuk wordlist lebih akurat
python3 ffufai.py --wordlists --include-response -u https://target.com/FUZZ -mc all -c

# Fuzzing subdirectory
python3 ffufai.py --wordlists -u https://target.com/static/js/FUZZ -mc all -c

# Target SPA, filter response size
python3 ffufai.py --wordlists -u https://target.com/FUZZ -mc all -fs 10018 -c

# Merge AI wordlist dengan SecLists
python3 ffufai.py --wordlists --merge /usr/share/seclists/Discovery/Web-Content/common.txt -u https://target.com/FUZZ -mc all -c

# === AI Extension Suggestion (butuh wordlist file) ===

# AI sarankan extension, fuzzing dengan wordlist kamu
python3 ffufai.py -u https://target.com/FUZZ -w wordlist.txt -mc all -c

# Lebih banyak extension
python3 ffufai.py --max-extensions 8 -u https://target.com/FUZZ -w wordlist.txt -mc all -c

# === Lainnya ===

# API key via CLI (kalau belum buat .env)
python3 ffufai.py --api-key 'key-kamu' --api-base-url 'https://api.z.ai/api/anthropic' --wordlists -u https://target.com/FUZZ -mc all -c

# ffuf di lokasi custom
python3 ffufai.py --ffuf-path /home/user/go/bin/ffuf --wordlists -u https://target.com/FUZZ -mc all -c
```

---

## Daftar Parameter

### Parameter ffufai

| Parameter | Default | Deskripsi |
|---|---|---|
| `--api-key` | - | API key langsung via CLI (Anthropic, OpenAI, atau z.ai) |
| `--api-base-url` | - | API base URL (wajib untuk z.ai) |
| `--api-type` | auto-detect | Pilih provider: `openai`, `anthropic`, atau `zai` |
| `--ffuf-path` | `ffuf` | Path ke binary ffuf |
| `--max-extensions` | `4` | Jumlah maksimum extension yang disarankan AI |
| `--wordlists` | - | Aktifkan mode wordlist generation |
| `--max-wordlist-size` | `200` | Ukuran maks wordlist yang dihasilkan AI |
| `--include-response` | - | Sertakan response body sebagai konteks untuk AI |
| `--merge` | - | Gabung saved wordlist dengan file wordlist external (misal SecLists) |

### Parameter ffuf yang Sering Dipakai

| Parameter | Deskripsi | Contoh |
|---|---|---|
| `-u` | Target URL, wajib mengandung `FUZZ` | `-u https://target.com/FUZZ` |
| `-w` | Path ke file wordlist | `-w wordlist.txt` |
| `-mc` | Match HTTP status code | `-mc all` atau `-mc 200,301` |
| `-fc` | Filter (buang) HTTP status code | `-fc 404` |
| `-fs` | Filter berdasarkan response size | `-fs 10018` |
| `-c` | Output berwarna | `-c` |
| `-v` | Verbose output (tampilkan full URL) | `-v` |
| `-t` | Jumlah thread (default: 40) | `-t 100` |
| `-o` | Simpan output ke file | `-o hasil.json` |
| `-r` | Follow redirects | `-r` |

Semua parameter ffuf lainnya bisa dipakai seperti biasa. Lihat `ffuf -h` untuk daftar lengkap.

---

## Prioritas API Key

1. **CLI arguments** (`--api-key`) - prioritas tertinggi
2. **`.env` file** - otomatis dibaca dari folder script
3. **Environment variable** - `export` di terminal

Jika ada beberapa API key tersedia, tool memakai prioritas berikut untuk provider:

1. **z.ai** (`ANTHROPIC_AUTH_TOKEN` + `ANTHROPIC_BASE_URL`) - diprioritaskan
2. **Anthropic** (`ANTHROPIC_API_KEY`)
3. **OpenAI** (`OPENAI_API_KEY`)

---

## Troubleshooting

| Masalah | Solusi |
|---|---|
| `command not found: ffuf` | Install ffuf (Langkah 3) atau gunakan `--ffuf-path /path/ke/ffuf` |
| `command not found: python3` | Install Python 3 (Langkah 1) |
| `No module named 'openai'` | Jalankan `pip install requests openai anthropic beautifulsoup4` |
| `No API key found` | Buat file `.env`, gunakan `--api-key`, atau set environment variable (Langkah 6) |
| `Error parsing AI response` | Response AI tidak valid, coba jalankan ulang |
| `Too many redirects` | Tool sudah menangani otomatis. Pastikan URL target benar |
| Semua response 200 size sama | Target adalah SPA. Tambahkan `-fs <size>` untuk filter |
| `stat wordlist.txt: no such file` | File wordlist tidak ada. Gunakan mode `--wordlists` atau tentukan path yang benar |

---

## Perubahan dari ffufai Original

- Dukungan **z.ai** via `ANTHROPIC_AUTH_TOKEN` + `ANTHROPIC_BASE_URL`
- Input API key langsung via CLI: `--api-key`, `--api-base-url`, `--api-type`
- `parse_json_response()` - menangani response AI yang dibungkus markdown code block
- `create_anthropic_client()` - mendukung custom base URL untuk provider non-OpenAI
- Fix redirect loop pada `get_headers()` dengan timeout dan fallback
- Custom model via environment variable `ZAI_MODEL`

## Credits

- [ffufai](https://github.com/jthack/ffufai) by jthack - project original
- [ffuf](https://github.com/ffuf/ffuf) - web fuzzer
- zlz (Sam Curry) - ide awal pembuatan ffufai

## License

This project is licensed under the MIT License - see the LICENSE file for details.
