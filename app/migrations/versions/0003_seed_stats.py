"""seed default stats

Revision ID: 0003_seed_stats
Revises: 0002_stats_user_stats
Create Date: 2026-05-23 22:00:00.000000

"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_seed_stats"
down_revision: str | None = "0002_stats_user_stats"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_DEFAULT_STATS = [
    ("strength", "Strength", "dumbbell"),
    ("health", "Health", "heart"),
    ("intelligence", "Intelligence", "brain"),
    ("mental_state", "Mental State", "flower"),
    ("endurance", "Endurance", "wind"),
    ("finance", "Finance", "coins"),
    ("social_skills", "Social Skills", "users"),
]


def upgrade() -> None:
    stats = sa.table(
        "stats",
        sa.column("id", sa.UUID()),
        sa.column("key", sa.String()),
        sa.column("display_name", sa.String()),
        sa.column("icon", sa.String()),
    )
    op.bulk_insert(
        stats,
        [
            {
                "id": uuid.uuid4(),
                "key": key,
                "display_name": name,
                "icon": icon,
            }
            for key, name, icon in _DEFAULT_STATS
        ],
    )


def downgrade() -> None:
    keys = [k for k, _, _ in _DEFAULT_STATS]
    op.execute(sa.text("DELETE FROM stats WHERE key = ANY(:keys)").bindparams(keys=keys))
