from datetime import datetime

from pydantic import BaseModel, EmailStr


class MemberRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""
    phone: str = ""


class MemberLogin(BaseModel):
    email: EmailStr
    password: str


class MemberOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    phone: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
