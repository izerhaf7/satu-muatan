"""v4 (K14) — indeks mutu penerima: hapus potongan, catat indeks, status DITOLAK

Tiga perubahan, semuanya berpasangan dengan aturan produk K14:

1. `serah_terima.persen_potongan` DIHAPUS. Kolom itu tidak pernah memengaruhi
   pembayaran apa pun — hanya menyimpan angka tawar-menawar. Penerima tidak
   boleh punya tuas komersial.
2. `serah_terima.indeks_mutu` DITAMBAH. Angka mutu yang benar-benar DILIHAT
   penerima saat memutuskan, supaya keputusannya bisa diaudit terhadap dasar
   yang sama.
3. Label enum baru: `status_partisipasi.DITOLAK` (penolakan bukan "selesai") dan
   `keputusan_serah_terima` tanpa `POTONG`.

Catatan PostgreSQL: label enum tidak bisa dibuang dengan ALTER TYPE, jadi
`keputusan_serah_terima` dibangun ulang sebagai tipe baru lalu ditukar. Baris
lama bernilai POTONG dipetakan ke TERIMA — secara historis memang barangnya
diterima, hanya dengan potongan yang tidak pernah berlaku.

Revision ID: b7e4c19a2f85
Revises: a2d5f8c14e73
"""

import sqlalchemy as sa
from alembic import op

revision = "b7e4c19a2f85"
down_revision = "a2d5f8c14e73"
branch_labels = None
depends_on = None

_LAMA = ("TERIMA", "POTONG", "TOLAK")
_BARU = ("TERIMA", "TOLAK")


def upgrade() -> None:
    op.drop_column("serah_terima", "persen_potongan")
    op.add_column("serah_terima", sa.Column("indeks_mutu", sa.Integer(), nullable=True))

    # ALTER TYPE ... ADD VALUE tidak boleh dipakai lalu nilainya dipakai dalam
    # transaksi yang sama; di sini hanya ditambahkan, jadi aman.
    op.execute("ALTER TYPE status_partisipasi ADD VALUE IF NOT EXISTS 'DITOLAK'")

    _tukar_enum_keputusan(_BARU, petakan_potong_ke="TERIMA")


def downgrade() -> None:
    _tukar_enum_keputusan(_LAMA)

    # Label DITOLAK dibiarkan ada: membuangnya menuntut membangun ulang tipe
    # beserta seluruh kolom yang memakainya, dan tidak ada baris yang rusak
    # karena kehadirannya.
    op.drop_column("serah_terima", "indeks_mutu")
    op.add_column(
        "serah_terima",
        sa.Column("persen_potongan", sa.Integer(), nullable=False, server_default="0"),
    )


def _tukar_enum_keputusan(label: tuple[str, ...], petakan_potong_ke: str | None = None) -> None:
    """Bangun ulang `keputusan_serah_terima` dengan daftar label baru."""
    daftar = ", ".join(f"'{x}'" for x in label)
    op.execute(f"CREATE TYPE keputusan_serah_terima_baru AS ENUM ({daftar})")

    if petakan_potong_ke is not None:
        op.execute(
            f"UPDATE serah_terima SET keputusan = '{petakan_potong_ke}' WHERE keputusan = 'POTONG'"
        )

    op.execute(
        "ALTER TABLE serah_terima ALTER COLUMN keputusan TYPE keputusan_serah_terima_baru "
        "USING keputusan::text::keputusan_serah_terima_baru"
    )
    op.execute("DROP TYPE keputusan_serah_terima")
    op.execute("ALTER TYPE keputusan_serah_terima_baru RENAME TO keputusan_serah_terima")
