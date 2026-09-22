"""Member-facing endpoints: registration/login, profile, Bible reading
plan progress, and certificates. Separate auth track from /admin — a
member JWT (type=member) cannot access admin routes and vice versa."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_member
from app.core.security import create_member_token, hash_password, verify_password
from app.db.session import get_db
from app.models.member import Member
from app.models.reading import Certificate, ReadingDay, ReadingPlan, ReadingProgress
from app.schemas.admin import Token
from app.schemas.member import MemberLogin, MemberOut, MemberRegister, MemberUpdate
from app.schemas.reading import (
    CertificateOut,
    MarkDayComplete,
    ReadingPlanOut,
    ReadingProgressOut,
)
from app.services.certificates import render_certificate_pdf

router = APIRouter(prefix="/members", tags=["members"])


# ---------------- Auth ----------------

@router.post("/register", response_model=Token, status_code=201)
def register(payload: MemberRegister, db: Session = Depends(get_db)):
    if db.query(Member).filter(Member.email == payload.email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    member = Member(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    token = create_member_token(subject=member.email)
    return Token(access_token=token)


@router.post("/login", response_model=Token)
def login(payload: MemberLogin, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.email == payload.email).first()
    if not member or not verify_password(payload.password, member.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not member.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_member_token(subject=member.email)
    return Token(access_token=token)


# ---------------- Profile ----------------

@router.get("/me", response_model=MemberOut)
def get_me(member: Member = Depends(get_current_member)):
    return member


@router.put("/me", response_model=MemberOut)
def update_me(
    payload: MemberUpdate,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    return member


# ---------------- Bible reading plans ----------------

@router.get("/reading-plans", response_model=list[ReadingPlanOut])
def list_reading_plans(db: Session = Depends(get_db)):
    return db.query(ReadingPlan).order_by(ReadingPlan.created_at.asc()).all()


@router.get("/me/reading-progress", response_model=list[ReadingProgressOut])
def get_my_progress(
    member: Member = Depends(get_current_member), db: Session = Depends(get_db)
):
    return (
        db.query(ReadingProgress).filter(ReadingProgress.member_id == member.id).all()
    )


@router.post("/me/reading-progress", response_model=ReadingProgressOut, status_code=201)
def mark_day_complete(
    payload: MarkDayComplete,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    day = db.query(ReadingDay).filter(ReadingDay.id == payload.reading_day_id).first()
    if not day:
        raise HTTPException(status_code=404, detail="Reading day not found")

    existing = (
        db.query(ReadingProgress)
        .filter(
            ReadingProgress.member_id == member.id,
            ReadingProgress.reading_day_id == day.id,
        )
        .first()
    )
    if existing:
        return existing

    progress = ReadingProgress(member_id=member.id, reading_day_id=day.id)
    db.add(progress)
    db.commit()
    db.refresh(progress)

    _maybe_issue_completion_certificate(db, member, day.plan_id)

    return progress


def _maybe_issue_completion_certificate(db: Session, member: Member, plan_id: int) -> None:
    """Auto-issues a certificate the moment a member finishes every day
    in a plan. Safe to call after every single day is marked — it no-ops
    if the plan isn't fully complete yet or a certificate already exists."""
    plan = db.query(ReadingPlan).filter(ReadingPlan.id == plan_id).first()
    if not plan or not plan.days:
        return

    completed_day_ids = {
        row.reading_day_id
        for row in db.query(ReadingProgress).filter(
            ReadingProgress.member_id == member.id,
            ReadingProgress.reading_day_id.in_([d.id for d in plan.days]),
        )
    }
    if len(completed_day_ids) < len(plan.days):
        return

    already_issued = (
        db.query(Certificate)
        .filter(Certificate.member_id == member.id, Certificate.plan_id == plan.id)
        .first()
    )
    if already_issued:
        return

    db.add(
        Certificate(
            member_id=member.id,
            plan_id=plan.id,
            title=f"{plan.title} — Completion Certificate",
        )
    )
    db.commit()


# ---------------- Certificates ----------------

@router.get("/me/certificates", response_model=list[CertificateOut])
def list_my_certificates(
    member: Member = Depends(get_current_member), db: Session = Depends(get_db)
):
    return db.query(Certificate).filter(Certificate.member_id == member.id).all()


@router.get("/me/certificates/{certificate_id}/pdf")
def download_certificate(
    certificate_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    certificate = (
        db.query(Certificate)
        .filter(Certificate.id == certificate_id, Certificate.member_id == member.id)
        .first()
    )
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")

    pdf_bytes = render_certificate_pdf(
        recipient_name=member.full_name or member.email,
        title=certificate.title,
        issued_date=certificate.issued_at.strftime("%B %d, %Y"),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="certificate-{certificate.id}.pdf"'
        },
    )
