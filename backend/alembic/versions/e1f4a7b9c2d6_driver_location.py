"""Store current driver location for nearby task assignment.

Revision ID: e1f4a7b9c2d6
Revises: d3e7f9a42b16
"""

from importlib import import_module

import sqlalchemy as sa

op = import_module("alembic.op")


revision = "e1f4a7b9c2d6"
down_revision = "d3e7f9a42b16"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pengguna", sa.Column("terkini_lat", sa.Float(), nullable=True))
    op.add_column("pengguna", sa.Column("terkini_lng", sa.Float(), nullable=True))
    op.add_column("pengguna", sa.Column("lokasi_diperbarui_pada", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_pengguna_terkini_lokasi", "pengguna", ["terkini_lat", "terkini_lng"])


def downgrade() -> None:
    op.drop_index("ix_pengguna_terkini_lokasi", table_name="pengguna")
    op.drop_column("pengguna", "lokasi_diperbarui_pada")
    op.drop_column("pengguna", "terkini_lng")
    op.drop_column("pengguna", "terkini_lat")
