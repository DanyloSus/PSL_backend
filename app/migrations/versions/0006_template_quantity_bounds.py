"""template quantity bounds

Revision ID: 0006_template_quantity_bounds
Revises: 0005_seed_activity_templates
Create Date: 2026-06-02 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_template_quantity_bounds"
down_revision: str | None = "0005_seed_activity_templates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "activity_templates",
        sa.Column("min_quantity", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "activity_templates",
        sa.Column("max_quantity", sa.Integer(), server_default="100", nullable=False),
    )
    op.create_check_constraint(
        "ck_template_min_quantity", "activity_templates", "min_quantity >= 1"
    )
    op.create_check_constraint(
        "ck_template_max_ge_min", "activity_templates", "max_quantity >= min_quantity"
    )
    op.create_check_constraint(
        "ck_template_max_quantity", "activity_templates", "max_quantity <= 10000"
    )


def downgrade() -> None:
    op.drop_constraint("ck_template_max_quantity", "activity_templates", type_="check")
    op.drop_constraint("ck_template_max_ge_min", "activity_templates", type_="check")
    op.drop_constraint("ck_template_min_quantity", "activity_templates", type_="check")
    op.drop_column("activity_templates", "max_quantity")
    op.drop_column("activity_templates", "min_quantity")
