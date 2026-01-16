# Change Document: LiveKit SFU Screen Share Upgrade

Date: 2026-01-13

## Summary

This upgrade replaces peer-to-peer screen sharing with LiveKit SFU fan-out, adds admin approval for protected/normal displays, enforces protected-display floors at the presenter, and introduces VPS bandwidth accounting with dashboard visibility.

## Update: 2026-01-16

- Protected display approvals are recommended, not required, before presenting.
- Presenter UI warns when fewer than 2 protected displays are approved.
- Quality guard treats zero protected displays as healthy (normal displays drive adaptation).
- LiveKit credential error now indicates required variables.
- Displays auto-approve as `normal` on join; admin can still promote to `protected`.
- Presenter heartbeat is broadcast to displays for faster reconnects.

## Architecture Changes

- Presenter publishes a single VP9 screen track to LiveKit.
- LiveKit SFU forwards to up to 5 displays without re-encoding.
- Displays join only after admin approval (protected/normal).
- Signaling, approvals, and dashboard remain in the existing FastAPI backend.

## Key Functional Changes

- Protected displays are explicitly approved and never trigger presenter quality reduction.
- Presenter encodes once with:
  - VP9 screen profile
  - 4 Mbps bitrate ceiling
  - 15 FPS ceiling
  - `contentHint = "detail"`
  - `degradationPreference = "maintain-resolution"`
  - L1T3 scalability
- Normal displays are allowed to influence reductions (within protected floors).
- Daily bandwidth usage is sampled on VPS and exposed in dashboard.

## New Endpoints

- `POST /api/admin/presenter/livekit-token`
  - Input: `{ "session_id": <int> }`
  - Requires presenter/admin role
  - Enforces minimum 2 protected displays before returning token
- `GET /api/admin/livekit/displays?session_id=<id>`
  - Admin list of pending/approved displays
- `POST /api/admin/livekit/displays/{display_id}/approve`
  - Input: `{ "session_id": <int>, "role": "protected" | "normal" }`
- `GET /api/admin/bandwidth/status`
  - Admin/presenter access for daily usage + thresholds

## New Environment Variables

Added to `.env.example`:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `LIVEKIT_TOKEN_TTL_SECONDS`
- `LIVEKIT_ROOM_PREFIX`
- `BANDWIDTH_MONITOR_ENABLED`
- `BANDWIDTH_INTERFACE`
- `BANDWIDTH_SAMPLE_INTERVAL_SECONDS`
- `BANDWIDTH_BUDGET_GB`
- `BANDWIDTH_WARN_GB`
- `BANDWIDTH_CRITICAL_GB`

## New Services / Files

- `services/livekit_tokens.py` (JWT token generation)
- `services/display_registry.py` (Redis-backed display registry)
- `services/bandwidth_monitor.py` (VPS NIC sampling)
- `LIVEKIT_VPS_SETUP.md` (systemd + VPS setup)
- `LIVEKIT_VPS_TEST_PLAN.md` (VPS-only validation checklist)

## Frontend Updates

- `templates/presenter_dashboard.html` now uses LiveKit client.
- `templates/display.html` subscribes via LiveKit after approval.
- `templates/admin_dashboard.html` adds display approval + LiveKit monitoring UI.
- LiveKit client is self-hosted at `/static/js/livekit-client.min.js` (UMD bundle).

## Redis Keys

- `display:registry:{session_id}` (display metadata/role/telemetry)
- `bandwidth:daily:{YYYY-MM-DD}` (bytes)
- `bandwidth:last_sample` (last counters)
- `bandwidth:minute:{YYYY-MM-DD}` (minute log)

## VPS Deployment Notes

LiveKit runs as a systemd service using the same Redis instance.

See: `LIVEKIT_VPS_SETUP.md`

## Testing (VPS Only)

1) Protected Display Immunity
   - 2 protected + 3 normal, induce loss
   - Confirm normal displays degrade first
   - Protected displays remain above 3.5 Mbps and 10 FPS

2) Bandwidth Ceiling
   - 4 Mbps @ 15 FPS to 5 displays
   - Validate ~12–13 GB/hour and <= 200 GB/day

3) Dashboard Accuracy
   - Compare dashboard total vs VPS NIC counters
   - Must match within ±3%

## Rollback

- Restore from `checkpoints/quiz_checkpoint_2026-01-13_125049.zip`
- Refer to `CHECKPOINT_2026-01-13.md` for snapshot details
