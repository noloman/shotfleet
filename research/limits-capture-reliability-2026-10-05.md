# Capture reliability: where a run can hang, flake, give wrong screenshots or leave a mess (2026-10-05)

DRAFT, committed early; the final version replaces it. Method: code reading of `shotfleet.py` (iOS `ios_run_inner`, Android `android_run`, `run_guarded`,
`make_pool`, `healthy_installs`, `collect_shots`, `capture_texts`, cleanup in `main_cmd`) plus device-free tests with stubs. No simulator, emulator or
Maestro was started (the device lock was held by another session: "WOD Tracker Play screenshots | retry tr,zh-TW").

## Top 3 findings (draft)

1. **A simulator that wedges while booting is left booted.** `make_pool` boots all n simulators, then waits on `bootstatus` one by one; a simulator is
   only added to `OUR_SIMS` (the cleanup list) after its own `bootstatus` and `status_bar` calls. A 900 s `bootstatus` timeout on sim 2 of 4 leaves sims
   2, 3 and 4 booted after shotfleet exits, because cleanup only shuts down `OUR_SIMS`.
2. **`run_guarded` can still block forever after it kills Maestro.** It reads Maestro's output through a pipe and `communicate()` waits for EOF, not for
   exit. Any process that inherited the pipe and is no longer a descendant (a daemonised helper, a reparented driver) keeps the call blocked after the
   kill, and the stall watchdog has no say any more.
3. **Terminal closed or ssh dropped (SIGHUP) skips all cleanup**; only SIGTERM and Ctrl-C are handled. Android cleanup also stops at the first adb
   call that times out, leaving the other emulators running.

(Per-step table, what is fixed, what remains and what needs devices: to follow in the final version.)
