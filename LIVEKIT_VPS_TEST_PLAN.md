# LiveKit SFU VPS Test Plan

All execution must run on the VPS only.

## Test 1: Protected Display Immunity

Goal: Protected displays never degrade when normal displays are under pressure.

Steps:
1. Approve 2 displays as `protected` and 3 as `normal`.
2. Start presenter screen share (VP9, 4 Mbps, 15 FPS cap).
3. Induce packet loss or bandwidth pressure for normal displays only.
4. Verify:
   - Normal displays show reduced FPS/bitrate first.
   - Protected displays remain >= 3.5 Mbps and >= 10 FPS.

## Test 2: Bandwidth Ceiling

Goal: Validate daily budget math and bitrate ceiling.

Steps:
1. Run 5 displays with presenter at 4 Mbps / 15 FPS.
2. Record egress for 1 hour.
3. Verify:
   - ~12–13 GB/hour total usage.
   - Extrapolated <= 200 GB/day.

## Test 3: Dashboard Accuracy

Goal: Dashboard matches VPS counters.

Steps:
1. Capture VPS NIC counters at start/end (RX+TX).
2. Compare to dashboard daily totals.
3. Validate within ±3%.
