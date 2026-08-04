"""v3/K13: tujuan bebas, petugas=driver ditugaskan sistem, permintaan dihapus

Revision ID: a2d5f8c14e73
Revises: f1b6c2e90a37
Create Date: 2026-08-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a2d5f8c14e73"
down_revision: Union[str, Sequence[str], None] = "f1b6c2e90a37"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # K13: driver ditugaskan sistem per muatan (dasar otorisasi muat/tutup/majukan).
    op.add_column("slot", sa.Column("petugas_id", sa.UUID(), nullable=True))
    op.create_foreign_key("fk_slot_petugas", "slot", "pengguna", ["petugas_id"], ["id"])

    # K13: penerima jadi buku alamat tujuan; baris bentukan sistem ditandai.
    op.add_column(
        "penerima",
        sa.Column("dibuat_otomatis", sa.Boolean(), server_default="false", nullable=False),
    )

    # K13: tujuan hasil resolusi disimpan di kiriman — dasar alokasi lot → tujuan.
    op.add_column("kiriman", sa.Column("penerima_id", sa.UUID(), nullable=True))
    op.create_foreign_key("fk_kiriman_penerima", "kiriman", "penerima", ["penerima_id"], ["id"])

    # K13: permintaan dihapus — penerima murni menerima, tidak memesan.
    op.drop_table("permintaan")
    sa.Enum(name="status_permintaan").drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    status_permintaan = sa.Enum(
        "TERBUKA", "TERPENUHI_SEBAGIAN", "TERPENUHI", "KEDALUWARSA", name="status_permintaan"
    )
    status_permintaan.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "permintaan",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("penerima_id", sa.UUID(), nullable=False),
        sa.Column("komoditas_id", sa.UUID(), nullable=False),
        sa.Column("volume_kg", sa.Integer(), nullable=False),
        sa.Column("tanggal_dibutuhkan", sa.Date(), nullable=False),
        sa.Column("status", status_permintaan, nullable=False),
        sa.Column("slot_id", sa.UUID(), nullable=True),
        sa.Column("volume_terpenuhi_kg", sa.Integer(), server_default="0", nullable=False),
        sa.Column("dibuat_pada", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["komoditas_id"], ["komoditas.id"]),
        sa.ForeignKeyConstraint(["penerima_id"], ["penerima.id"]),
        sa.ForeignKeyConstraint(["slot_id"], ["slot.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.drop_constraint("fk_kiriman_penerima", "kiriman", type_="foreignkey")
    op.drop_column("kiriman", "penerima_id")
    op.drop_column("penerima", "dibuat_otomatis")
    op.drop_constraint("fk_slot_petugas", "slot", type_="foreignkey")
    op.drop_column("slot", "petugas_id")
