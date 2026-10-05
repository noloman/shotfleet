# First-run limits: from `curl | sh` to the first screenshot (2026-10-05)

Question: how long and how painful is it for a developer who has Xcode and nothing else? Method: the live installer
(`https://shotfleet.com/install.sh`, program 0.1.0) patched to install into a throwaway HOME only, then every device-free command
from that HOME with `env -i` and a bare PATH. No simulator, emulator, Maestro run or `doctor --fix` was started. The machine is shared
and was busy, so timings that involve macOS text recognition are worst cases, not typical ones.

## Top 3 findings

1. **A plain `shotfleet doctor` offered the 600 MB download plan.** In `cmd_doctor` the loop that prints each check reused the name
   `fix`, so the `--fix` flag was always true afterwards. Every `doctor` therefore ended with "doctor --fix would do 4 thing(s)" and,
   on a terminal, asked "Run these 4? [y/N]". Seen on the live 0.1.0 program from a clean HOME. This is the command the installer and
   README tell every buyer to run second. A buyer who answers y is downloading Maestro (300 MB) and Google's tools before reading
   anything; one who answers n sees "nothing was run" and may think doctor failed. Fixed (commit 1 below).
2. **`doctor` takes 62 to 68 s on a first run and looks hung.** It waits up to 60 s for the text-recognition model to compile and then
   says "slow to start". Run four times from the same clean HOME on a busy Mac it hit the 60 s limit every time, and a direct
   `ocr --warmup` took 75 s, so the doctor wait gave up before the compile could finish. Whether the cache is kept when the wait kills
   the helper is not known (needs a quiet Mac, see the last section). Not fixed: removing the wait changes what `check` promises.
3. **The order and text pushed a Xcode-only buyer toward the wrong things.** Install said "next: doctor, then activate"; the README
   says activate, doctor, init, and its heading says "once Maestro and a simulator build exist", while `doctor --fix` is what fetches
   Maestro. An iOS-only buyer saw a block of Android SDK commands with a `brew` line that fails without Homebrew. The Java line named
   only `brew install`. Fixed in the text (commits 2, 4), README proposal below.

## The walk, with times (clean HOME, Apple silicon, Xcode installed)

| Step | Command | Time | What the buyer sees |
|---|---|---|---|
| 1 | `curl ... install.sh \| sh` | 5 s | Installs 0.1.0 (22 MB) to `~/.local/bin` when neither Homebrew folder nor `/usr/local/bin` is writable. Prints an `export PATH` line for `~/.zshrc`. The current shell still says "command not found" until a new Terminal window is opened; the old text did not say so. |
| 2 | `shotfleet --version` | 1 s | `shotfleet 0.1.0`. The live program is one release behind the repo (0.1.1), so no fix made today is live until the next release and a site deploy of `install.sh`. |
| 3 | `shotfleet doctor` | 62 to 68 s | Maestro MISSING, Android lines MISSING, then the unwanted fix plan (finding 1). Java, Xcode runtime and swiftc showed ok only because this Mac has Homebrew's JDK; a truly bare Mac would also fail Java. |
| 4 | `shotfleet doctor` with Xcode installed but `xcode-select` on the Command Line Tools | 62 s | "MISSING xcrun simctl -> install Xcode and an iOS Simulator runtime". Wrong advice: Xcode is there, it is not selected. Fixed (commit 3). |
| 5 | `shotfleet init` in an empty folder | 1 s | Exit 2 with the `xcodebuild` and `gradlew` commands. Good. With a bare `.xcodeproj` and no shared scheme it printed `-scheme '<scheme>'` with no explanation. Fixed (commit 6). |
| 6 | `shotfleet init <fixture .app>` | 0 s | Writes `shotfleet.toml` and `flow.yaml`, lists 5 languages, says what `run` will do. Did not mention that Maestro is missing. Fixed (commit 5). |
| 7 | `shotfleet run --locales en` | 0 s | Prints the licence note, then "Maestro isn't installed. Run shotfleet doctor --fix". Clear, but it is the third place the buyer learns this. |
| 8 | `shotfleet activate mykey` / a well-formed wrong key | 1 s | Both refuse in one line with the receipt-email hint and the buy URL. Good. `activate --help` said nothing about the key or the network; fixed (commit 7). |
| 9 | `shotfleet check <folder>` (no `--app`) | 79 s, exit 2 | "macOS text recognition isn't answering (ANECompilerService is stuck)". Under heavy load on this Mac; the message is accurate and offers Tesseract. A new buyer on a quiet Mac should not see it, but nobody has timed that. |

Not walked (needs a device or a 600 MB download): `doctor --fix`, the first `run`, simulator boot, Maestro driver start.

## What the whole path costs a new buyer (estimate, partly measured)

- Install 5 s (measured). `doctor` 1 minute (measured, busy Mac).
- `doctor --fix`: Maestro 300 MB and Java about 50 MB from the plan text; Android is skippable for iOS buyers. Time unmeasured.
- Building the app in Debug for the simulator: the buyer's own project, minutes to tens of minutes the first time.
- First `run --locales en`: a simulator boot plus Maestro driver start, "a few minutes" in the code, never timed from a clean Mac.
- Licence key: the buyer must buy first; the key arrives by email. `check` and two-language `run` work without one.

## Friction ranked by refund risk

1. **Doctor offers the big download unprompted (finding 1).** High: it looks like the tool is installing things behind the back. Fixed.
2. **No Maestro, and the buyer finds out late.** High: the README quickstart header assumes Maestro exists; `init` happily succeeds;
   `run` then fails. Now `init` and `doctor` both point to `doctor --fix`. Fixed in wording; the README is still to change.
3. **Xcode not selected or licence not accepted.** High for Xcode-only buyers: a fresh Xcode needs `sudo xcode-select -s` and
   `sudo xcodebuild -license accept` / first-launch components. Doctor now names the right Xcode; it still cannot tell an unaccepted
   licence from other simctl failures. Partly fixed.
4. **The 60 s silent-looking doctor and the first text-recognition compile (finding 2).** Medium: looks hung, then shows "slow to start".
5. **Debug simulator build must already exist, and `<scheme>` was unexplained.** Medium. Explained now; `init --build` does not exist
   (research/setup-friction.md section 2).
6. **PATH after the installer.** Medium: the first `shotfleet doctor` in the same Terminal window fails with "command not found". The
   installer text now says to open a new window. A fix in the installer's own shell cannot change the parent shell.
7. **The program on the site is 0.1.0 and has finding 1.** Medium until the next release is built and `install.sh` redeployed.
8. **Android lines for an iOS-only buyer.** Low to medium: doctor now prints "iOS still needs" and "Android still needs" separately and
   marks the Android block as skippable.

## What was fixed (one commit each, device-free tests in `tests/test_limits_first_run.py` and `tests/test_doctor_fix.py`)

1. doctor no longer offers the fix plan unless `--fix` is given (rename of the loop variable; regression test fails on the old code).
2. `install.sh`: PATH line says to open a new Terminal window; the next-step line is doctor (with `--fix`), then init, then activate.
3. doctor: Xcode installed but not selected gets `sudo xcode-select -s <path>` and the licence command instead of "install Xcode".
4. doctor: "iOS still needs: ..." and "Android still needs: ..." lines; Java line offers `doctor --fix` first; no-Homebrew note under the Android block; final `next:` names `--fix`.
5. init: prints a note when Maestro is missing, before the `next:` line.
6. init: explains `<scheme>` when the project has no shared scheme on disk.
7. `activate --help`: says where the key is and that activation needs internet once.

`shotfleet.py` hunks are small on purpose (other branches touch the same file); commit 1 and 4 touch `cmd_doctor`, 3 adds `xcode_hint`.

## Not fixed, on purpose

- The 60 s doctor wait: needs a quiet-Mac measurement first, then either a shorter wait with a "run `shotfleet check` once to finish it" line or a background start.
- An unaccepted Xcode licence cannot be told apart from other simctl failures without running `xcodebuild`.
- `doctor --fix` on a real Mac (the README says so itself).
- The README quickstart (below). Changing it also changes site claims tests, so it is proposed, not applied.

## What needs a real clean Mac or an outside tester

A tester with an Apple silicon Mac that has Xcode installed from the App Store and no Homebrew, no Java, no Maestro, no Android Studio
(a new user account on a Mac, or a fresh macOS VM with Xcode, works). Give them only the Gumroad receipt and the site. Record, with a
stopwatch and screen recording, every step: time from the install line to `shotfleet --version` working in the same window (expect
"command not found" for the first try); time and output of the first `shotfleet doctor` (does it ask anything, how long); whether
`xcode-select -p` points at Xcode; whether `doctor --fix --yes` completes and how long the 350 MB take; time from `init` to the first
PNG in `out/`; every point where they stopped, searched or asked for help; whether they ever saw a macOS dialog (Java stub,
"Apple could not verify", Xcode licence, "install developer tools"). Also record the first text-recognition compile time on a quiet
Mac (`time ocr --warmup` inside the app folder, then `shotfleet doctor` twice) and whether the second `doctor` is fast. Ask them what
they thought `doctor` was doing. Then repeat once with Homebrew installed. Two testers are enough to find the common walls.

## Proposed README Quickstart

The current one starts "once Maestro and a simulator build exist" and puts `activate` before `doctor`. Proposed:

```bash
curl -fsSL https://shotfleet.com/install.sh | sh   # then open a new Terminal window
shotfleet doctor --fix        # shows what is missing, asks once, fetches Maestro and Java (about 350 MB)
cd path/to/MyApp              # your project; build it once for the simulator in Xcode (Debug) first
shotfleet init                # finds the Debug simulator build, writes shotfleet.toml and flow.yaml
shotfleet run --locales en    # first run takes a few minutes: it boots a simulator
shotfleet activate <key>      # from your Gumroad receipt (2 languages and `check` work without one)
shotfleet run                 # every language
```

Notes to add: Xcode must be the selected one (`xcode-select -p`); the Android block of `doctor` can be ignored by iOS-only apps; the
first `doctor` can take a minute while macOS prepares text recognition.

## Unverified

- All timings involving text recognition (a loaded shared Mac).
- That `doctor --fix` works end to end on a Mac, and how long it takes.
- What a Mac with the real `/usr/bin/java` stub and no JDK shows for the Java line (this Mac has Homebrew's JDK).
- Anything from the first `run` onward on a clean Mac.
