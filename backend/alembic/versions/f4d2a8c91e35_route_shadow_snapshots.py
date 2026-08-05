"""Route shadow snapshots for informational provider data.

Revision ID: f4d2a8c91e35
Revises: c9a3f7d21b64
"""

from importlib import import_module

import sqlalchemy as sa

op = import_module("alembic.op")


revision = "f4d2a8c91e35"
down_revision = "c9a3f7d21b64"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pengiriman", sa.Column("rute_polyline", sa.Text(), nullable=True))
    op.add_column("pengiriman", sa.Column("rute_versi", sa.Integer(), nullable=True))
    op.add_column("pengiriman", sa.Column("rute_input_hash", sa.Text(), nullable=True))
    op.add_column("pengiriman", sa.Column("rute_jarak_provider_km", sa.Numeric(10, 3), nullable=True))
    op.add_column("pengiriman", sa.Column("rute_durasi_provider_menit", sa.Integer(), nullable=True))
    op.add_column("pengiriman", sa.Column("rute_dihitung_pada", sa.DateTime(timezone=True), nullable=True))
    op.add_column("pengiriman", sa.Column("rute_sumber", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("pengiriman", "rute_sumber")
    op.drop_column("pengiriman", "rute_dihitung_pada")
    op.drop_column("pengiriman", "rute_durasi_provider_menit")
    op.drop_column("pengiriman", "rute_jarak_provider_km")
    op.drop_column("pengiriman", "rute_input_hash")
    op.drop_column("pengiriman", "rute_versi")
    op.drop_column("pengiriman", "rute_polyline")
