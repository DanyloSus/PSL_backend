from __future__ import annotations

import uuid

from pydantic import BaseModel


class StatOut(BaseModel):
    id: uuid.UUID
    key: str
    display_name: str
    icon: str

    model_config = {"from_attributes": True}


class UserStatOut(BaseModel):
    stat: StatOut
    xp: int
    level: int
    xp_into_level: int
    xp_for_next: int
