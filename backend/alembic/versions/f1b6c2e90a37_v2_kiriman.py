"""v2 §3/C0: tabel kiriman (pencocokan otomatis)

Revision ID: f1b6c2e90a37
Revises: e8c1d4a55b06
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f1b6c2e90a37"
down_revision: Union[str, Sequence[str], None] = "e8c1d4a55b06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kiriman",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("petani_id", sa.UUID(), nullable=False),
        sa.Column("komoditas_id", sa.UUID(), nullable=False),
        sa.Column("volume_kg", sa.Integer(), nullable=False),
        sa.Column("tanggal_siap", sa.Date(), nullable=False),
        sa.Column("lat_tujuan", sa.Double(), nullable=False),
        sa.Column("lng_tujuan", sa.Double(), nullable=False),
        sa.Column("alamat_tujuan", sa.Text(), nullable=False),
        sa.Column("slot_id", sa.UUID(), nullable=True),
        sa.Column("partisipasi_id", sa.UUID(), nullable=True),
        sa.Column("dibuat_pada", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["komoditas_id"], ["komoditas.id"]),
        sa.ForeignKeyConstraint(["partisipasi_id"], ["partisipasi.id"]),
        sa.ForeignKeyConstraint(["petani_id"], ["pengguna.id"]),
        sa.ForeignKeyConstraint(["slot_id"], ["slot.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("kiriman")
