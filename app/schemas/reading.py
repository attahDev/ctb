from datetime import datetime

from pydantic import BaseModel


class ReadingDayOut(BaseModel):
    id: int
    day_number: int
    reference: str

    model_config = {"from_attributes": True}


class ReadingDayCreate(BaseModel):
    day_number: int
    reference: str


class ReadingPlanOut(BaseModel):
    id: int
    title: str
    description: str
    created_at: datetime
    days: list[ReadingDayOut] = []

    model_config = {"from_attributes": True}


class ReadingPlanCreate(BaseModel):
    title: str
    description: str = ""


class ReadingProgressOut(BaseModel):
    reading_day_id: int
    completed_at: datetime

    model_config = {"from_attributes": True}


class MarkDayComplete(BaseModel):
    reading_day_id: int


class CertificateOut(BaseModel):
    id: int
    title: str
    issued_at: datetime
    plan_id: int | None

    model_config = {"from_attributes": True}
