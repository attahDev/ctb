"""Everything behind the admin login: content CRUD, submission moderation,
and (superadmin-only) managing other admin accounts."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_superadmin
from app.core.security import hash_password
from app.db.session import get_db
from app.services.storage import upload_image
from app.models.admin import AdminUser
from app.models.reading import ReadingDay, ReadingPlan
from app.models.registration import EventRegistration
from app.models.member import Member
from app.models.event import Event
from app.models.live_session import LiveSession
from app.models.partner import Partner
from app.models.testimony import Testimony
from app.models.submissions import (
    BibleClassEnrollment,
    ContactSubmission,
    CounsellingRequest,
    NewsletterSubscriber,
    PrayerRequest,
    TribeJoinRequest,
    VolunteerApplication,
)
from app.schemas.admin import AdminUserCreate, AdminUserOut
from app.schemas.reading import ReadingDayCreate, ReadingDayOut, ReadingPlanCreate, ReadingPlanOut
from app.schemas.registration import RegistrantOut
from app.schemas.event import EventCreate, EventOut, EventUpdate
from app.schemas.live_session import LiveSessionCreate, LiveSessionOut, LiveSessionUpdate
from app.schemas.partner import PartnerCreate, PartnerOut, PartnerUpdate
from app.schemas.testimony import TestimonyCreate, TestimonyOut, TestimonyUpdate
from app.schemas.submissions import (
    BibleClassOut,
    ContactOut,
    CounsellingOut,
    NewsletterOut,
    PrayerRequestOut,
    StatusUpdate,
    TribeJoinOut,
    VolunteerOut,
)

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)]
)


def _get_or_404(db: Session, model, obj_id: int):
    obj = db.query(model).filter(model.id == obj_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return obj


def _apply_update(obj, payload) -> None:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)


# ---------------- Events ----------------

@router.get("/events", response_model=list[EventOut])
def list_all_events(db: Session = Depends(get_db)):
    return db.query(Event).order_by(Event.created_at.desc()).all()


@router.post("/events", response_model=EventOut, status_code=201)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    if db.query(Event).filter(Event.slug == payload.slug).first():
        raise HTTPException(status_code=409, detail="An event with this slug already exists")
    event = Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.put("/events/{event_id}", response_model=EventOut)
def update_event(event_id: int, payload: EventUpdate, db: Session = Depends(get_db)):
    event = _get_or_404(db, Event, event_id)
    _apply_update(event, payload)
    db.commit()
    db.refresh(event)
    return event


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = _get_or_404(db, Event, event_id)
    db.delete(event)
    db.commit()


@router.get("/events/{event_id}/registrations", response_model=list[RegistrantOut])
def list_event_registrants(event_id: int, db: Session = Depends(get_db)):
    _get_or_404(db, Event, event_id)  # 404s cleanly if the event doesn't exist
    rows = (
        db.query(EventRegistration, Member)
        .join(Member, Member.id == EventRegistration.member_id)
        .filter(EventRegistration.event_id == event_id)
        .order_by(EventRegistration.registered_at.asc())
        .all()
    )
    return [
        RegistrantOut(
            member_id=member.id,
            full_name=member.full_name,
            email=member.email,
            registered_at=registration.registered_at,
        )
        for registration, member in rows
    ]


# ---------------- Testimonies ----------------

@router.get("/testimonies", response_model=list[TestimonyOut])
def list_all_testimonies(db: Session = Depends(get_db)):
    return db.query(Testimony).order_by(Testimony.created_at.desc()).all()


@router.post("/testimonies", response_model=TestimonyOut, status_code=201)
def create_testimony(payload: TestimonyCreate, db: Session = Depends(get_db)):
    testimony = Testimony(**payload.model_dump())
    db.add(testimony)
    db.commit()
    db.refresh(testimony)
    return testimony


@router.put("/testimonies/{testimony_id}", response_model=TestimonyOut)
def update_testimony(testimony_id: int, payload: TestimonyUpdate, db: Session = Depends(get_db)):
    testimony = _get_or_404(db, Testimony, testimony_id)
    _apply_update(testimony, payload)
    db.commit()
    db.refresh(testimony)
    return testimony


@router.delete("/testimonies/{testimony_id}", status_code=204)
def delete_testimony(testimony_id: int, db: Session = Depends(get_db)):
    testimony = _get_or_404(db, Testimony, testimony_id)
    db.delete(testimony)
    db.commit()


# ---------------- Partners ----------------

@router.get("/partners", response_model=list[PartnerOut])
def list_all_partners(db: Session = Depends(get_db)):
    return db.query(Partner).order_by(Partner.sort_order.asc()).all()


@router.post("/partners", response_model=PartnerOut, status_code=201)
def create_partner(payload: PartnerCreate, db: Session = Depends(get_db)):
    partner = Partner(**payload.model_dump())
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


@router.put("/partners/{partner_id}", response_model=PartnerOut)
def update_partner(partner_id: int, payload: PartnerUpdate, db: Session = Depends(get_db)):
    partner = _get_or_404(db, Partner, partner_id)
    _apply_update(partner, payload)
    db.commit()
    db.refresh(partner)
    return partner


@router.delete("/partners/{partner_id}", status_code=204)
def delete_partner(partner_id: int, db: Session = Depends(get_db)):
    partner = _get_or_404(db, Partner, partner_id)
    db.delete(partner)
    db.commit()


# ---------------- Live sessions (Zoom/Meet/etc links) ----------------

@router.get("/live-sessions", response_model=list[LiveSessionOut])
def list_all_live_sessions(db: Session = Depends(get_db)):
    return db.query(LiveSession).order_by(LiveSession.created_at.desc()).all()


@router.post("/live-sessions", response_model=LiveSessionOut, status_code=201)
def create_live_session(payload: LiveSessionCreate, db: Session = Depends(get_db)):
    session = LiveSession(**payload.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.put("/live-sessions/{session_id}", response_model=LiveSessionOut)
def update_live_session(
    session_id: int, payload: LiveSessionUpdate, db: Session = Depends(get_db)
):
    session = _get_or_404(db, LiveSession, session_id)
    _apply_update(session, payload)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/live-sessions/{session_id}", status_code=204)
def delete_live_session(session_id: int, db: Session = Depends(get_db)):
    session = _get_or_404(db, LiveSession, session_id)
    db.delete(session)
    db.commit()


# ---------------- Submission moderation ----------------
# Generic pattern: GET list (optionally filter by status) + PATCH status.

_SUBMISSION_MODELS = {
    "contact": (ContactSubmission, ContactOut),
    "prayer-requests": (PrayerRequest, PrayerRequestOut),
    "newsletter": (NewsletterSubscriber, NewsletterOut),
    "volunteer": (VolunteerApplication, VolunteerOut),
    "bible-class": (BibleClassEnrollment, BibleClassOut),
    "tribe-join": (TribeJoinRequest, TribeJoinOut),
    "counselling": (CounsellingRequest, CounsellingOut),
}


@router.get("/submissions/{kind}")
def list_submissions(kind: str, status: str | None = None, db: Session = Depends(get_db)):
    if kind not in _SUBMISSION_MODELS:
        raise HTTPException(status_code=404, detail="Unknown submission type")
    model, schema = _SUBMISSION_MODELS[kind]
    query = db.query(model)
    if status and hasattr(model, "status"):
        query = query.filter(model.status == status)
    items = query.order_by(model.id.desc()).all()
    return [schema.model_validate(item) for item in items]


@router.patch("/submissions/{kind}/{item_id}")
def update_submission_status(
    kind: str, item_id: int, payload: StatusUpdate, db: Session = Depends(get_db)
):
    if kind not in _SUBMISSION_MODELS:
        raise HTTPException(status_code=404, detail="Unknown submission type")
    model, schema = _SUBMISSION_MODELS[kind]
    if not hasattr(model, "status"):
        raise HTTPException(status_code=400, detail="This submission type has no status field")
    item = _get_or_404(db, model, item_id)
    item.status = payload.status
    if payload.show_on_wall is not None and hasattr(model, "show_on_wall"):
        item.show_on_wall = payload.show_on_wall
    db.commit()
    db.refresh(item)
    return schema.model_validate(item)


# ---------------- Reading plans (Bible reading progress feature) ----------------

@router.get("/reading-plans", response_model=list[ReadingPlanOut])
def list_reading_plans_admin(db: Session = Depends(get_db)):
    return db.query(ReadingPlan).order_by(ReadingPlan.created_at.desc()).all()


@router.post("/reading-plans", response_model=ReadingPlanOut, status_code=201)
def create_reading_plan(payload: ReadingPlanCreate, db: Session = Depends(get_db)):
    plan = ReadingPlan(**payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/reading-plans/{plan_id}", status_code=204)
def delete_reading_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = _get_or_404(db, ReadingPlan, plan_id)
    db.delete(plan)
    db.commit()


@router.post(
    "/reading-plans/{plan_id}/days", response_model=ReadingDayOut, status_code=201
)
def add_reading_day(plan_id: int, payload: ReadingDayCreate, db: Session = Depends(get_db)):
    _get_or_404(db, ReadingPlan, plan_id)  # 404s cleanly if the plan doesn't exist
    if (
        db.query(ReadingDay)
        .filter(ReadingDay.plan_id == plan_id, ReadingDay.day_number == payload.day_number)
        .first()
    ):
        raise HTTPException(status_code=409, detail="That day number already exists on this plan")

    day = ReadingDay(plan_id=plan_id, **payload.model_dump())
    db.add(day)
    db.commit()
    db.refresh(day)
    return day


@router.delete("/reading-days/{day_id}", status_code=204)
def delete_reading_day(day_id: int, db: Session = Depends(get_db)):
    day = _get_or_404(db, ReadingDay, day_id)
    db.delete(day)
    db.commit()


# ---------------- Image uploads ----------------

@router.post("/uploads")
async def upload_admin_image(file: UploadFile):
    data = await file.read()
    url = await upload_image(
        filename=file.filename or "upload.jpg",
        content_type=file.content_type or "application/octet-stream",
        data=data,
    )
    return {"url": url}


# ---------------- Admin user management (superadmin only) ----------------

@router.get("/users", response_model=list[AdminUserOut], dependencies=[Depends(get_current_superadmin)])
def list_admin_users(db: Session = Depends(get_db)):
    return db.query(AdminUser).order_by(AdminUser.created_at.asc()).all()


@router.post(
    "/users",
    response_model=AdminUserOut,
    status_code=201,
    dependencies=[Depends(get_current_superadmin)],
)
def create_admin_user(payload: AdminUserCreate, db: Session = Depends(get_db)):
    if db.query(AdminUser).filter(AdminUser.email == payload.email).first():
        raise HTTPException(status_code=409, detail="An admin with this email already exists")
    admin = AdminUser(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        is_superadmin=payload.is_superadmin,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@router.delete(
    "/users/{user_id}", status_code=204, dependencies=[Depends(get_current_superadmin)]
)
def deactivate_admin_user(user_id: int, db: Session = Depends(get_db)):
    admin = _get_or_404(db, AdminUser, user_id)
    admin.is_active = False
    db.commit()
