from __future__ import annotations

from app.services.leveling import LevelingService


def test_thresholds_monotonic() -> None:
    assert LevelingService.threshold_for(1) == 0
    assert LevelingService.threshold_for(2) == 100
    assert LevelingService.threshold_for(3) > LevelingService.threshold_for(2)
    assert LevelingService.threshold_for(10) > LevelingService.threshold_for(5)


def test_level_from_xp_basic() -> None:
    assert LevelingService.level_from_xp(0) == 1
    assert LevelingService.level_from_xp(-100) == 1
    assert LevelingService.level_from_xp(99) == 1
    assert LevelingService.level_from_xp(100) == 2
    assert LevelingService.level_from_xp(LevelingService.threshold_for(5)) == 5


def test_progress_shape() -> None:
    p = LevelingService.progress(150)
    assert p.level == 2
    assert p.xp_into_level == 150 - LevelingService.threshold_for(2)
    assert p.xp_for_next == LevelingService.threshold_for(3) - LevelingService.threshold_for(2)
    assert p.xp_total == 150
