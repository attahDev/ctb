"""Public-facing endpoints: read-only content + the six form submissions
that the frontend already has UI for but nowhere to send data yet."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import asc
from sqlalchemy.orm import Session

from app.core.limiter import limiter
from app.db.session import get_db
from app.models.event import Event
from app.models.live_session import LiveSession
from app.models.partner import Partner
from app.models.testimony import Testimony
from app.models.submissions import (
    BibleClassEnrollment,
    ContactSubmission,
    NewsletterSubscriber,
    PrayerRequest,
    TribeJoinRequest,
    VolunteerApplication,
)
from app.schemas.event import EventOut
from app.schemas.live_session import LiveSessionOut
from app.schemas.partner import PartnerOut
from app.schemas.testimony import TestimonyOut
from app.schemas.submissions import (
    BibleClassCreate,
    BibleClassOut,
    ContactCreate,
    ContactOut,
    NewsletterCreate,
    NewsletterOut,
    PrayerRequestCreate,
    PrayerRequestOut,
    TribeJoinCreate,
    TribeJoinOut,
    VolunteerCreate,
    VolunteerOut,
)
from app.services.email import send_email

router = APIRouter(tags=["public"])

FORM_RATE_LIMIT = "10/minute"


# ---------------- Content (read-only) ----------------

@router.get("/events", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)):
    return (
        db.query(Event)
        .filter(Event.is_published.is_(True))
        .order_by(asc(Event.created_at))
        .all()
    )


@router.get("/events/{slug}", response_model=EventOut)
def get_event(slug: str, db: Session = Depends(get_db)):
    event = (
        db.query(Event)
        .filter(Event.slug == slug, Event.is_published.is_(True))
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/testimonies", response_model=list[TestimonyOut])
def list_testimonies(featured_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(Testimony).filter(Testimony.is_published.is_(True))
    if featured_only:
        query = query.filter(Testimony.is_featured.is_(True))
    return query.order_by(asc(Testimony.created_at)).all()


@router.get("/partners", response_model=list[PartnerOut])
def list_partners(db: Session = Depends(get_db)):
    return (
        db.query(Partner)
        .filter(Partner.is_published.is_(True))
        .order_by(asc(Partner.sort_order))
        .all()
    )


@router.get("/live-sessions", response_model=list[LiveSessionOut])
def list_live_sessions(db: Session = Depends(get_db)):
    return (
        db.query(LiveSession)
        .filter(LiveSession.is_active.is_(True))
        .order_by(asc(LiveSession.scheduled_at))
        .all()
    )


# ---------------- Form submissions ----------------
# Each is rate-limited (10/min/IP via Redis) since these are open, unauthenticated
# endpoints that will otherwise be the first thing spam bots find.

@router.post("/contact", response_model=ContactOut, status_code=201)
@limiter.limit(FORM_RATE_LIMIT)
def submit_contact(
    request: Request,
    payload: ContactCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    submission = ContactSubmission(**payload.model_dump())
    db.add(submission)
    db.commit()
    db.refresh(submission)
    background_tasks.add_task(
        send_email,
        payload.email,
        "We received your message — Glory Time Christian Center",
        f"Hi {payload.full_name}, thanks for reaching out. Someone from our team will respond soon.",
    )
    return submission


@router.post("/prayer-requests", response_model=PrayerRequestOut, status_code=201)
@limiter.limit(FORM_RATE_LIMIT)
def submit_prayer_request(request: Request, payload: PrayerRequestCreate, db: Session = Depends(get_db)):
    prayer_request = PrayerRequest(**payload.model_dump())
    db.add(prayer_request)
    db.commit()
    db.refresh(prayer_request)
    return prayer_request


@router.post("/newsletter", response_model=NewsletterOut, status_code=201)
@limiter.limit(FORM_RATE_LIMIT)
def subscribe_newsletter(request: Request, payload: NewsletterCreate, db: Session = Depends(get_db)):
    existing = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == payload.email
    ).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
        return existing

    subscriber = NewsletterSubscriber(email=payload.email)
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    return subscriber


@router.post("/volunteer", response_model=VolunteerOut, status_code=201)
@limiter.limit(FORM_RATE_LIMIT)
def submit_volunteer(request: Request, payload: VolunteerCreate, db: Session = Depends(get_db)):
    application = VolunteerApplication(**payload.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.post("/bible-class", response_model=BibleClassOut, status_code=201)
@limiter.limit(FORM_RATE_LIMIT)
def submit_bible_class(request: Request, payload: BibleClassCreate, db: Session = Depends(get_db)):
    enrollment = BibleClassEnrollment(**payload.model_dump())
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.post("/tribe-join", response_model=TribeJoinOut, status_code=201)
@limiter.limit(FORM_RATE_LIMIT)
def submit_tribe_join(request: Request, payload: TribeJoinCreate, db: Session = Depends(get_db)):
    tribe_request = TribeJoinRequest(**payload.model_dump())
    db.add(tribe_request)
    db.commit()
    db.refresh(tribe_request)
    return tribe_request
