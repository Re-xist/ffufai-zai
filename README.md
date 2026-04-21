<div align="center">

# `ffufai-zai`

![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

<p align="center">

**ffufai-zai** adalah fork dari [ffufai](https://github.com/jthack/ffufai) dengan tambahan dukungan **z.ai API**. Tool ini adalah wrapper berbasis AI untuk web fuzzer [ffuf](https://github.com/ffuf/ffuf) yang secara otomatis menyarankan file extension atau wordlist untuk fuzzing berdasarkan analisis URL target dan HTTP headers menggunakan AI.

</p>

</div>

---

## Fitur

- Integrasi langsung dengan ffuf
- Dukungan **3 provider AI**: z.ai, Anthropic, dan OpenAI
- **Extension Suggestion** - AI menganalisis target dan menyarankan extension file yang relevan
- **Wordlist Generation** - AI membuat wordlist kontekstual berdasarkan teknologi dan konten target
- Semua parameter ffuf diteruskan langsung
- Menangani markdown code block wrapping dari response AI
- Handle redirect loop pada target yang menggunakan SPA

## Prerequisites

- Python 3.6+
- [ffuf](https://github.com/ffuf/ffuf) (terinstall dan bisa diakses di PATH)
- Salah satu API key: z.ai, Anthropic, atau OpenAI

## Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/Re-xist/ffufai-zai.git
cd ffufai-zai
```

### 2. Install Dependencies

```bash
pip install requests openai anthropic beautifulsoup4
```

### 3. Install ffuf

Menggunakan Go:
```bash
go install github.com/ffuf/ffuf/v2@latest
```

Atau download binary dari [ffuf releases](https://github.com/ffuf/ffuf/releases).

Pastikan ffuf bisa diakses:
```bash
ffuf -V
```

### 4. Setup API Key

Pilih salah satu provider:

#### Z.ai (Direkomendasikan untuk pengguna Indonesia)

```bash
export ANTHROPIC_AUTH_TOKEN='api-key-z-ai-kamu'
export ANTHROPIC_BASE_URL='https://api.z.ai/api/anthropic'
```

Dapatkan API key di: https://z.ai/manage-apikey/apikey-list

#### Anthropic (Claude)

```bash
export ANTHROPIC_API_KEY='api-key-anthropic-kamu'
```

#### OpenAI (GPT)

```bash
export OPENAI_API_KEY='api-key-openai-kamu'
```

Buat permanen dengan menambahkan ke `~/.bashrc` atau `~/.zshrc`:
```bash
echo 'export ANTHROPIC_AUTH_TOKEN="api-key-kamu"' >> ~/.bashrc
echo 'export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"' >> ~/.bashrc
source ~/.bashrc
```

### 5. (Opsional) Buat Symlink

```bash
sudo ln -s $(pwd)/ffufai.py /usr/local/bin/ffufai
```

## Cara Penggunaan

### Mode Extension Suggestion (Default)

AI menganalisis URL + headers target, lalu menyarankan file extension untuk fuzzing. Extension ditambahkan otomatis ke flag `-e` ffuf.

```bash
python3 ffufai.py -u https://target.com/FUZZ -w wordlist.txt
```

Contoh output:
```
{'extensions': ['.json', '.js', '.bak', '.zip']}
# ffuf akan dijalankan dengan -e .json,.js,.bak,.zip
```

### Mode Wordlist Generation

AI membuat wordlist kontekstual berdasarkan analisis teknologi dan konteks target. Tidak perlu menyediakan file wordlist.

```bash
python3 ffufai.py --wordlists -u https://target.com/FUZZ -mc all -c
```

Dengan ukuran wordlist custom (default: 200):
```bash
python3 ffufai.py --wordlists --max-wordlist-size 50 -u https://target.com/FUZZ -mc all -c
```

Dengan response body sebagai konteks tambahan (lebih akurat, lebih banyak token):
```bash
python3 ffufai.py --wordlists --include-response -u https://target.com/FUZZ -mc all -c
```

### Contoh Penggunaan Lengkap

```bash
# Fuzzing dengan extension suggestion dan wordlist file
python3 ffufai.py --max-extensions 6 -u https://target.com/FUZZ -w /path/to/wordlist.txt -mc all -c

# Fuzzing dengan AI-generated wordlist, filter SPA catch-all
python3 ffufai.py --wordlists --max-wordlist-size 100 -u https://target.com/api/FUZZ -mc all -fs 10018 -c

# Fuzzing ke subdirectory
python3 ffufai.py --wordlists -u https://target.com/static/js/FUZZ -mc all -c

# Menggunakan ffuf di path custom
python3 ffufai.py --ffuf-path /home/user/go/bin/ffuf -u https://target.com/FUZZ -w wordlist.txt
```

## Parameter

### Parameter Tambahan ffufai

| Parameter | Default | Deskripsi |
|---|---|---|
| `--ffuf-path` | `ffuf` | Path ke binary ffuf |
| `--max-extensions` | `4` | Jumlah maksimum extension yang disarankan AI |
| `--wordlists` | - | Aktifkan mode wordlist generation (AI buat wordlist) |
| `--max-wordlist-size` | `200` | Ukuran maks wordlist yang dihasilkan AI |
| `--include-response` | - | Sertakan response body sebagai konteks tambahan |

### Parameter ffuf yang Sering Dipakai

| Parameter | Deskripsi |
|---|---|
| `-u` | Target URL (wajib, harus mengandung `FUZZ`) |
| `-w` | Path ke file wordlist |
| `-mc` | Match HTTP status code (default: `200-299,301,302,307,401,403,405,500`) |
| `-fc` | Filter HTTP status code |
| `-fs` | Filter berdasarkan response size |
| `-c` | Output berwarna |
| `-v` | Verbose output |
| `-t` | Jumlah thread concurrent (default: 40) |

Semua parameter ffuf lainnya bisa dipakai seperti biasa.

## Prioritas API Key

Jika beberapa API key tersedia sekaligus, prioritasnya:

1. **z.ai** (`ANTHROPIC_AUTH_TOKEN` + `ANTHROPIC_BASE_URL`)
2. **Anthropic** (`ANTHROPIC_API_KEY`)
3. **OpenAI** (`OPENAI_API_KEY`)

## Perubahan dari ffufai Original

- Dukungan **z.ai** via `ANTHROPIC_AUTH_TOKEN` + `ANTHROPIC_BASE_URL`
- `parse_json_response()` - menangani response AI yang dibungkus markdown code block
- `create_anthropic_client()` - mendukung custom base URL untuk provider non-OpenAI
- Fix redirect loop pada `get_headers()` dengan timeout dan fallback
- Custom model via environment variable `ZAI_MODEL`

## Troubleshooting

| Masalah | Solusi |
|---|---|
| `command not found: ffuf` | Install ffuf atau gunakan `--ffuf-path` |
| `command not found: python3` | Install Python 3 |
| `No module named 'openai'` | Jalankan `pip install requests openai anthropic beautifulsoup4` |
| `No API key found` | Set environment variable API key (lihat [Setup API Key](#4-setup-api-key)) |
| `Error parsing AI response` | Response AI tidak valid, coba jalankan ulang |
| `Too many redirects` | Tool sudah menangani ini otomatis, tapi pastikan URL target benar |
| Semua response 200 size sama | Target adalah SPA, gunakan `-fs <size>` untuk filter catch-all |

## Credits

- [ffufai](https://github.com/jthack/ffufai) by jthack - project original
- [ffuf](https://github.com/ffuf/ffuf) - web fuzzer
- zlz (Sam Curry) - ide awal pembuatan ffufai

## License

This project is licensed under the MIT License - see the LICENSE file for details.
