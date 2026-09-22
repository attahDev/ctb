from datetime import datetime

from pydantic import BaseModel


class PartnerBase(BaseModel):
    name: str
    logo_url: str = ""
    website_url: str = ""
    sort_order: int = 0
    is_published: bool = True


class PartnerCreate(PartnerBase):
    pass


class PartnerUpdate(BaseModel):
    name: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    sort_order: int | None = None
    is_published: bool | None = None


class PartnerOut(PartnerBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
