# T_1 state

Generated: 2026-02-14 11:32:35 +05:30
Repository: D:/quiz

## 1) Git Snapshot

- Branch: `main`
- Remote tracking: `origin/main`
- Local vs remote divergence: `0 behind, 0 ahead`
- Working tree: clean (no uncommitted changes)
- Current HEAD: `b649863c9d116fa73918febc049240873ed496a6`
- HEAD message: `quiz buzzer update` (2026-02-11)
- Root commit: `5671fd64f0a796fe9d3e9231ecba13963cbb85d1` (`first commit`, 2025-12-31)
- Total commits in repo: `42`

This file documents the exact project state represented by commit `b649863`.

## 2) Current Application State

The project is a FastAPI-based real-time quiz platform with role-based flows for:
- Admin
- Quiz Master
- Team participants
- Main display
- Presenter (screen share)

Entry point and routing:
- App entry: `main.py`
- Routers mounted: `auth`, `admin`, `media`, `qm`, `team`, `display`, `ws`
- Main interfaces available in templates under `templates/`

Core runtime dependencies include:
- FastAPI/Uvicorn
- SQLAlchemy + Alembic + aiosqlite
- Redis/aioredis for buzzer/timer realtime coordination
- WebSockets + Jinja templates
- PPT/media stack (`python-pptx`, `pdf2image`, `Pillow`)

## 3) Change Timeline (High-Level)

- 2025-12-31: initial repo bootstrap (`first commit`)
- 2026-01-02 to 2026-01-04: presenter/screen-share and heartbeat-related development
- 2026-01-09: timer/buzzer performance and blocking fixes
- 2026-01-13: display/livekit related updates
- 2026-01-16: display/admin iterative updates and patches
- 2026-02-11: latest buzzer behavior changes (`quiz buzzer update`)

Latest change set (`b649863`) modified:
- `routers/qm_router.py`
- `routers/team_router.py`
- `routers/ws_router.py`
- `templates/qm_dashboard.html`
- `templates/team_interface.html`
- `CHANGELOG_CONSOLIDATED.md`

From `CHANGELOG_CONSOLIDATED.md` (2026-02-11):
- Team UI simplified around buzzer flow
- Digit keys `1-9` can trigger buzzer (when unlocked)
- Buzzer lock changed to 1-second auto-expiring cooldown
- QM controls updated for cooldown/clear queue behavior

## 4) Most Frequently Touched Files (History Signal)

Top files by commit touch-count:
- `routers/ws_router.py` (14)
- `templates/presenter_dashboard.html` (14)
- `templates/display.html` (13)
- `templates/admin_dashboard.html` (11)
- `routers/admin_router.py` (10)
- `templates/qm_dashboard.html` (8)
- `routers/qm_router.py` (7)
- `templates/team_interface.html` (6)
- `main.py` (5)

This indicates active churn mainly in realtime signaling, display/presenter UI, and admin/QM control surfaces.

## 5) Related State Artifacts Already Present

- Existing checkpoint archive: `checkpoints/quiz_checkpoint_2026-01-13_125049.zip`
- Existing docs: `PROJECT_SUMMARY.md`, `CHANGELOG_CONSOLIDATED.md`, `STATUS.md`, `LATEST_FIXES.md`

## 6) Revert / Restore Guidance

To keep this exact state as a durable reference point:

```bash
git tag -a T_1_state b649863 -m "T_1 state snapshot"
git push origin T_1_state
```

To restore local code to this exact snapshot later (destructive to uncommitted work):

```bash
git checkout main
git reset --hard b649863c9d116fa73918febc049240873ed496a6
```

Non-destructive alternative (recommended for review/testing):

```bash
git checkout -b restore/T_1_state b649863c9d116fa73918febc049240873ed496a6
```

---

Snapshot ID: `T_1 state`
