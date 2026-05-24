from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    pass


class ActivityInputType(enum.StrEnum):
    BINARY = "BINARY"
    QUANTITY = "QUANTITY"


class ActivityTemplate(Base):
    __tablename__ = "activity_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    input_type: Mapped[ActivityInputType] = mapped_column(
        Enum(ActivityInputType, name="activity_input_type"),
        nullable=False,
        default=ActivityInputType.BINARY,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    effects: Mapped[list[ActivityEffect]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ActivityEffect(Base):
    __tablename__ = "activity_effects"
    __table_args__ = (UniqueConstraint("template_id", "stat_id", name="uq_template_stat_effect"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activity_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    xp_change: Mapped[int] = mapped_column(Integer, nullable=False)

    template: Mapped[ActivityTemplate] = relationship(back_populates="effects")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activity_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_xp_applied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    effects_applied: Mapped[list[ActivityLogEffect]] = relationship(
        back_populates="log",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ActivityLogEffect(Base):
    __tablename__ = "activity_log_effects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activity_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stats.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    xp_applied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    log: Mapped[ActivityLog] = relationship(back_populates="effects_applied")
