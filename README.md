# Satu Muatan

Perkakas operasional bagi koperasi desa untuk menggabungkan panen beberapa petani
kecil menjadi satu muatan penuh, mengirimkannya ke pembeli institusional lewat
vendor logistik yang sudah ada, dan menyerahkannya dengan bukti mutu yang
menentukan pembayaran.

**Framing produk: efisiensi logistik + transparansi mutu.**

> Karya lomba Software Development Competition — IT Festival 2026, Sekolah Vokasi IPB.
> Subtema: Smart Agroindustry and Logistic System.

## URL Produksi

- Aplikasi (Vercel): _[diisi setelah deploy — target 3 Agustus]_
- API (Render): _[diisi setelah deploy — target 3 Agustus]_

**Wajib diuji dari jaringan seluler** (bukan wifi rumah/kampus) sebelum tanggal
di atas — lihat langkah 5 di bagian [Deploy](#deploy) di bawah.

## Kredensial Demo

Login memakai nomor HP + PIN 6 digit, atau tombol **Masuk cepat (demo)** di
layar Masuk (4 tombol utama sesuai spec §9.1: Koperasi, Petani, dan Penerima —
lihat catatan di bawah tabel untuk Dedi/Ijah).

| Peran | Nama | No. HP | PIN |
|---|---|---|---|
| Pengurus Koperasi | Bu Nia | `081200000001` | `123456` |
| Petani | Asep | `081200000011` | `123456` |
| Petani | Wati | `081200000012` | `123456` |
| Petani | Dedi | `081200000013` | `123456` |
| Petani | Ijah | `081200000014` | `123456` |
| Kepala Dapur SPPG Cibiru 3 | Bu Rina | `081200000021` | `123456` |

Catatan: tombol **Masuk cepat (demo)** menyediakan 4 peran utama (Koperasi,
Petani Asep, Petani Wati, Penerima). Dedi dan Ijah (langkah 5–6 skenario di
bawah) masuk lewat nomor HP + PIN di atas secara manual. Dua petani tambahan
di data seed (Ujang `081200000015`, Euis `081200000016`, PIN sama) tidak
dipakai di skenario demo utama — muncul di riwayat 8 slot lama untuk mengisi
grafik Dashboard Dampak.

## Skenario Demo (±10 menit, spec §11.2)

**Reset ke keadaan awal** sebelum mulai (aman dijalankan berkali-kali,
idempoten): tombol reset di aplikasi (mode demo) memanggil `POST
/api/demo/reset`, atau langsung di server: `python backend/seed/skenario_demo.py`
— mencetak cheat-sheet lengkap dengan angka yang dihitung ULANG saat itu juga
oleh mesin harga sungguhan (bukan angka yang ditulis manual di dokumen ini).

Rute demo (gudang koperasi → SPPG Panyileukan 2 → SPPG Ujungberung 1 → SPPG
Cibiru 3, nearest-neighbor): **70,03 km**. Ambang transit rute ini: **181
menit**. Angka di bawah adalah hasil mesin harga sungguhan pada rute ini
(diverifikasi cocok persis dengan KEPUTUSAN.md K2).

1. Login sebagai **Kepala Dapur SPPG Cibiru 3** (Bu Rina) → input permintaan
   300 kg Kubis, untuk besok.
2. Login sebagai **Pengurus Koperasi** (Bu Nia) → buka slot, pilih 3 tujuan
   (Cibiru 3, Ujungberung 1, Panyileukan 2) → tampil: jarak **70,03 km**,
   pratinjau harga kalau 300 kg = **Rp1.007/kg**.
3. Login sebagai **Petani Asep** → ikut kirim 300 kg Kubis
   → **HARGA ATAP TERKUNCI Rp1.007/kg**.
4. **Petani Wati** ikut +200 kg (kumulatif 500 kg) → harga berjalan turun ke
   **Rp605/kg** *[animasi]*.
5. **Petani Dedi** ikut +180 kg (kumulatif 680 kg) → turun ke **Rp445/kg**
   *[animasi]*.
6. **Petani Ijah** ikut +100 kg (kumulatif 780 kg) → turun ke **Rp388/kg**
   *[animasi]*
   → Layar Asep menunjukkan: **"Kamu hemat Rp619/kg → Rp185.700"**.
7. Koperasi tutup slot → sistem memilih **VAN** untuk 780 kg total (biaya
   total Rp302.077, harga final Rp388/kg).
8. Muat: timbang 4 lot, foto, satu lot ditandai **"ada cacat terlihat"**.
9. Lacak: majukan status pengiriman sampai **TIBA**.
10. Serah terima: 3 lot **TERIMA**, 1 lot **POTONG 20%** → atribusi
    **PETANI** (cacat sudah terlihat sejak muat, sebelum berangkat).
11. Buka **Berita Acara** → cetak (`window.print()` ke PDF).
12. Buka **Dashboard Dampak** → 4 kartu terisi (data dari 8 slot riwayat +
    slot demo yang baru selesai — grafik bulanan tidak kosong).
13. Buka **Panel Asumsi** → ubah faktor emisi → tunjukkan Dashboard Dampak
    ikut berubah.

## Arsitektur Singkat

```
frontend/   React 18 + Vite + TS + Tailwind (PWA, mobile-first 360px)
backend/    FastAPI + SQLAlchemy 2 + Alembic (Python)
kontrak/    openapi.yaml + types.ts + skema.sql  ← kontrak beku antar-modul
            Postgres 16 (lokal: docker-compose; produksi: Postgres terkelola)
```

- **Mesin harga** (`backend/app/domain/`): fungsi murni; mencari kombinasi
  kendaraan berbiaya total terendah, mengunci **harga atap** per petani saat
  bergabung, dan menghitung harga final + kembalian saat cutoff. Petani tidak
  pernah ditagih di atas atapnya.
- **Mesin atribusi**: keputusan mutu (PETANI / LOGISTIK / TIDAK_TERBUKTI)
  dari bukti muat + waktu tempuh vs ambang — selalu dengan penjelasan.
- **Vendor logistik** lewat pola adapter: `MOCK` (demo, deterministik, tarif
  publik) / `DELIVEREE` (kerangka, menunggu kredensial).
- **Panel Asumsi**: semua koefisien bisnis hidup di tabel `konfigurasi` +
  `tier_kendaraan` dengan badge TERVERIFIKASI/ASUMSI — tidak ada angka
  bisnis hardcoded di kode.

## Menjalankan Lokal

```bash
# database
docker compose up -d

# backend  (Python 3.12+; venv di backend/.venv)
cd backend
pip install -r requirements.txt
alembic upgrade head
python seed/seed.py              # master data + 8 slot riwayat (idempoten)
python seed/skenario_demo.py     # reset ke keadaan awal demo + cetak cheat-sheet
uvicorn app.main:app --reload --port 8100      # http://127.0.0.1:8100/docs

# frontend
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

Konfigurasi lewat env — salin `backend/.env.example` ke `backend/.env`.

## Deploy

Tiga bagian (spec §3.3): database Postgres terkelola (Neon), backend Docker
(Render — Railway sebagai alternatif), frontend statis (Vercel). Tidak ada
Docker Compose di produksi — hanya dipakai untuk Postgres lokal.

### 1. Database — Neon (Postgres, region Singapore)

1. Buka [neon.tech](https://neon.tech) → daftar/masuk (SSO GitHub tercepat).
2. **New Project** → nama `satu-muatan` → **Region: Singapore**
   (`ap-southeast-1`) → biarkan versi Postgres default → **Create**.
3. Di dashboard project, buka **Connection Details** → salin
   **Connection string** (bentuknya
   `postgresql://user:pass@host/dbname?sslmode=require`).
4. **Penting**: ganti awalan `postgresql://` menjadi `postgresql+psycopg://`
   (backend memakai driver `psycopg`, bukan `psycopg2` bawaan kebanyakan
   contoh) — inilah nilai `DATABASE_URL` untuk langkah berikutnya.

### 2. Backend — Render (Blueprint dari `render.yaml`)

1. Push branch/kode ini ke GitHub (repo berisi `render.yaml` di root).
2. Buka [dashboard.render.com](https://dashboard.render.com) → **New** →
   **Blueprint**.
3. Hubungkan akun GitHub → pilih repo ini. Render membaca `render.yaml` dan
   menampilkan rencana service `satu-muatan-api`.
4. Saat diminta mengisi env var yang ditandai rahasia (`sync: false` di
   `render.yaml`):
   - `DATABASE_URL` → tempel connection string Neon dari langkah 1.4.
   - `CORS_ORIGINS` → isi sementara `http://localhost:5173` (akan diperbarui
     di langkah 4 setelah URL Vercel ada).
   - `JWT_SECRET` **tidak perlu diisi** — Render membuatnya otomatis
     (`generateValue: true`).
5. **Apply** / **Create New Resources** → tunggu build image Docker selesai
   (±2–3 menit, bisa dipantau di tab **Logs**; cari baris
   `[entrypoint] alembic upgrade head...` lalu `Uvicorn running on...`).
6. Setelah status **Live**, catat URL backend (mis.
   `https://satu-muatan-api.onrender.com`). Verifikasi:
   `curl https://satu-muatan-api.onrender.com/healthz` → harus
   `{"status":"ok"}`.
7. **Seed data (sekali, manual)** — migrasi jalan otomatis tiap start
   container, tapi seed TIDAK: buka tab **Shell** di service Render (atau
   `render ssh`), lalu:
   ```bash
   cd backend
   python seed/seed.py
   python seed/skenario_demo.py
   ```

> **Alternatif Railway** (kalau kuota tier gratis Render habis): New Project →
> Deploy from GitHub repo → pilih repo ini → set **Root Directory**
> `backend` (Railway mendeteksi `Dockerfile` otomatis) → isi env var yang
> sama seperti tabel di `backend/.env.example` (`DATABASE_URL`, `JWT_SECRET`,
> `VENDOR_ADAPTER`, `DEMO_MODE`, `CORS_ORIGINS`) lewat tab **Variables** →
> Railway menyuntikkan `PORT` otomatis sama seperti Render. Jalankan seed
> lewat `railway run python seed/seed.py` dari CLI (atau tab **Shell** kalau
> tersedia di paket yang dipakai).

### 3. Frontend — Vercel

1. Buka [vercel.com](https://vercel.com) → **Add New** → **Project**.
2. **Import** repo GitHub yang sama.
3. **Root Directory** → klik **Edit** → pilih `frontend` (monorepo — jangan
   biarkan default root repo; `frontend/vercel.json` mengatur build & rewrite
   SPA-nya).
4. Framework Preset **Vite** biasanya terdeteksi otomatis lewat
   `frontend/vercel.json` (`buildCommand: npm run build`,
   `outputDirectory: dist`).
5. **Environment Variables** → tambah:
   - `VITE_API_URL` = URL backend Render dari langkah 2.6, **tanpa** trailing
     slash (mis. `https://satu-muatan-api.onrender.com`). Dibaca oleh
     `frontend/src/api/client.ts` sebagai `BASE_URL`; path panggilan API
     sudah membawa prefix `/api/...` sendiri.
6. **Deploy** → tunggu build selesai (±1–2 menit).
7. Catat URL Vercel (mis. `https://satu-muatan.vercel.app`).

### 4. Hubungkan balik — `CORS_ORIGINS`

1. Kembali ke Render dashboard → service `satu-muatan-api` → tab
   **Environment**.
2. Update `CORS_ORIGINS` → `https://satu-muatan.vercel.app,http://localhost:5173`
   (dipisah koma, tanpa spasi, tanpa trailing slash; **jangan pernah** `*` di
   produksi — spec §3.3).
3. **Save Changes** → Render otomatis redeploy service (±1 menit, tidak perlu
   build ulang Docker karena env var saja yang berubah).

### 5. Verifikasi dari jaringan seluler (wajib, spec §3.3 & §14)

1. Matikan wifi di HP, pakai data seluler.
2. Buka URL Vercel dari langkah 3.7 di browser HP.
3. **Masuk cepat (demo)** salah satu peran → pastikan layar Beranda memuat
   data (ini sekaligus bukti CORS & koneksi backend berjalan dari luar
   jaringan kantor/kampus).
4. Jalankan skenario §11.2 minimal sampai Detail Slot (langkah 1–6) untuk
   memastikan animasi harga berjalan mulus di koneksi seluler.
5. Catat kedua URL (frontend + backend) di bagian
   [URL Produksi](#url-produksi) di atas.
