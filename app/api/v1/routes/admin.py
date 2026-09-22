"""Everything behind the admin login: content CRUD, submission moderation,
and (superadmin-only) managing other admin accounts."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_superadmin
from app.core.security import hash_password
from app.db.session import get_db
from app.services.storage import upload_image
from app.models.admin import AdminUser
from app.models.event import Event
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
from app.schemas.admin import AdminUserCreate, AdminUserOut
from app.schemas.event import EventCreate, EventOut, EventUpdate
from app.schemas.partner import PartnerCreate, PartnerOut, PartnerUpdate
from app.schemas.testimony import TestimonyCreate, TestimonyOut, TestimonyUpdate
from app.schemas.submissions import (
    BibleClassOut,
    ContactOut,
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


# ---------------- Submission moderation ----------------
# Generic pattern: GET list (optionally filter by status) + PATCH status.

_SUBMISSION_MODELS = {
    "contact": (ContactSubmission, ContactOut),
    "prayer-requests": (PrayerRequest, PrayerRequestOut),
    "newsletter": (NewsletterSubscriber, NewsletterOut),
    "volunteer": (VolunteerApplication, VolunteerOut),
    "bible-class": (BibleClassEnrollment, BibleClassOut),
    "tribe-join": (TribeJoinRequest, TribeJoinOut),
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
    db.commit()
    db.refresh(item)
    return schema.model_validate(item)


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
