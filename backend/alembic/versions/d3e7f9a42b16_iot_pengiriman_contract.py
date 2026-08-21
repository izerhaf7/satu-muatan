"""IoT telemetry, GPS, sensor assignment, and shipment status contract.

Revision ID: d3e7f9a42b16
Revises: f4d2a8c91e35
"""

from importlib import import_module

import sqlalchemy as sa

op = import_module("alembic.op")


revision = "d3e7f9a42b16"
down_revision = "f4d2a8c91e35"
branch_labels = None
depends_on = None


status_pengiriman = sa.Enum("MUAT", "ANTAR", "BONGKAR_MUAT", "SELESAI", name="status_pengiriman")


def upgrade() -> None:
    status_pengiriman.create(op.get_bind(), checkfirst=True)
    op.add_column("slot", sa.Column("sensor_node_path", sa.Text(), nullable=True))
    op.add_column("pengiriman", sa.Column("status_pengiriman", status_pengiriman, nullable=True))
    op.add_column("jejak_posisi", sa.Column("akurasi_m", sa.Float(), nullable=True))
    op.add_column("telemetri", sa.Column("sensor_uptime_ms", sa.Integer(), nullable=True))
    op.add_column("telemetri", sa.Column("received_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("telemetri", "received_at")
    op.drop_column("telemetri", "sensor_uptime_ms")
    op.drop_column("jejak_posisi", "akurasi_m")
    op.drop_column("pengiriman", "status_pengiriman")
    op.drop_column("slot", "sensor_node_path")
    status_pengiriman.drop(op.get_bind(), checkfirst=True)
