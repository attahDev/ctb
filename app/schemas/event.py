from datetime import datetime

from pydantic import BaseModel


class EventBase(BaseModel):
    title: str
    slug: str
    day: str
    month: str
    time_display: str
    location: str
    summary: str
    image_url: str = ""
    is_published: bool = True


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    day: str | None = None
    month: str | None = None
    time_display: str | None = None
    location: str | None = None
    summary: str | None = None
    image_url: str | None = None
    is_published: bool | None = None


class EventOut(EventBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
