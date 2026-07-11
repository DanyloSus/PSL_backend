"""add onboarding_completed to users

Revision ID: 0007_add_onboarding_completed
Revises: 0006_template_quantity_bounds
Create Date: 2026-07-11 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_add_onboarding_completed"
down_revision: str | None = "0006_template_quantity_bounds"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "onboarding_completed")
