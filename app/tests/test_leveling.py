from __future__ import annotations

from app.services.leveling import level_from_xp, progress, threshold_for


def test_thresholds_monotonic() -> None:
    assert threshold_for(1) == 0
    assert threshold_for(2) == 100
    assert threshold_for(3) > threshold_for(2)
    assert threshold_for(10) > threshold_for(5)


def test_level_from_xp_basic() -> None:
    assert level_from_xp(0) == 1
    assert level_from_xp(-100) == 1
    assert level_from_xp(99) == 1
    assert level_from_xp(100) == 2
    assert level_from_xp(threshold_for(5)) == 5


def test_progress_shape() -> None:
    p = progress(150)
    assert p.level == 2
    assert p.xp_into_level == 150 - threshold_for(2)
    assert p.xp_for_next == threshold_for(3) - threshold_for(2)
    assert p.xp_total == 150
