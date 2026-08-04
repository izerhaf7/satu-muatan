"""v4 (K14) — alamat terstruktur, titik penjemputan, rute dua tahap, wilayah

Empat kelompok perubahan:

1. `kiriman` mendapat ALAMAT TERSTRUKTUR (nama, telepon, jalan, RT/RW, desa,
   kecamatan, kabupaten, provinsi, kode pos, patokan) untuk tujuan DAN asal.
   Satu baris teks bebas tidak cukup untuk logistik sungguhan; surat jalan pun
   mensyaratkan data pengirim & penerima yang lengkap.
2. `kiriman.lat_asal/lng_asal` — titik penjemputan. Sebelumnya asal kiriman
   tidak ada sama sekali: semua petani dianggap berangkat dari titik kumpul.
3. Tabel `slot_jemput` — perhentian penjemputan berurutan, sejajar dengan
   `slot_tujuan`. Rute muatan kini dua tahap: jemput dulu, baru antar.
4. Tabel `wilayah` (autocomplete alamat, di-seed dari berkas JSON di repo) dan
   `geokode_cache` (hasil reverse geocoding yang sudah pernah dicari).

Revision ID: c9a3f7d21b64
Revises: b7e4c19a2f85
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c9a3f7d21b64"
down_revision = "b7e4c19a2f85"
branch_labels = None
depends_on = None

_KOLOM_ALAMAT = ("jalan", "rt_rw", "desa", "kecamatan", "kabupaten", "provinsi", "kode_pos", "patokan")


def upgrade() -> None:
    # 1 & 2 — kiriman
    op.add_column("kiriman", sa.Column("nama_penerima", sa.Text(), nullable=True))
    op.add_column("kiriman", sa.Column("telepon_penerima", sa.Text(), nullable=True))
    for kolom in _KOLOM_ALAMAT:
        op.add_column("kiriman", sa.Column(f"{kolom}_tujuan", sa.Text(), nullable=True))

    op.add_column("kiriman", sa.Column("lat_asal", sa.Float(), nullable=True))
    op.add_column("kiriman", sa.Column("lng_asal", sa.Float(), nullable=True))
    op.add_column("kiriman", sa.Column("alamat_asal", sa.Text(), nullable=True))
    op.add_column("kiriman", sa.Column("telepon_pengirim", sa.Text(), nullable=True))
    for kolom in _KOLOM_ALAMAT:
        op.add_column("kiriman", sa.Column(f"{kolom}_asal", sa.Text(), nullable=True))

    op.add_column("penerima", sa.Column("telepon", sa.Text(), nullable=True))
    op.add_column("penerima", sa.Column("kode_pos", sa.Text(), nullable=True))

    # 3 — perhentian penjemputan
    op.create_table(
        "slot_jemput",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("slot.id"), nullable=False),
        sa.Column(
            "partisipasi_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partisipasi.id"), nullable=False
        ),
        sa.Column("urutan", sa.Integer(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("alamat", sa.Text(), nullable=False),
        sa.Column("jarak_segmen_km", sa.Numeric(8, 2), nullable=False),
        sa.UniqueConstraint("slot_id", "urutan", name="uq_slot_jemput_slot_id_urutan"),
    )

    # 4 — wilayah & cache geokode
    op.create_table(
        "wilayah",
        sa.Column("kode", sa.Text(), primary_key=True),
        sa.Column("nama", sa.Text(), nullable=False),
        sa.Column("tingkat", sa.Text(), nullable=False),
        sa.Column("induk_kode", sa.Text(), nullable=True, index=True),
        sa.Column("jalur", sa.Text(), nullable=False),
        sa.Column("kode_pos", sa.Text(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
    )
    # Autocomplete mengetik nama, bukan kode — indeksnya harus di nama.
    op.create_index("ix_wilayah_nama", "wilayah", ["nama"])
    op.create_index("ix_wilayah_tingkat", "wilayah", ["tingkat"])

    op.create_table(
        "geokode_cache",
        sa.Column("kunci", sa.Text(), primary_key=True),
        sa.Column("sumber", sa.Text(), nullable=False),
        sa.Column("hasil_json", sa.Text(), nullable=False),
        sa.Column("dibuat_pada", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("geokode_cache")
    op.drop_index("ix_wilayah_tingkat", table_name="wilayah")
    op.drop_index("ix_wilayah_nama", table_name="wilayah")
    op.drop_table("wilayah")
    op.drop_table("slot_jemput")

    op.drop_column("penerima", "kode_pos")
    op.drop_column("penerima", "telepon")

    for kolom in _KOLOM_ALAMAT:
        op.drop_column("kiriman", f"{kolom}_asal")
    op.drop_column("kiriman", "telepon_pengirim")
    op.drop_column("kiriman", "alamat_asal")
    op.drop_column("kiriman", "lng_asal")
    op.drop_column("kiriman", "lat_asal")

    for kolom in _KOLOM_ALAMAT:
        op.drop_column("kiriman", f"{kolom}_tujuan")
    op.drop_column("kiriman", "telepon_penerima")
    op.drop_column("kiriman", "nama_penerima")
