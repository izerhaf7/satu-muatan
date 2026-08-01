"""v2 §6/C3: lot.cacat_terlihat -> grade_asal, serah_terima + grade_tiba &
sisa_umur_simpan_persen

Backfill: cacat_terlihat=true -> grade_asal 2 (Kurang, di bawah ambang),
false -> 5 (Sangat baik). grade_tiba riwayat dipetakan dari atribusi lama.

Revision ID: e8c1d4a55b06
Revises: d7a9b2e31f40
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e8c1d4a55b06"
down_revision: Union[str, Sequence[str], None] = "d7a9b2e31f40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("lot", sa.Column("grade_asal", sa.Integer(), nullable=False, server_default="5"))
    op.execute("UPDATE lot SET grade_asal = CASE WHEN cacat_terlihat THEN 2 ELSE 5 END")
    op.drop_column("lot", "cacat_terlihat")

    op.add_column("serah_terima", sa.Column("grade_tiba", sa.Integer(), nullable=True))
    op.add_column("serah_terima", sa.Column("sisa_umur_simpan_persen", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE serah_terima SET grade_tiba = CASE atribusi::text "
        "WHEN 'PETANI' THEN 2 WHEN 'LOGISTIK' THEN 3 ELSE 5 END"
    )


def downgrade() -> None:
    op.drop_column("serah_terima", "sisa_umur_simpan_persen")
    op.drop_column("serah_terima", "grade_tiba")

    op.add_column("lot", sa.Column("cacat_terlihat", sa.Boolean(), nullable=False, server_default="false"))
    op.execute("UPDATE lot SET cacat_terlihat = (grade_asal < 3)")
    op.drop_column("lot", "grade_asal")
