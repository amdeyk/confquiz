# Quiz System Plan, Schemas, and API Contract

Comprehensive plan for the FastAPI-based quiz system, including data schemas and REST/WebSocket contracts. This single document is intended to guide implementation end-to-end.

---

## 1. System Objectives

- Support Admin, Quiz Master, Team, and Main Screen operator roles with dedicated UIs optimized for laptop/mobile.
- Handle PPT/PPTX upload, conversion to PNG, explicit question → answer slide mapping, and optional native PPT playback where Office is installed.
- Provide per-slide and per-round timer presets, ad-hoc timers, and fastest-finger mode with reliable buzzer concurrency control.
- Offer configurable scoring presets per round, logging/undo, and scoreboard visibility tailored to each role.
- Operate completely offline over a local Wi-Fi router, keeping all assets/state on the host laptop.

---

## 2. Architecture & Module Plan

| Module | Responsibility |
| --- | --- |
| `auth` | OAuth2 for Admin/QM, token-based code login for teams, role-based guards. |
| `media` | PPT upload, conversion to PNG via LibreOffice/python-pptx, storage management, thumbnail generation. |
| `session` | Session lifecycle, deck registration, question-answer mapping, round configuration, snapshot endpoints. |
| `timer_service` | Redis-backed timer state machine, preset management, fastest-finger integration. |
| `buzzer_service` | WebSocket handlers, Redis Lua script for ordering, lock/unlock logic, event auditing. |
| `score_service` | Team totals, scoring presets, bonus/penalty handling, undo stack. |
| `ws_hub` | Manages WebSocket rooms per role, authentication, broadcast of state updates. |
| `ui_*` | Templates/JS/CSS for Admin, Quiz Master, Team, Main Screen. |
| `offline_tools` | Startup script for LAN IP discovery, QR code display, backup/export utilities. |

---

## 3. Data Schemas

### 3.1 SQL Tables (DDL-style summary)

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT CHECK(role IN ('admin', 'quiz_master')) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE teams (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  code TEXT UNIQUE NOT NULL,
  is_active BOOLEAN DEFAULT 1,
  seat_order INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  status TEXT CHECK(status IN ('draft', 'live', 'ended')) DEFAULT 'draft',
  banner_text TEXT DEFAULT 'AISMOC 2026 QUIZ',
  current_round_id INTEGER,
  current_slide_id INTEGER,
  mode TEXT CHECK(mode IN ('question', 'answer', 'native')) DEFAULT 'question',
  ppt_native_allowed BOOLEAN DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(current_round_id) REFERENCES rounds(id),
  FOREIGN KEY(current_slide_id) REFERENCES slides(id)
);

CREATE TABLE rounds (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  type TEXT CHECK(type IN ('normal', 'bonus', 'penalty', 'fastest')) NOT NULL,
  timer_default_ms INTEGER,
  scoring_presets JSON NOT NULL, -- e.g. {"positive":[10,20],"negative":[-5]}
  order_index INTEGER NOT NULL
);

CREATE TABLE decks (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  deck_type TEXT CHECK(deck_type IN ('question', 'answer')) NOT NULL,
  ppt_path TEXT NOT NULL,
  native_required BOOLEAN DEFAULT 0
);

CREATE TABLE slides (
  id INTEGER PRIMARY KEY,
  deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
  slide_index INTEGER NOT NULL,
  png_path TEXT NOT NULL,
  thumb_path TEXT NOT NULL,
  default_timer_ms INTEGER,
  UNIQUE(deck_id, slide_index)
);

CREATE TABLE slide_mappings (
  question_slide_id INTEGER UNIQUE NOT NULL REFERENCES slides(id) ON DELETE CASCADE,
  answer_slide_id INTEGER NOT NULL REFERENCES slides(id) ON DELETE CASCADE,
  answer_timer_override_ms INTEGER,
  PRIMARY KEY (question_slide_id)
);

CREATE TABLE team_sessions (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  starting_score INTEGER DEFAULT 0
);

CREATE TABLE scores (
  id INTEGER PRIMARY KEY,
  team_session_id INTEGER NOT NULL REFERENCES team_sessions(id) ON DELETE CASCADE,
  total INTEGER DEFAULT 0,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE score_events (
  id INTEGER PRIMARY KEY,
  team_session_id INTEGER NOT NULL REFERENCES team_sessions(id) ON DELETE CASCADE,
  round_id INTEGER NOT NULL REFERENCES rounds(id),
  actor_user_id INTEGER REFERENCES users(id),
  delta INTEGER NOT NULL,
  reason TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE buzzer_events (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  team_id INTEGER NOT NULL REFERENCES teams(id),
  device_id TEXT NOT NULL,
  placement INTEGER NOT NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_logs (
  id INTEGER PRIMARY KEY,
  actor_role TEXT,
  actor_id INTEGER,
  action TEXT NOT NULL,
  payload JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 Redis Keys

| Key | Type | Purpose |
| --- | --- | --- |
| `timer:{session_id}` | Hash (`state`, `start_epoch`, `duration_ms`, `remaining_ms`) | Authoritative timer state. |
| `timer:tick:{session_id}` | Pub/Sub channel | Broadcast timer ticks. |
| `buzzer:{session_id}` | Sorted set (`timestamp` as score, `team_id:device_id` as member) | Buzz order. |
| `buzzer:first:{session_id}` | String | Captures first buzz using `SETNX`. |
| `team:{team_id}:devices` | Set | Tracks active device tokens (max 2). |
| `ws:snapshot:{session_id}` | Hash | Cached current slide/round/mode for quick bootstrapping. |

---

## 4. API Contract

### 4.1 Authentication

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/api/auth/login` | None | Admin/QM login; body `{username,password}`. Returns `{access_token, role}`. |
| POST | `/api/teams/login` | None | Team login via `{code, nickname}`. Returns `{team_token, team_id, session_id}`; enforces max two connections. |

### 4.2 Session Management (Admin)

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/admin/sessions` | Create session `{name, banner_text?, ppt_native_allowed?}`. |
| GET | `/api/admin/sessions/{id}` | Retrieve session details incl. rounds, decks, mappings. |
| PATCH | `/api/admin/sessions/{id}` | Update status (`draft/live/ended`), banner text, native flag. |
| POST | `/api/admin/sessions/{id}/rounds` | Define rounds with order and scoring presets. |
| PUT | `/api/admin/sessions/{id}/rounds/{round_id}` | Update round settings/presets. |
| POST | `/api/admin/sessions/{id}/decks` | Upload PPT file; `deck_type` required. Returns deck + slide metadata. |
| POST | `/api/admin/sessions/{id}/mappings` | Submit slide mappings array `[{question_slide_id, answer_slide_id, answer_timer_override_ms}]`. |
| GET | `/api/admin/sessions/{id}/snapshot` | Admin view of live state (slides, timers, buzzers). |
| POST | `/api/admin/teams` | Create/update teams; body includes `code`, `name`, `seat_order`. |
| POST | `/api/admin/sessions/{id}/teams` | Attach teams to session (preload scoreboard). |
| POST | `/api/admin/sessions/{id}/controls/native-launch` | Mark session as using native PPT, deliver download link to QM. |
| POST | `/api/admin/sessions/{id}/flush` | Reset scores/buzzers (with confirmation). |

### 4.3 Quiz Master Controls

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/qm/sessions/live` | List sessions assigned/live. |
| POST | `/api/qm/sessions/{id}/slide/next` | Advance to next question slide (auto loads mapping). |
| POST | `/api/qm/sessions/{id}/slide/prev` | Go to previous slide. |
| POST | `/api/qm/sessions/{id}/slide/reveal` | Show answer slide (uses mapping). |
| POST | `/api/qm/sessions/{id}/slide/jump` | Jump to specific question or answer slide `{slide_id, mode}`. |
| POST | `/api/qm/sessions/{id}/mode` | Switch between `question`, `answer`, `native`. |
| POST | `/api/qm/sessions/{id}/timer/start` | `{duration_ms?, preset_id?, fastest_finger?}`; falls back to slide/round defaults. |
| POST | `/api/qm/sessions/{id}/timer/pause` | Pause timer. |
| POST | `/api/qm/sessions/{id}/timer/reset` | Reset timer to default. |
| POST | `/api/qm/sessions/{id}/buzzer/lock` | Lock/unlock buzzers. |
| POST | `/api/qm/sessions/{id}/scores/{team_id}` | Adjust score `{delta, reason?, round_id?}`. |
| POST | `/api/qm/sessions/{id}/scores/{team_id}/undo` | Undo latest score event for team. |

### 4.4 Team Client

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/team/sessions/current` | Returns assigned session snapshot. |
| POST | `/api/team/sessions/{id}/buzz` | Alternative to WebSocket buzz (fallback); includes device token. |

### 4.5 Main Screen

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/display/sessions/{id}/snapshot` | Fetch slide/scoring/timer state for initial render. |

### 4.6 WebSocket Channels

| Channel | Consumers | Events |
| --- | --- | --- |
| `/ws/admin/{session}` | Admin dashboard | `session.update`, `timer.update`, `buzzer.update`, `audit.event`. |
| `/ws/qm/{session}` | Quiz Master | `slide.update`, `timer.tick`, `score.update`, `buzzer.queue`, `round.update`. |
| `/ws/display/{session}` | Main Screen | `slide.update`, `timer.tick`, `score.update`, `indicator.update`, `buzzer.results`. |
| `/ws/team/{session}` | Team clients | `timer.tick`, `score.update` (limited), `buzzer.status`, `placement`. |

Event payload example (`timer.tick`):

```json
{
  "event": "timer.tick",
  "session_id": 12,
  "state": "counting",
  "remaining_ms": 18000,
  "mode": "fastest"
}
```

Event payload example (`buzzer.queue`):

```json
{
  "event": "buzzer.queue",
  "queue": [
    {"team_id": 3, "placement": 1, "timestamp": "2026-06-01T10:12:03.123Z"},
    {"team_id": 7, "placement": 2, "timestamp": "2026-06-01T10:12:03.140Z"}
  ],
  "locked": true
}
```

---

## 5. Implementation Roadmap (Reiterated)

1. Bootstrap FastAPI project, DB migrations, RBAC.  
2. Implement media pipeline + slide storage.  
3. Build Admin session wizard, including mapping UI and round configuration forms.  
4. Develop session snapshot + WebSocket infrastructure.  
5. Implement timer/buzzer services with Redis integration and Lua scripts.  
6. Create Quiz Master responsive interface with slide, scoring, timer, and native PPT controls.  
7. Deliver Team client UI with concurrency limits and buzzer feedback.  
8. Build Main Screen display with banner, scoreboard, and overlays.  
9. Add offline deployment helpers (LAN detection, QR).  
10. Conduct end-to-end testing, focusing on buzzer concurrency, timer drift, and reconnection behavior.

---

## 6. Outstanding Clarifications

1. Confirm baseline preset values for default rounds (currently configurable but UI needs initial seeds).  
2. Define exact visual treatment for scoring overlay on Main Screen (text bar vs modal).  
3. Decide whether theming (colors/logos) should be configurable per session beyond the current banner.  
4. Determine if audio cues (timer end, buzz confirmation) are required for Team/Main Screen clients.

Once clarified, these items can be incorporated into UI requirements and UX polish tasks.
