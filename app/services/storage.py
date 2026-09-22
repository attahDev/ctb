"""Image uploads via Supabase Storage's REST API. Deliberately avoids the
full supabase-py SDK (which pulls in postgrest, gotrue, realtime, etc.) —
a plain httpx call is all a single "upload a file, get a public URL back"
endpoint needs."""

import uuid
from pathlib import Path

import httpx
from fastapi import HTTPException

from app.core.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


async def upload_image(filename: str, content_type: str, data: bytes) -> str:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=503,
            detail="Image uploads aren't configured yet (missing Supabase credentials).",
        )

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image type. Use JPEG, PNG, WEBP, or GIF.",
        )

    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Image must be under 5 MB.")

    ext = Path(filename).suffix or ".jpg"
    object_path = f"uploads/{uuid.uuid4().hex}{ext}"

    upload_url = (
        f"{settings.supabase_url}/storage/v1/object/"
        f"{settings.supabase_bucket}/{object_path}"
    )

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            upload_url,
            headers={
                "Authorization": f"Bearer {settings.supabase_service_role_key}",
                "apikey": settings.supabase_service_role_key,
                "Content-Type": content_type,
                "x-upsert": "false",
            },
            content=data,
        )

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=502,
            detail=f"Image upload failed: {response.text[:200]}",
        )

    return (
        f"{settings.supabase_url}/storage/v1/object/public/"
        f"{settings.supabase_bucket}/{object_path}"
    )
