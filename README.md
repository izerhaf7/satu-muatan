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
| Petugas Satu Muatan | Bu Nia | `081200000001` | `123456` |
| Petani | Asep | `081200000011` | `123456` |
| Petani | Wati | `081200000012` | `123456` |
| Petani | Dedi | `081200000013` | `123456` |
| Petani | Ijah | `081200000014` | `123456` |
| Kepala Dapur Katering Cibiru | Bu Rina | `081200000021` | `123456` |

Catatan: **petugas adalah driver Satu Muatan** (K13/K14) — dia menjemput panen
ke lokasi masing-masing petani, memeriksa & memfoto, memberi grade mutu, lalu
mengantarkannya. Dia BUKAN pengirim: menu Kirim Panen tidak ada di perannya.
Muatan tidak ditugaskan otomatis kepadanya — muatan menunggu di **papan tugas**
dan diambil sendiri, satu muatan aktif dalam satu waktu.

Ijah masuk manual via nomor HP + PIN (tidak ada tombol cepatnya). Dua petani
tambahan di data seed (Ujang `081200000015`, Euis `081200000016`, PIN sama)
muncul di riwayat 8 slot lama untuk mengisi grafik Dashboard Dampak.

## Skenario Demo (±8 menit, spec v2 §8.2)

**Reset ke keadaan awal** sebelum mulai (aman dijalankan berkali-kali,
idempoten): tombol reset di aplikasi (mode demo) memanggil `POST
/api/demo/reset`, atau langsung di server: `python backend/seed/skenario_demo.py`
— mencetak cheat-sheet lengkap dengan angka yang dihitung ULANG saat itu juga
oleh mesin harga sungguhan (bukan angka yang ditulis manual di dokumen ini).

1. Login sebagai **Petani Asep** → **Kirim Panen** → tandai titik **penjemputan**
   (tombol "Gunakan lokasi saya" atau ketuk peta) — alamatnya terbaca otomatis,
   dan mengetik nama desa memunculkan **autocomplete daerah**. Lalu tandai
   **tujuan** dengan cara yang sama. Volume di bawah **50 kg ditolak di layar**,
   bukan setelah dikirim.
2. Tekan **Kirim** → sistem membuka muatan baru → Asep melihat **harga atap**
   terkunci di layar Muatanmu.
3. Login sebagai **Petani Wati** → kirim dari kebunnya sendiri, tujuan berdekatan
   → sistem mencocokkan ke **muatan yang SAMA** → harga berjalan turun. Kiriman
   yang justru akan MENAIKKAN harga grup membuka muatannya sendiri, bukan
   ditolak buntu.
4. **Petani Dedi** & **Ijah** menyusul → harga turun lagi → atap tiap petani
   tetap di angka saat dia bergabung.
5. Login sebagai **Petugas** → **Beranda**: muatan menunggu di **papan tugas**.
   Tekan **Ambil tugas ini**. Mencoba mengambil muatan kedua → ditolak.
6. Buka **Muat** → **rute penjemputan berurutan** tampil: nomor, nama petani,
   alamat lengkap, jarak tiap segmen, tombol arah jalan. Timbang tiap lot —
   **foto muat wajib**, tombol simpan terkunci tanpa foto.
7. **Selesai muat** → berangkat → **Lacak**: tekan "Majukan posisi" atau nyalakan
   "Jalan otomatis" — peta benar-benar bergerak sepanjang rute. Grafik suhu
   berlabel "Data simulasi — sensor fisik menyusul".
8. Login sebagai **Penerima** → **Lacak Resi** → masukkan nomor resi → timeline,
   peta, grafik suhu, dan **INDEKS MUTU** tampil **sebelum** memutuskan.
   Pilihannya hanya **Terima** atau **Tolak**; tombol Tolak baru muncul kalau
   penurunan mutu terukur melewati ambang 50%. Tidak ada potongan harga.
9. **Serah Terima** → atribusi PETANI / LOGISTIK / TIDAK_TERBUKTI / NORMAL
   dengan **kalimat penjelasan**.
10. Kembali sebagai petani → **Riwayat**: tiap baris bisa **diklik**, dengan
    tautan **Lacak** dan **Berita Acara** → cetak (`window.print()` ke PDF).
11. **Dashboard Dampak** → empat kartu semboyan terisi. **Panel Asumsi** → ubah
    faktor emisi → kartu emisi ikut berubah.

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
- **Rute dua tahap** (`backend/app/domain/rute.py`): titik kumpul → semua lokasi
  **penjemputan** → semua tujuan, keduanya nearest-neighbor. `jarak_km` (dasar
  harga) menghitung kedua tahap.
- **Indeks mutu** (`backend/app/domain/mutu.py`): rata-rata tertimbang sisa umur
  simpan (Q10) dan ketepatan waktu tempuh — ditampilkan ke penerima **sebelum**
  dia memutuskan terima/tolak. Murni dari data terpantau; grade tiba sengaja
  tidak ikut supaya penerima tidak bisa menggerakkan angkanya sendiri.
- **Alamat & wilayah**: tabel `wilayah` di-seed dari berkas JSON di repo
  (6.612 baris Jawa Barat, data Kemendagri via [wilayah.id](https://wilayah.id/),
  diunduh sekali oleh `backend/seed/unduh_wilayah.py`). Autocomplete jalan
  **tanpa internet**. Reverse geocoding lewat proxy backend
  (`GET /api/geokode/balik`): memakai Google Geocoding kalau
  `GOOGLE_MAPS_API_KEY` diisi, kalau tidak jatuh ke wilayah terdekat dari tabel
  sendiri. **Kunci API tidak pernah masuk browser**, dan demo tetap jalan kalau
  jaringan bermasalah.
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

### Cloud Run (jalur paralel, tanpa traffic awal)

Render tetap jalur rollback. `backend/docker-entrypoint.sh` mempertahankan
`RUN_MIGRATIONS=true` secara default, jadi perilaku Render/Railway tidak berubah.
Cloud Run runtime harus memakai `RUN_MIGRATIONS=false`; `scripts/deploy-cloud-run.ps1`
lebih dulu membuat/menjalankan migration job serial (`tasks=1`, `parallelism=1`,
`max-retries=0`) dengan `alembic upgrade head`, lalu membuat revision service
tanpa traffic. Semua nilai runtime rahasia tetap berada di Secret Manager dan
tidak boleh disimpan di argumen, log, `.env`, atau repository.

Cloud Build memakai `cloudbuild.yaml` dan tag image immutable `${COMMIT_SHA}`.
Jalankan script hanya setelah resource Phase 2 tersedia; Task 2 ini tidak
membuat resource maupun mengirim traffic. Parameter `DatabaseUrlSecret` dan
`JwtSecret` adalah **nama** secret, bukan nilainya.

Kill switch Cloud Run: arahkan traffic ke revision sebelumnya; bila perlu
nonaktifkan revision terbaru; bila provider geo aktif nanti, nonaktifkan kunci
provider di Secret Manager. Jangan hapus Render sampai health, auth, CORS, dan
log Cloud Run tervalidasi.

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

