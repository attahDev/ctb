from datetime import datetime

from pydantic import BaseModel, EmailStr


class StatusUpdate(BaseModel):
    status: str
    show_on_wall: bool | None = None  # only meaningful for prayer-requests


# --- Contact ---
class ContactCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str = ""
    message: str


class ContactOut(ContactCreate):
    id: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Prayer request ---
class PrayerRequestCreate(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    request_text: str
    is_private: bool = False


class PrayerRequestOut(PrayerRequestCreate):
    id: int
    status: str
    show_on_wall: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PrayerWallEntry(BaseModel):
    """Public-safe subset — never exposes email/phone."""

    name: str
    request_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Newsletter ---
class NewsletterCreate(BaseModel):
    email: EmailStr


class NewsletterOut(NewsletterCreate):
    id: int
    is_active: bool
    subscribed_at: datetime

    model_config = {"from_attributes": True}


# --- Volunteer ---
class VolunteerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str = ""
    area_of_interest: str = ""
    message: str = ""


class VolunteerOut(VolunteerCreate):
    id: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Bible class ---
class BibleClassCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str = ""
    preferred_schedule: str = ""


class BibleClassOut(BibleClassCreate):
    id: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Tribe join ---
class TribeJoinCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str = ""
    tribe_preference: str = ""
    message: str = ""


class TribeJoinOut(TribeJoinCreate):
    id: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Counselling ---
class CounsellingCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str = ""
    preferred_format: str = ""
    message: str = ""


class CounsellingOut(CounsellingCreate):
    id: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
