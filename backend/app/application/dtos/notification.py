from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event: str
    title: str
    body: str
    opportunity_id: str | None = None
    read_at: datetime | None = None
    created_at: datetime
