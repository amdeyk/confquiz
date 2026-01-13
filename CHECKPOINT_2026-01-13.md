# Checkpoint 2026-01-13 12:50:49

Purpose: capture the current system state after the screen-share quality audit.

Scope
- WebRTC presenter-to-display streaming with WebSocket signaling.
- No server-side media processing.
- Quality improvements already in place (direct track, higher bitrate, no downscaling).

Current behavior (screen share)
- Presenter uses getDisplayMedia and sends the raw video track (no canvas step).
- Frame rate is constrained by the selected FPS control (default 10).
- Encoder settings cap at 5 Mbps, maxFramerate set, and scaleResolutionDownBy = 1.0.
- SDP is modified to prefer VP9 when available.
- Display receives the track and renders it in the fullscreen video element.
- STUN server: stun.l.google.com:19302.

Key files
- templates/presenter_dashboard.html (capture, encoding parameters, SDP codec preference)
- templates/display.html (receiver and display mode switching)
- routers/ws_router.py (WebRTC signaling over WebSocket)

Restore instructions
- Extract `checkpoints/quiz_checkpoint_2026-01-13_125049.zip` to a clean folder.
- If you later enable git write access, you can add a commit/tag to mark this point.

Notes
- Git tagging/committing was not performed because the repo's `.git` directory is write-protected.
