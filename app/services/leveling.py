"""XP / level helpers.

Cumulative XP required to *reach* level L: floor(100 * (L-1)**1.5).
Level 1 starts at xp=0. Levels never decrease in MVP.
"""

from __future__ import annotations

from dataclasses import dataclass


def threshold_for(level: int) -> int:
    if level <= 1:
        return 0
    return int(100 * (level - 1) ** 1.5)


def level_from_xp(xp: int) -> int:
    if xp <= 0:
        return 1
    level = 1
    while threshold_for(level + 1) <= xp:
        level += 1
    return level


@dataclass(slots=True, frozen=True)
class LevelProgress:
    level: int
    xp_into_level: int
    xp_for_next: int
    xp_total: int


def progress(xp: int) -> LevelProgress:
    xp = max(0, xp)
    level = level_from_xp(xp)
    base = threshold_for(level)
    next_base = threshold_for(level + 1)
    return LevelProgress(
        level=level,
        xp_into_level=xp - base,
        xp_for_next=next_base - base,
        xp_total=xp,
    )
