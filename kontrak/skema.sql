-- REFERENSI BACAAN. Sumber kebenaran skema = migrasi Alembic (backend/alembic/).
-- Digenerate dari metadata SQLAlchemy oleh scripts/ekspor_kontrak.py.

CREATE TABLE komoditas (
	id UUID NOT NULL, 
	nama TEXT NOT NULL, 
	satuan TEXT DEFAULT 'kg' NOT NULL, 
	harga_acuan_per_kg INTEGER NOT NULL, 
	umur_simpan_jam INTEGER NOT NULL, 
	laju_susut_per_jam NUMERIC(6, 5) NOT NULL, 
	status_sumber status_sumber NOT NULL, 
	catatan_sumber TEXT, 
	PRIMARY KEY (id)
);

CREATE TABLE konfigurasi (
	kunci TEXT NOT NULL, 
	nilai TEXT NOT NULL, 
	tipe tipe_konfigurasi NOT NULL, 
	label TEXT NOT NULL, 
	satuan TEXT, 
	status_sumber status_sumber NOT NULL, 
	catatan_sumber TEXT, 
	PRIMARY KEY (kunci)
);

CREATE TABLE koperasi (
	id UUID NOT NULL, 
	nama TEXT NOT NULL, 
	kode TEXT, 
	desa TEXT, 
	kecamatan TEXT, 
	kabupaten TEXT, 
	alamat_gudang TEXT NOT NULL, 
	lat FLOAT NOT NULL, 
	lng FLOAT NOT NULL, 
	dibuat_pada TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (kode)
);

CREATE TABLE penerima (
	id UUID NOT NULL, 
	nama TEXT NOT NULL, 
	tipe tipe_penerima NOT NULL, 
	alamat TEXT NOT NULL, 
	lat FLOAT NOT NULL, 
	lng FLOAT NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE tier_kendaraan (
	id UUID NOT NULL, 
	kode TEXT NOT NULL, 
	nama TEXT NOT NULL, 
	kapasitas_kg INTEGER NOT NULL, 
	tarif_dasar INTEGER NOT NULL, 
	tarif_per_km INTEGER NOT NULL, 
	urutan INTEGER NOT NULL, 
	aktif BOOLEAN DEFAULT 'true' NOT NULL, 
	status_sumber status_sumber NOT NULL, 
	catatan_sumber TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (kode)
);

CREATE TABLE pengguna (
	id UUID NOT NULL, 
	nama TEXT NOT NULL, 
	no_hp TEXT NOT NULL, 
	pin_hash TEXT NOT NULL, 
	peran peran_pengguna NOT NULL, 
	koperasi_id UUID, 
	penerima_id UUID, 
	aktif BOOLEAN DEFAULT 'true' NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (no_hp), 
	FOREIGN KEY(koperasi_id) REFERENCES koperasi (id), 
	FOREIGN KEY(penerima_id) REFERENCES penerima (id)
);

CREATE TABLE slot (
	id UUID NOT NULL, 
	kode TEXT NOT NULL, 
	koperasi_id UUID NOT NULL, 
	tanggal_kirim DATE NOT NULL, 
	cutoff_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	status status_slot NOT NULL, 
	jarak_km NUMERIC(8, 2) NOT NULL, 
	tier_terpilih_id UUID, 
	jumlah_kendaraan INTEGER DEFAULT '1' NOT NULL, 
	rencana_json JSONB, 
	biaya_total INTEGER, 
	harga_final_per_kg INTEGER, 
	subsidi_koperasi INTEGER DEFAULT '0' NOT NULL, 
	volume_terkunci_kg INTEGER DEFAULT '0' NOT NULL, 
	dibuat_pada TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (kode), 
	FOREIGN KEY(koperasi_id) REFERENCES koperasi (id), 
	FOREIGN KEY(tier_terpilih_id) REFERENCES tier_kendaraan (id)
);

CREATE TABLE partisipasi (
	id UUID NOT NULL, 
	slot_id UUID NOT NULL, 
	petani_id UUID NOT NULL, 
	komoditas_id UUID NOT NULL, 
	volume_kg INTEGER NOT NULL, 
	harga_atap_per_kg INTEGER NOT NULL, 
	harga_final_per_kg INTEGER, 
	kembalian_rp INTEGER DEFAULT '0' NOT NULL, 
	status status_partisipasi NOT NULL, 
	bergabung_pada TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (slot_id, petani_id, komoditas_id), 
	FOREIGN KEY(slot_id) REFERENCES slot (id), 
	FOREIGN KEY(petani_id) REFERENCES pengguna (id), 
	FOREIGN KEY(komoditas_id) REFERENCES komoditas (id)
);

CREATE TABLE pengiriman (
	id UUID NOT NULL, 
	slot_id UUID NOT NULL, 
	vendor TEXT NOT NULL, 
	vendor_ref TEXT, 
	status_vendor TEXT, 
	waktu_berangkat TIMESTAMP WITH TIME ZONE, 
	waktu_tiba TIMESTAMP WITH TIME ZONE, 
	kuotasi_json JSONB, 
	dibuat_pada TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (slot_id), 
	FOREIGN KEY(slot_id) REFERENCES slot (id)
);

CREATE TABLE permintaan (
	id UUID NOT NULL, 
	penerima_id UUID NOT NULL, 
	komoditas_id UUID NOT NULL, 
	volume_kg INTEGER NOT NULL, 
	tanggal_dibutuhkan DATE NOT NULL, 
	status status_permintaan NOT NULL, 
	slot_id UUID, 
	volume_terpenuhi_kg INTEGER DEFAULT '0' NOT NULL, 
	dibuat_pada TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(penerima_id) REFERENCES penerima (id), 
	FOREIGN KEY(komoditas_id) REFERENCES komoditas (id), 
	FOREIGN KEY(slot_id) REFERENCES slot (id)
);

CREATE TABLE slot_tujuan (
	id UUID NOT NULL, 
	slot_id UUID NOT NULL, 
	penerima_id UUID NOT NULL, 
	urutan INTEGER NOT NULL, 
	jarak_segmen_km NUMERIC(8, 2) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (slot_id, urutan), 
	FOREIGN KEY(slot_id) REFERENCES slot (id), 
	FOREIGN KEY(penerima_id) REFERENCES penerima (id)
);

CREATE TABLE jejak_posisi (
	id UUID NOT NULL, 
	pengiriman_id UUID NOT NULL, 
	lat FLOAT, 
	lng FLOAT, 
	waktu TIMESTAMP WITH TIME ZONE NOT NULL, 
	sumber sumber_posisi NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(pengiriman_id) REFERENCES pengiriman (id)
);

CREATE TABLE lot (
	id UUID NOT NULL, 
	partisipasi_id UUID NOT NULL, 
	kode_qr TEXT NOT NULL, 
	penerima_id UUID, 
	berat_aktual_kg INTEGER, 
	foto_muat TEXT, 
	waktu_muat TIMESTAMP WITH TIME ZONE, 
	catatan_muat TEXT, 
	cacat_terlihat BOOLEAN DEFAULT 'false' NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(partisipasi_id) REFERENCES partisipasi (id), 
	UNIQUE (kode_qr), 
	FOREIGN KEY(penerima_id) REFERENCES penerima (id)
);

CREATE TABLE serah_terima (
	id UUID NOT NULL, 
	lot_id UUID NOT NULL, 
	penerima_id UUID NOT NULL, 
	waktu_bongkar TIMESTAMP WITH TIME ZONE NOT NULL, 
	foto_bongkar TEXT, 
	keputusan keputusan_serah_terima NOT NULL, 
	persen_potongan INTEGER DEFAULT '0' NOT NULL, 
	alasan TEXT, 
	durasi_transit_menit INTEGER NOT NULL, 
	ambang_transit_menit INTEGER NOT NULL, 
	atribusi atribusi NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (lot_id), 
	FOREIGN KEY(lot_id) REFERENCES lot (id), 
	FOREIGN KEY(penerima_id) REFERENCES penerima (id)
);
