"""v2 §4/C1: kolom q10 & suhu_acuan_c di komoditas (sisa umur simpan)

Revision ID: c4e5f6a07b18
Revises: b3f2a91c04d7
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c4e5f6a07b18"
down_revision: Union[str, Sequence[str], None] = "b3f2a91c04d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "komoditas",
        sa.Column("q10", sa.Numeric(precision=4, scale=2), nullable=False, server_default="2.0"),
    )
    op.add_column(
        "komoditas",
        sa.Column("suhu_acuan_c", sa.Numeric(precision=4, scale=1), nullable=False, server_default="25"),
    )


def downgrade() -> None:
    op.drop_column("komoditas", "suhu_acuan_c")
    op.drop_column("komoditas", "q10")
