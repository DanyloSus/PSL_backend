from __future__ import annotations

from sqladmin import ModelView

from app.models.activity import (
    ActivityEffect,
    ActivityLog,
    ActivityLogEffect,
    ActivityTemplate,
)
from app.models.stat import Stat
from app.models.user import User
from app.models.user_stat import UserStat


class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    column_list = [
        User.id,
        User.email,
        User.username,
        User.role,
        User.global_level,
        User.global_xp,
        User.is_active,
        User.created_at,
    ]
    column_searchable_list = [User.email, User.username]
    column_sortable_list = [User.created_at, User.global_level, User.global_xp]
    form_excluded_columns = [User.password_hash, User.refresh_tokens]


class StatAdmin(ModelView, model=Stat):
    name = "Stat"
    name_plural = "Stats"
    icon = "fa-solid fa-chart-simple"
    column_list = [Stat.key, Stat.display_name, Stat.icon]
    column_searchable_list = [Stat.key, Stat.display_name]


class UserStatAdmin(ModelView, model=UserStat):
    name = "UserStat"
    name_plural = "UserStats"
    icon = "fa-solid fa-bolt"
    column_list = [
        UserStat.id,
        UserStat.user_id,
        UserStat.stat_id,
        UserStat.xp,
        UserStat.level,
    ]


class ActivityTemplateAdmin(ModelView, model=ActivityTemplate):
    name = "Activity Template"
    name_plural = "Activity Templates"
    icon = "fa-solid fa-list-check"
    column_list = [
        ActivityTemplate.title,
        ActivityTemplate.input_type,
        ActivityTemplate.is_enabled,
        ActivityTemplate.created_at,
    ]
    column_searchable_list = [ActivityTemplate.title]
    column_sortable_list = [ActivityTemplate.title, ActivityTemplate.created_at]


class ActivityEffectAdmin(ModelView, model=ActivityEffect):
    name = "Activity Effect"
    name_plural = "Activity Effects"
    icon = "fa-solid fa-arrow-trend-up"
    column_list = [
        ActivityEffect.id,
        ActivityEffect.template_id,
        ActivityEffect.stat_id,
        ActivityEffect.xp_change,
    ]


class ActivityLogAdmin(ModelView, model=ActivityLog):
    name = "Activity Log"
    name_plural = "Activity Logs"
    icon = "fa-solid fa-clipboard-list"
    can_create = False
    can_edit = False
    can_delete = False
    column_list = [
        ActivityLog.id,
        ActivityLog.user_id,
        ActivityLog.template_id,
        ActivityLog.quantity,
        ActivityLog.total_xp_applied,
        ActivityLog.created_at,
    ]
    column_sortable_list = [ActivityLog.created_at, ActivityLog.total_xp_applied]


class ActivityLogEffectAdmin(ModelView, model=ActivityLogEffect):
    name = "Activity Log Effect"
    name_plural = "Activity Log Effects"
    can_create = False
    can_edit = False
    can_delete = False
    column_list = [
        ActivityLogEffect.id,
        ActivityLogEffect.log_id,
        ActivityLogEffect.stat_id,
        ActivityLogEffect.xp_applied,
    ]


ALL_VIEWS = [
    UserAdmin,
    StatAdmin,
    UserStatAdmin,
    ActivityTemplateAdmin,
    ActivityEffectAdmin,
    ActivityLogAdmin,
    ActivityLogEffectAdmin,
]
