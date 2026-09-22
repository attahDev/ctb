from pydantic import BaseModel, EmailStr


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""
    is_superadmin: bool = False


class AdminUserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_superadmin: bool
    is_active: bool

    model_config = {"from_attributes": True}
