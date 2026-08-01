"""v2 §5/C2: tabel telemetri (suhu/kelembapan dummy per pengiriman)

Revision ID: d7a9b2e31f40
Revises: c4e5f6a07b18
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d7a9b2e31f40"
down_revision: Union[str, Sequence[str], None] = "c4e5f6a07b18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum dibuat OTOMATIS oleh op.create_table (pola sama seperti migrasi awal
    # 1c78e6ed77bb) — .create() eksplisit sebelum create_table malah memicu
    # DuplicateObject (create_table meng-create type lagi).
    sumber_telemetri = postgresql.ENUM("SIMULASI", "SENSOR", "HP_PETUGAS", name="sumber_telemetri")

    op.create_table(
        "telemetri",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("pengiriman_id", sa.UUID(), nullable=False),
        sa.Column("waktu", sa.DateTime(timezone=True), nullable=False),
        sa.Column("suhu_c", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("kelembapan_persen", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("lat", sa.Double(), nullable=True),
        sa.Column("lng", sa.Double(), nullable=True),
        sa.Column("sumber", sumber_telemetri, nullable=False),
        sa.ForeignKeyConstraint(["pengiriman_id"], ["pengiriman.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("telemetri")
    sa.Enum(name="sumber_telemetri").drop(op.get_bind())
