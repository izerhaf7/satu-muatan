# Satu Muatan

Perkakas operasional bagi koperasi desa untuk menggabungkan panen beberapa petani
kecil menjadi satu muatan penuh, mengirimkannya ke pembeli institusional lewat
vendor logistik yang sudah ada, dan menyerahkannya dengan bukti mutu yang
menentukan pembayaran.

**Framing produk: efisiensi logistik + transparansi mutu.**

> Karya lomba Software Development Competition — IT Festival 2026, Sekolah Vokasi IPB.
> Subtema: Smart Agroindustry and Logistic System.

## URL Produksi

- Aplikasi: _(diisi saat deploy — target paling lambat 3 Agustus 2026)_
- API: _(diisi saat deploy)_

## Kredensial Demo

Login memakai nomor HP + PIN 6 digit, atau tombol **Masuk cepat (demo)**.

| Peran | Akun | PIN |
|---|---|---|
| Pengurus Koperasi | _(diisi saat seed demo)_ | 123456 |
| Petani | Asep · Wati · Dedi · Ijah | 123456 |
| Kepala Dapur SPPG | SPPG Cibiru 3 | 123456 |

## Skenario Demo (±10 menit)

_(diisi lengkap di Fase 3 — ringkas: permintaan dapur → buka slot → 4 petani ikut
kirim & harga berjalan turun → tutup slot → muat + QR → lacak → serah terima →
berita acara → dashboard dampak → panel asumsi)_

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
python seed/seed.py
uvicorn app.main:app --reload      # http://localhost:8000/docs

# frontend
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

Konfigurasi lewat env — salin `backend/.env.example` ke `backend/.env`.
