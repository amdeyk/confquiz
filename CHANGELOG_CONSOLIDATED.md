# Consolidated Change Log

## 2026-02-14

### Main Display - Presenter View Disabled and Left Rail Layout
- Disabled presenter/screen-share rendering on the main display page.
- Forced display mode handling on main display to stay `png_slides` (screen-share view ignored on this page).
- Kept timer, score table, and buzzer queue update flows unchanged.
- Changed display layout so the status panel is on the **left** and constrained to **18%** width.
- Main display area now stays blank and white for the remaining **82%** of width.
- Set main display background to pure white.

Files changed:
- templates/display.html

### Main Display - Left Rail Density Update
- Moved the buzzer queue card above the score card so buzzer updates appear higher on the screen.
- Reduced spacing/font sizes in the left rail to improve visibility for larger lists.
- Updated left rail card sizing so both sections can better show up to 9 teams and up to 9 buzzer entries.
- Kept all buzzer/score/timer update functionality unchanged.

Files changed:
- templates/display.html

### Main Display - Panel Order Adjustment
- Restored left rail order to: Timer -> Scores -> Buzzer Queue.
- Kept compact/dense styling improvements from the previous update.

Files changed:
- templates/display.html

## 2026-02-11

### Team Interface - Buzzer Round Keypad
- Removed help, timer, score, and on-screen buzzer controls from the team interface.
- Added a read-only current round button (label populated once from the display snapshot).
- Added physical keypad capture: any key 1-9 triggers the buzzer when buzzers are unlocked.
- Buzzer availability is driven by the existing buzzer lock/unlock state.
- No backend heartbeat or buzzer logic changes.
- Team count: no UI limits; verified flow supports 8 teams (queue placement displays correctly).

### Buzzer Auto-Unlock (No QM Unlock Required)
- Buzzer lock now auto-expires after 1 second to remove manual unlock requirements.
- Team and HTTP buzz endpoints enforce a 1-second cooldown using the lock key.
- QM lock endpoint sets a 1-second lock (no persistent lock); unlock still clears the queue.
- Team UI status reflects cooldown state.
- QM dashboard buzzer button now triggers a 1-second cooldown and Clear Queue explicitly clears the server queue.

Files changed:
- templates/team_interface.html
- routers/ws_router.py
- routers/team_router.py
- routers/qm_router.py
- templates/qm_dashboard.html

Test notes:
- Lock buzzers -> keypress ignored, status shows waiting.
- Unlock buzzers -> press any digit 1-9, buzz registers.
- Confirmed placement display updates and clears on queue clear.
