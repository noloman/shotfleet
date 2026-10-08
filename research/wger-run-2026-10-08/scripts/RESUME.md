# RESUME (showcase-wger builds, device-free)
State is in progress.log (timestamps). Order: ANDROID (pub get + apk --debug), then iOS (simulator --debug), one at a time.
Scripts: chain-android.sh, chain-ios.sh (own files only). Logs: logs/. Results: android.result / ios.result ("<status> <wall s>").
Own process group pid: android.pid / ios.pid (setpgrp, perl alarm 3600). Stop only that group if needed: kill -TERM -<pid>.
Foreign java pids before the build: java-pids.before (do NOT touch them).
Artifacts: src/build/... ; copies to app/ ; record in ARTIFACTS.txt. Do not clean src/build until the coordinator says so.

## iPhone device job (2026-10-08, OCR session) -- RESUME
Script: chain-iphone.sh (detached, caffeinate -i). Status file: chain-iphone.status (waiting | idle | running NAME | released | gaveup). State: progress.log.
Waits for the start rule (lock free, earlier queue lines DONE, quiet check x3), takes /tmp/shotfleet-devices.lock, then runs commands written to showcase-wger/cmd: "run NAME LOCALES" or "release". Last run result: last.result.
Hard limits inside the script: 30 min per run (perl alarm), 10 min no progress -> kills ONLY its own run group, 75 min hold, 25 min idle -> release. Trap releases the lock, shuts down pool sims it booted, replaces my queue line with DONE.
Outputs: out-iphone-dry, out-iphone-run1..3 (failed attempts: out-*-failed-*). Logs: logs/. Do NOT touch the Android queue line.
