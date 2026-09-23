from datetime import datetime

from pydantic import BaseModel


class LiveSessionBase(BaseModel):
    title: str
    link: str
    description: str = ""
    scheduled_at: datetime | None = None
    is_active: bool = True


class LiveSessionCreate(LiveSessionBase):
    pass


class LiveSessionUpdate(BaseModel):
    title: str | None = None
    link: str | None = None
    description: str | None = None
    scheduled_at: datetime | None = None
    is_active: bool | None = None


class LiveSessionOut(LiveSessionBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
