from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.activity import ActivityInputType
from app.schemas.user import StatOut


class ActivityEffectOut(BaseModel):
    stat_id: uuid.UUID
    xp_change: int

    model_config = {"from_attributes": True}


class ActivityTemplateOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    input_type: ActivityInputType
    is_enabled: bool
    effects: list[ActivityEffectOut]

    model_config = {"from_attributes": True}


class LogActivityRequest(BaseModel):
    activity_template_id: uuid.UUID = Field(alias="activityTemplateId")
    quantity: int = Field(default=1, ge=1, le=10_000)

    model_config = {"populate_by_name": True}


class AppliedEffect(BaseModel):
    stat: StatOut
    xp_applied: int
    xp: int
    level: int
    leveled_up: bool


class LogActivityResponse(BaseModel):
    log_id: uuid.UUID
    total_xp_applied: int
    applied: list[AppliedEffect]
    global_xp: int
    global_level: int
    global_leveled_up: bool


class ActivityHistoryEffect(BaseModel):
    stat_id: uuid.UUID
    xp_applied: int


class ActivityHistoryEntry(BaseModel):
    id: uuid.UUID
    activity_template_id: uuid.UUID
    quantity: int
    total_xp_applied: int
    created_at: datetime
    effects: list[ActivityHistoryEffect]
