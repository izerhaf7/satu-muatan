"""v2 rename: koperasi -> titik_kumpul, peran KOPERASI -> PETUGAS

Spec delta v2 §2:
- tabel koperasi -> titik_kumpul, kolom alamat_gudang -> alamat,
  + kolom tipe (enum tipe_titik_kumpul, default PETANI_UTAMA) & petugas_id (FK pengguna)
- slot.koperasi_id -> titik_kumpul_id, slot.subsidi_koperasi -> selisih_jaminan_atap
- pengguna.koperasi_id -> titik_kumpul_id
- enum peran_pengguna: nilai KOPERASI -> PETUGAS (recreate-type pattern)
- enum atribusi: + nilai NORMAL (dipakai §6/C3)

Revision ID: b3f2a91c04d7
Revises: 1c78e6ed77bb
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b3f2a91c04d7"
down_revision: Union[str, Sequence[str], None] = "1c78e6ed77bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. enum baru untuk tipe titik kumpul
    tipe_titik_kumpul = postgresql.ENUM(
        "PETANI_UTAMA", "GAPOKTAN", "KOPERASI", "MITRA", name="tipe_titik_kumpul"
    )
    tipe_titik_kumpul.create(op.get_bind())

    # 2. rename tabel + kolom alamat, tambah tipe & petugas_id
    op.rename_table("koperasi", "titik_kumpul")
    op.alter_column("titik_kumpul", "alamat_gudang", new_column_name="alamat")
    op.add_column(
        "titik_kumpul",
        sa.Column("tipe", tipe_titik_kumpul, nullable=False, server_default="PETANI_UTAMA"),
    )
    op.add_column(
        "titik_kumpul",
        sa.Column("petugas_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pengguna.id"), nullable=True),
    )

    # 3. rename kolom FK & kolom selisih di slot/pengguna
    op.alter_column("slot", "koperasi_id", new_column_name="titik_kumpul_id")
    op.alter_column("slot", "subsidi_koperasi", new_column_name="selisih_jaminan_atap")
    op.alter_column("pengguna", "koperasi_id", new_column_name="titik_kumpul_id")

    # 4. enum peran_pengguna: KOPERASI -> PETUGAS.
    #    Pola recreate-type (aman dalam satu transaksi; ADD VALUE tidak bisa
    #    dipakai untuk UPDATE di transaksi yang sama).
    op.execute("ALTER TYPE peran_pengguna RENAME TO peran_pengguna_old")
    op.execute("CREATE TYPE peran_pengguna AS ENUM ('PETANI', 'PETUGAS', 'PENERIMA')")
    op.execute(
        "ALTER TABLE pengguna ALTER COLUMN peran TYPE peran_pengguna USING "
        "(CASE WHEN peran::text = 'KOPERASI' THEN 'PETUGAS' ELSE peran::text END)::peran_pengguna"
    )
    op.execute("DROP TYPE peran_pengguna_old")

    # 5. enum atribusi: tambah NORMAL (dipakai logika §6/C3).
    op.execute("ALTER TYPE atribusi ADD VALUE 'NORMAL'")


def downgrade() -> None:
    # 4'. kembalikan enum peran_pengguna (PETUGAS -> KOPERASI)
    op.execute("ALTER TYPE peran_pengguna RENAME TO peran_pengguna_old")
    op.execute("CREATE TYPE peran_pengguna AS ENUM ('PETANI', 'KOPERASI', 'PENERIMA')")
    op.execute(
        "ALTER TABLE pengguna ALTER COLUMN peran TYPE peran_pengguna USING "
        "(CASE WHEN peran::text = 'PETUGAS' THEN 'KOPERASI' ELSE peran::text END)::peran_pengguna"
    )
    op.execute("DROP TYPE peran_pengguna_old")
    # Catatan: nilai NORMAL di enum atribusi dibiarkan saat downgrade — Postgres
    # tidak bisa menghapus satu nilai enum tanpa recreate type; nilai tambahan
    # tidak merusak data lama.

    # 3'. kembalikan nama kolom
    op.alter_column("pengguna", "titik_kumpul_id", new_column_name="koperasi_id")
    op.alter_column("slot", "selisih_jaminan_atap", new_column_name="subsidi_koperasi")
    op.alter_column("slot", "titik_kumpul_id", new_column_name="koperasi_id")

    # 2'. kembalikan tabel
    op.drop_column("titik_kumpul", "petugas_id")
    op.drop_column("titik_kumpul", "tipe")
    op.alter_column("titik_kumpul", "alamat", new_column_name="alamat_gudang")
    op.rename_table("titik_kumpul", "koperasi")

    # 1'. hapus enum tipe titik kumpul
    sa.Enum(name="tipe_titik_kumpul").drop(op.get_bind())
