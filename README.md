# Glory Time Christian Center — Backend API

FastAPI + PostgreSQL + SQLAlchemy + Alembic + Redis. Serves the public content
(events, testimonies, partners) and the six form submissions (contact, prayer
request, newsletter, volunteer, Bible class, tribe join) that the Next.js
frontend already has UI for, plus a lightweight admin panel API for
moderation and content management.

## Local setup

1. Copy `.env.example` to `.env` and fill in real values (especially
   `SECRET_KEY` and the first superadmin credentials).
2. Start everything:
   ```bash
   docker compose up --build
   ```
3. Run migrations (first time, and after any model change):
   ```bash
   docker compose exec api alembic revision --autogenerate -m "init"
   docker compose exec api alembic upgrade head
   ```
4. Create the first superadmin:
   ```bash
   docker compose exec api python seed_admin.py
   ```
5. API is live at `http://localhost:8000`, interactive docs at
   `http://localhost:8000/docs`.

## Auth

`POST /api/v1/auth/login` with `username` (email) + `password` as form data
returns a JWT. Send it as `Authorization: Bearer <token>` on every
`/api/v1/admin/*` route.

## Endpoints at a glance

**Public (no auth)**
- `GET /api/v1/events`, `GET /api/v1/events/{slug}`
- `GET /api/v1/testimonies?featured_only=true`
- `GET /api/v1/partners`
- `POST /api/v1/contact`
- `POST /api/v1/prayer-requests`
- `POST /api/v1/newsletter`
- `POST /api/v1/volunteer`
- `POST /api/v1/bible-class`
- `POST /api/v1/tribe-join`

All public POST routes are rate-limited to 10 requests/minute/IP via Redis.

**Admin (JWT required)**
- Full CRUD: `/api/v1/admin/events`, `/api/v1/admin/testimonies`, `/api/v1/admin/partners`
- Moderation: `GET /api/v1/admin/submissions/{kind}`,
  `PATCH /api/v1/admin/submissions/{kind}/{id}` — `kind` is one of
  `contact`, `prayer-requests`, `newsletter`, `volunteer`, `bible-class`, `tribe-join`
- Admin user management (superadmin only):
  `GET/POST /api/v1/admin/users`, `DELETE /api/v1/admin/users/{id}` (deactivates)

## What's not built yet (Phase 3 — member portal)

Auth for regular members, Glory Connect video conferencing, giving history,
Bible reading progress, certificates, and the event registration dashboard.
Those all live behind login per the site's build spec and are a separate
scoping conversation — this repo only covers the public site + admin panel.
