# Sharing this Mac's simulators and emulators between agent sessions

Many Claude sessions run shotfleet jobs on one Mac. Two jobs at once (load 600-1000, free memory near zero) made simulators hang and voided runs, and
shotfleet's pool simulators share names (`shotfleet-<device>-N`), so two runs of the same device type steal each other's simulators. The rule that worked on
2026-10-03/05:

1. **One device job at a time.** Take the lock before booting any iOS simulator or Android emulator (also `fixture-e2e.sh`, `shotfleet run`, `maestro`):
   `mkdir /tmp/shotfleet-devices.lock && echo "<session> | <what> | <started HH:MM> | est. <N> min" > /tmp/shotfleet-devices.lock/holder`.
   If `mkdir` fails, someone holds it: do non-device work and queue a line in `/tmp/shotfleet-device-queue.md`.
2. **Release it** (`rm -rf /tmp/shotfleet-devices.lock`) when your own simulators and emulators are shut down.
3. **Hard time limit** on every run script and waiter (kill only your own PIDs). A waiter without one held the lock for 8 hours.
4. **Never kill or delete what you have not proven is yours** (process cwd, parent chain, or a log naming the folder). A stale lock (older than 2 h, no live
   process) is reported to the queue owner, not broken.
5. **Quiet check before starting:** free memory at least 20 percent, load under 300, and no other emulator on ports 57xx. A job that needs another disk floor says so
   in the queue file. Jobs that share no device names or ports with a running job (an iOS job beside an Android-only one) may run in parallel with the owner's OK.
6. **Do not change the machine-wide default** while others are queued: importing an iOS runtime makes `latest_ios_runtime()` pick it for every run.

The queue file and lock live in `/tmp`, so they do not survive a restart: pollers die with their sessions; re-arm them.
