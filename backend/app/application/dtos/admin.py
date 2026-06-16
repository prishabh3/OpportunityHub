from datetime import datetime

from pydantic import BaseModel


class AdminAnalytics(BaseModel):
    opportunities_total: int
    by_type: dict[str, int]
    users_total: int
    bookmarks_total: int
    notifications_total: int


class SourceStat(BaseModel):
    key: str
    display_name: str
    opportunity_count: int


class ConnectorRunRead(BaseModel):
    id: str
    source_key: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    items_found: int
    items_created: int
    items_updated: int
    items_failed: int
    error_message: str | None = None
