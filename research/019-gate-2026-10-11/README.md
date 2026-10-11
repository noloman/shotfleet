# 0.1.9 release gate, 2026-10-11 (signed, notarized build from a444c3a)

Three gate runs of the full fixture e2e (iPhone, iPad, Android; iOS pinned to 26.4; Maestro 2.0.10). Only the third counts.

1. g3-019-run1-android-assertions-skipped.log (13:53-14:09): printed "PASS: all 49 assertions", but the 16 Android "assertions on the output" never ran. python3 on the job's PATH was Xcode's 3.9 and the helper said "shotfleet needs Python 3.11 or newer". My mistake, not a shotfleet fault. Not a full pass.
2. g3-019b-gate-run2-thrash-FAIL.log (14:58-15:20): the four iOS simulators stopped answering (`simctl uninstall` timed out) with swap at 18 to 20 GB and the load at 400 to 700; 0 of 4 iOS languages captured, 19 of 65 assertions failed. Memory thrash on the Mac, not shotfleet.
3. g3-019c-gate-PASS.log (15:36-16:07, 31 min 37 s): PASS, all 65 assertions, 0 FAIL, including the Android output assertions (python@3.14 first on PATH).

g3-019-maestro2110.log: the Maestro 2.11.0 legs from the first job, 14:09-14:27: Android 30 of 30, iOS 36 of 36. They ran with the same signed build and had all their assertions.
proofs.out: non-device proofs on the shipped files. Proof F runs `check`, `run` and `init` on a fake React Native iOS app and APK with the 0.1.8 and the 0.1.9 binary: `init` exits 0 on 0.1.8 and 2 on 0.1.9; `check` exits 2 on both (0.1.8 already did that for these two); `run` stopped at "Maestro isn't installed" on this Mac before the strings check, so the `run` change is proven by the unit tests (C420) only. No device was used.
tar.gz sha256 f9544f32dea13273c0e01dc231af11b62518b8089625beefee379af944ccbbbd, pkg 2061fab2030488bce7fbee27619918fea615ea63e80964655ad626697fcafb7b (sha256.txt, verify.out: 12 checks, 0 failed).
The `claude -p` half of the MCP client test did not run (the claude CLI was logged out); the raw stdio half passed.
