from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.admin import AdminUser
from app.models.member import Member

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
member_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/members/login", auto_error=False)


def get_current_admin(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> AdminUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None or payload.get("type") != "admin":
        raise credentials_error

    admin = db.query(AdminUser).filter(AdminUser.email == payload.get("sub")).first()
    if admin is None or not admin.is_active:
        raise credentials_error
    return admin


def get_current_superadmin(admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
    if not admin.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privileges required",
        )
    return admin


def get_current_member(
    token: str | None = Depends(member_oauth2_scheme), db: Session = Depends(get_db)
) -> Member:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_error

    payload = decode_access_token(token)
    if payload is None or payload.get("type") != "member":
        raise credentials_error

    member = db.query(Member).filter(Member.email == payload.get("sub")).first()
    if member is None or not member.is_active:
        raise credentials_error
    return member
