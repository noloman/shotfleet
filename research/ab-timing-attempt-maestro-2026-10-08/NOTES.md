# Same-build timing A/B, Maestro 2.0.10 vs 2.11.0: attempt of 2026-10-08, stopped, no result

Plan: Crossfit Tracker 1.6.7 (iOS build 58, the WOD Tracker showcase build and flows), shotfleet from origin/main cf43aa6, all 19 languages, iPhone 17 Pro Max on iOS 26.4, then the Android phone AVD, each on Maestro 2.0.10 and 2.11.0 (order flipped per platform), to see whether 2.11.0 changes the home-page numbers (9 minutes on iOS, 15 on Android, measured on 2.0.10 with app 1.6.2). `job-a.py` is the job, `waiter-a.py` the waiter with its start gate (lock free, not actively swapping, load < 100, free memory >= 40 %, pressure <= 2, disk >= 15 GB).

What happened (device lock held 14:26 to 14:50):

| Run | Start conditions | Result |
|---|---|---|
| iOS, 2.0.10, 4 simulators | load 20, pressure 1, swap 13.7 of 14.3 GB used (96 %) | shotfleet warned "very busy (swap is 96% full)"; all 4 simulators stopped answering at `simctl uninstall` (60 s); 0/19 captured, 544 s; load rose to 614 |
| iOS, 2.11.0, 4 simulators | load 479, swap 16.2 of 17.4 GB used | 4 simulators replaced ("stopped answering last run"); no capture line after 13 minutes; stopped by me at 14:50 (SIGINT to the job, SIGTERM to the run, `logs/`, `job.log`) |
| Android | not started | n/a |

Conclusion: the failure is the host (swap full, same as the 0.1.6 gate of 2026-10-07 on 2.0.10 and the first iPad attempt on 2.11.0 the same day), not the Maestro version, so there is no timing comparison. The home-page line stays "measured on Maestro 2.0.10"; the fixture runs of 2026-10-07 (`research/maestro-2-11-0.1.6-2026-10-07/`) show that 2.11.0 works. `summary.json` holds the first run only (the job was interrupted before the second was recorded).

Lesson for the start gate: "not actively swapping" and low load are true just before four simulators boot, then the swap-full host collapses. Add "swap used < 70 % of total" (the coordinator adds it to the 0.1.8 gate rule), or boot fewer devices (`--parallel 2`).
