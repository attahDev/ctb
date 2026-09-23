from datetime import datetime

from pydantic import BaseModel

from app.schemas.event import EventOut


class EventRegistrationCreate(BaseModel):
    event_id: int


class EventRegistrationOut(BaseModel):
    id: int
    registered_at: datetime
    event: EventOut

    model_config = {"from_attributes": True}


class RegistrantOut(BaseModel):
    """What admin sees when checking who's registered for an event —
    deliberately excludes anything sensitive, just enough to plan for."""

    member_id: int
    full_name: str
    email: str
    registered_at: datetime
