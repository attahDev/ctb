from datetime import datetime

from pydantic import BaseModel


class TestimonyBase(BaseModel):
    name: str
    role: str = ""
    quote: str
    image_url: str = ""
    is_featured: bool = False
    is_published: bool = True


class TestimonyCreate(TestimonyBase):
    pass


class TestimonySubmit(BaseModel):
    """What the public can submit — no control over is_published/is_featured,
    those stay admin-only via the full TestimonyCreate/admin panel."""

    name: str
    role: str = ""
    quote: str


class TestimonyUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    quote: str | None = None
    image_url: str | None = None
    is_featured: bool | None = None
    is_published: bool | None = None


class TestimonyOut(TestimonyBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
