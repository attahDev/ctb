"""Import every model here so anything that needs the full metadata
(Alembic autogenerate, Base.metadata.create_all) sees all tables.
Import this module, not app.db.base, when you need that."""

from app.db.base import Base  # noqa: F401
from app.models.admin import AdminUser  # noqa: F401
from app.models.event import Event  # noqa: F401
from app.models.testimony import Testimony  # noqa: F401
from app.models.partner import Partner  # noqa: F401
from app.models.submissions import (  # noqa: F401
    ContactSubmission,
    PrayerRequest,
    NewsletterSubscriber,
    VolunteerApplication,
    BibleClassEnrollment,
    TribeJoinRequest,
)
