# Satu Muatan

Layanan *groupage* untuk pengirim hasil tani skala kecil. Beberapa petani yang
tidak saling kenal berbagi satu truk ke koridor yang sama, dengan harga yang
dijamin tidak pernah naik dan bukti perjalanan yang menentukan tanggung jawab
kalau mutu turun.

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
layar Masuk (4 tombol: Petugas Asep, Petani Wati, Petani Dedi, Penerima).

| Peran | Nama | No. HP | PIN |
|---|---|---|---|
| Petugas Titik Kumpul | Asep | `081200000011` | `123456` |
| Petani | Bu Nia | `081200000001` | `123456` |
| Petani | Wati | `081200000012` | `123456` |
| Petani | Dedi | `081200000013` | `123456` |
| Petani | Ijah | `081200000014` | `123456` |
| Kepala Dapur Katering Cibiru | Bu Rina | `081200000021` | `123456` |

Catatan: **Asep adalah petani yang ditunjuk sebagai petugas** di Titik Kumpul
Pak Asep — dia yang menimbang, memfoto, dan memberi grade mutu (bukan pegawai
platform, bukan driver vendor). Ijah masuk manual via nomor HP + PIN (tidak ada
tombol cepatnya). Dua petani tambahan di data seed (Ujang `081200000015`,
Euis `081200000016`, PIN sama) muncul di riwayat 8 slot lama untuk mengisi
grafik Dashboard Dampak.

## Skenario Demo (±8 menit, spec v2 §8.2)

**Reset ke keadaan awal** sebelum mulai (aman dijalankan berkali-kali,
idempoten): tombol reset di aplikasi (mode demo) memanggil `POST
/api/demo/reset`, atau langsung di server: `python backend/seed/skenario_demo.py`
— mencetak cheat-sheet lengkap dengan angka yang dihitung ULANG saat itu juga
oleh mesin harga sungguhan (bukan angka yang ditulis manual di dokumen ini).

1. Login sebagai **Petani Asep** → buka **Kirim Panen** → tujuan Dapur Katering
   Cibiru, sawi 300 kg, besok → tampil **harga atap** dan **potensi penghematan**
   sebelum berkomitmen.
2. Tekan **Kirim** → sistem membuka muatan baru → Asep diarahkan ke layar
   **Muatanmu** (Detail Slot).
3. Login sebagai **Petani Wati** → kirim 200 kg, tujuan 8 km dari tujuan Asep
   → sistem mencocokkan ke **muatan yang SAMA** (radius koridor 15 km)
   → harga berjalan turun *[animasi]*.
4. **Petani Dedi** +180 kg, **Petani Ijah** +100 kg → harga turun lagi *[animasi]*
   → Layar Asep: atap terkunci, harga sekarang, dan total hematnya.
5. Login sebagai **Petugas (Asep)** → **Muat**: timbang 4 lot, foto, grade mutu
   — 3 lot **"Sangat baik"**, 1 lot **"Cukup"**.
6. Berangkat → **Lacak**: grafik suhu naik siang hari (berlabel "Data simulasi
   — sensor fisik menyusul"), kartu suhu maks & **sisa umur simpan** sawi.
7. Tiba → **Serah Terima**: 3 lot **Terima**, 1 lot **Potong 20%** → atribusi
   **PETANI** dengan **kalimat penjelasan** (grade asal di bawah standar).
8. Buka **Berita Acara** → cetak (`window.print()` ke PDF).
9. Buka **Dashboard Dampak** → **empat kartu semboyan** terisi: Menekan biaya
   logistik · Menurunkan emisi · Transparansi perjalanan · Keamanan pangan.
10. Buka **Panel Asumsi** → ubah faktor emisi → kartu emisi ikut berubah.

## Arsitektur Singkat

```
frontend/   React 18 + Vite + TS + Tailwind (PWA, mobile-first 360px, responsif desktop)
backend/    FastAPI + SQLAlchemy 2 + Alembic (Python)
kontrak/    openapi.yaml + types.ts + skema.sql  ← kontrak beku antar-modul
            Postgres 16 (lokal: docker-compose; produksi: Postgres terkelola)
```

- **Pencocokan otomatis** (`backend/app/domain/pencocokan.py`): petani tidak
  memilih slot — kiriman dicocokkan greedy ke muatan berdasarkan radius koridor
  + jendela tanggal, dipecah saat kelebihan kapasitas armada.
- **Mesin harga** (`backend/app/domain/harga.py`): fungsi murni; mengunci
  **harga atap** per petani saat bergabung (tidak pernah naik), harga final +
  kembalian saat cutoff.
- **Mesin atribusi 3-input**: grade asal × grade tiba × bukti paparan (transit
  vs ambang, sisa umur simpan model Q10) → PETANI / LOGISTIK / TIDAK_TERBUKTI /
  NORMAL — selalu dengan kalimat penjelasan.
- **Telemetri** (`backend/app/services/telemetri.py`): kurva suhu harian
  deterministik, berlabel "Data simulasi" di UI.
- **Vendor logistik** lewat pola adapter: `MOCK` (demo, deterministik) /
  `DELIVEREE` (kerangka).
- **Panel Asumsi**: semua koefisien bisnis hidup di tabel `konfigurasi` +
  `tier_kendaraan` dengan badge TERVERIFIKASI/ASUMSI — tidak ada angka bisnis
  hardcoded di kode.

## Menjalankan Lokal

```bash
# database
docker compose up -d

# backend  (Python 3.12+; venv di backend/.venv)
cd backend
pip install -r requirements.txt
alembic upgrade head
python seed/seed.py              # master data + 8 slot riwayat + telemetri (idempoten)
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
4. Jalankan skenario demo §8.2 minimal sampai **Muatanmu** (langkah 1–2) untuk
   memastikan animasi harga berjalan mulus di koneksi seluler.
5. Catat kedua URL (frontend + backend) di bagian
   [URL Produksi](#url-produksi) di atas.

