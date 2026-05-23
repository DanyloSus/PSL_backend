"""seed activity templates

Revision ID: 0005_seed_activity_templates
Revises: 0004_activities
Create Date: 2026-05-23 22:30:00.000000

"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_seed_activity_templates"
down_revision: str | None = "0004_activities"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Each entry: (title, description, input_type, [(stat_key, xp_change), ...])
_TEMPLATES: list[tuple[str, str, str, list[tuple[str, int]]]] = [
    (
        "Workout (gym)",
        "Strength training session, 1 hour.",
        "QUANTITY",
        [("strength", 10), ("health", 3), ("endurance", 2)],
    ),
    ("Run", "Cardio run, 1 km.", "QUANTITY", [("endurance", 5), ("health", 2)]),
    ("Walk", "Walking, 1 km.", "QUANTITY", [("endurance", 2), ("mental_state", 1)]),
    (
        "Read book",
        "Reading non-fiction, 30 minutes.",
        "QUANTITY",
        [("intelligence", 6), ("mental_state", 2)],
    ),
    ("Study / course", "Focused learning, 1 hour.", "QUANTITY", [("intelligence", 10)]),
    ("Quality sleep (8h)", "Slept ~8 hours.", "BINARY", [("health", 10), ("mental_state", 5)]),
    ("Meditate", "Meditation session, 15 minutes.", "QUANTITY", [("mental_state", 7)]),
    ("Drink water (1L)", "Hydrate, 1 liter.", "QUANTITY", [("health", 2)]),
    ("Healthy meal", "Cooked balanced meal.", "BINARY", [("health", 5)]),
    (
        "Call family or friend",
        "Meaningful conversation.",
        "BINARY",
        [("social_skills", 6), ("mental_state", 2)],
    ),
    ("Meet someone new", "Engaged with a new person.", "BINARY", [("social_skills", 8)]),
    ("Save money", "Set aside savings or invested.", "BINARY", [("finance", 8)]),
    (
        "Alcohol",
        "Drank alcohol.",
        "BINARY",
        [("social_skills", 3), ("health", -10), ("mental_state", -3)],
    ),
    ("Junk food", "Ate fast/junk food.", "BINARY", [("health", -6)]),
    (
        "Doomscroll (1h)",
        "Scrolled social feeds, 1 hour.",
        "QUANTITY",
        [("intelligence", -3), ("mental_state", -4)],
    ),
]


def upgrade() -> None:
    bind = op.get_bind()
    stats_result = bind.execute(sa.text("SELECT id, key FROM stats")).all()
    stat_id_by_key = {row[1]: row[0] for row in stats_result}

    templates = sa.table(
        "activity_templates",
        sa.column("id", sa.UUID()),
        sa.column("title", sa.String()),
        sa.column("description", sa.String()),
        sa.column("input_type", sa.Enum("BINARY", "QUANTITY", name="activity_input_type")),
        sa.column("is_enabled", sa.Boolean()),
    )
    effects = sa.table(
        "activity_effects",
        sa.column("id", sa.UUID()),
        sa.column("template_id", sa.UUID()),
        sa.column("stat_id", sa.UUID()),
        sa.column("xp_change", sa.Integer()),
    )

    template_rows = []
    effect_rows = []
    for title, desc, input_type, eff_specs in _TEMPLATES:
        tpl_id = uuid.uuid4()
        template_rows.append(
            {
                "id": tpl_id,
                "title": title,
                "description": desc,
                "input_type": input_type,
                "is_enabled": True,
            }
        )
        for stat_key, xp in eff_specs:
            stat_id = stat_id_by_key.get(stat_key)
            if stat_id is None:
                continue
            effect_rows.append(
                {
                    "id": uuid.uuid4(),
                    "template_id": tpl_id,
                    "stat_id": stat_id,
                    "xp_change": xp,
                }
            )
    op.bulk_insert(templates, template_rows)
    op.bulk_insert(effects, effect_rows)


def downgrade() -> None:
    titles = [t[0] for t in _TEMPLATES]
    op.execute(
        sa.text("DELETE FROM activity_templates WHERE title = ANY(:titles)").bindparams(
            titles=titles
        )
    )
