# Satu Muatan — Agent Notes

Sistem konsolidasi muatan & bukti mutu untuk rantai pasok hortikultura. FastAPI + SQLAlchemy 2 backend, React 18 + Vite + TypeScript + Tailwind frontend. Lomba IT Festival 2026 SV IPB.

## Authoritative sources

- `spek_satu_muatan.md` — source of truth.
- `KEPUTUSAN.md` — Fase 0 architect decisions that **override** the spec (numbers, schema, contract). Do not "fix" back to the spec.
- `CLAUDE.md` — hard rules and daily commands (read it first).
- `kontrak/` — frozen contract between modules: `openapi.yaml`, `skema.sql`, `types.ts`. Only modify via the `arsitek` agent.

## Hard rules (do not break)

1. **No hardcoded business constants.** All coefficients live in `konfigurasi` or `tier_kendaraan` tables, seedable from `backend/seed/seed.py`.
2. **`backend/app/domain/` must stay pure.** No DB imports, no I/O, no `datetime.now()`. Pass everything through parameters.
3. **Harga atap never changes** after a farmer joins. Farmers are never charged above their atap.
4. **Attribution must keep the `TIDAK_TERBUKTI` branch.** Never remove or simplify it.
5. **Never use the words** "tengkulak", "potong rantai distribusi", or "middleman" in UI, copy, comments, or commits.
6. **Mobile-first, 360 px.** Test UI from a phone view.
7. **Indonesian for domain identifiers, English for technical.**

## Local commands

```bash
# Database (Postgres 16 on host port 5433 — not 5432)
docker compose up -d

# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
python seed/seed.py            # idempotent master + 8 historical slots
python seed/skenario_demo.py   # reset to demo state, prints live cheat-sheet
uvicorn app.main:app --reload --port 8100

# Tests (pytest runs against a separate DB: satu_muatan_test on port 5433)
cd backend
pytest -v
pytest tests/test_harga_domain.py -v

# Frontend
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build    # tsc --noEmit && vite build
npm run test     # vitest run
```

> **Port 8100, not 8000.** Port 8000 is used by another local service. Use `127.0.0.1`, not `localhost`, on Windows to avoid IPv6 Docker stalls.

## Backend

- Entry: `backend/app/main.py`. Routers under `backend/app/routers/` are mounted with `/api` prefix.
- Health: `GET /healthz`.
- Config: `backend/app/config.py` reads `.env`. In production, env vars are injected by the platform; do not commit `.env`.
- DB: `backend/app/database.py` (SQLAlchemy 2, `DeclarativeBase`). Models live in `backend/app/models/`.
- Domain: pure functions in `backend/app/domain/` (armada, harga, atribusi, dampak). No DB, no I/O, no `datetime.now()`.
- Vendor adapter: `backend/app/adapters/` — `MOCK` (default, deterministic) and `DELIVEREE` (stub). Set via `VENDOR_ADAPTER`.
- Auth: JWT, PIN 6 digits. Demo login endpoint is active when `DEMO_MODE=true`.
- No lint/format/typecheck tools are configured (no ruff, black, prettier, eslint). Keep code clean and match existing style.

## Frontend

- Entry: `frontend/src/main.tsx`. Routing in `frontend/src/App.tsx`.
- State: Zustand (`frontend/src/stores/`). Server state: TanStack Query.
- API client: `frontend/src/api/client.ts`. `BASE_URL = import.meta.env.VITE_API_URL ?? ""`. Calls are already prefixed with `/api/...`.
- Vite dev proxy: `/api` → `http://127.0.0.1:8100`.
- PWA: `VitePWA` with `injectManifest` strategy (not `generateSW`), `src/sw.ts`. Precaches `woff2` fonts.
- Tailwind: 5-color palette only (`tanah`, `kertas`, `daun`, `tanah-liat`, `kabut`). Use opacity modifiers (`/5`, `/10`, `/20`, `/40`, `/60`, `/80`) for tones.
- Design system: minimum touch target 48 px, body base 16 px, custom font sizes `keterangan`, `subjudul`, `judul`, `display`.
- Mobile-first: layout max-width `max-w-md`, no heavy desktop chrome.
- Mock dev mode: `VITE_MOCK=1 npm run dev` activates `frontend/vite.mockApi.ts` for local UI-only development.

## Database / migrations

- Migrations: Alembic, `backend/alembic/`. `alembic upgrade head` runs migrations.
- `backend/alembic/env.py` loads `DATABASE_URL` from settings; never hardcode it in `alembic.ini`.
- Local DB: `postgresql+psycopg://satu_muatan:satu_muatan_dev@127.0.0.1:5433/satu_muatan` (note `psycopg` driver, not `psycopg2`).
- Production: Neon/Supabase connection string **must** use `postgresql+psycopg://` prefix.

## Tests

- Backend tests: `backend/tests/`. `conftest.py` sets `DATABASE_URL` to `satu_muatan_test` at module import time (before `app.config.get_settings()` is cached).
- Tests reset the schema once per session and truncate all tables before each test.
- Domain tests are independent of DB; API/integration tests need the Postgres container running.
- Run a single test: `pytest tests/test_harga_domain.py -v` or `pytest tests/test_api_auth.py::test_masuk_berhasil -v`.
- Frontend: `vitest` configured via `package.json` scripts. No test files exist yet.

## Deploy / env

- `render.yaml` — Render Blueprint for backend. Docker image from `backend/Dockerfile`. Entrypoint runs `alembic upgrade head` then uvicorn.
- `frontend/vercel.json` — SPA rewrites + Vite build. Deploy `frontend/` as root directory on Vercel.
- `VITE_API_URL` on Vercel must have **no trailing slash**.
- `CORS_ORIGINS` on Render: comma-separated, no spaces, no trailing slash, never `*` in production.
- `JWT_SECRET` is generated by Render (`generateValue: true`); do not set it in the blueprint.
- `DEMO_MODE` stays `true` during the competition so judges can use demo login.

## Repo conventions

- AI-related files (`spek_satu_muatan.md`, `CLAUDE.md`, `KEPUTUSAN.md`, `.claude/`, `proposal/`) are excluded via `.git/info/exclude`, not `.gitignore`. They must not be committed. Do not use `git add -f` on them.
- No AI trail in commit messages (no `Co-Authored-By`).
- `kontrak/` is frozen; only the `arsitek` agent may change it. Other agents must stop and report if they need contract changes.
- Worktrees (`../sm-domain`, `../sm-api`, etc.) may be used. Copy `CLAUDE.md`, `KEPUTUSAN.md`, and `spek_satu_muatan.md` from the main checkout before working there.

## Scope guard

Before adding any feature not in spec §9, read §12. If it is in §12, the answer is no. Time is the binding constraint.

## Framing

Frame the product as **logistics efficiency + quality transparency**, never as cutting middlemen.
