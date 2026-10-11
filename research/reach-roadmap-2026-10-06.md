# Reach roadmap: who can't use shotfleet, and the cheapest way to let them (2026-10-06)

Owner's goal: "investigate how we can overcome any limitations and make shotfleet a project that can be used by as many people as
possible". This is research and a plan. Nothing was built, and nothing was published or posted. No simulator, emulator or device lock was
used, and nothing was killed. Branch `claude/reach-roadmap` from `origin/main` (03b3271).

Tags: **[M]** measured here today (command and output in "Measurements"); **[R]** read in the repo (file named); **[W]** read on the web
today (URL in Sources); **INFERENCE** = my estimate, with the test that would settle it. Market numbers are rough. Each one says how rough.

This note builds on these notes and doesn't repeat them: `research/limits-platform-reach-2026-10-05.md` (older macOS, Intel, Linux arm64),
`research/workarounds-reach-distribution-2026-10-05.md` (tap, Action, Intel, Linux packaging), `research/vm-older-macos-results-2026-10-05.md`
(branch `claude/vm-older-macos-results`), `research/beyond-maestro-2026-10-06.md` (branch `claude/beyond-maestro-research`: fastlane,
Paparazzi and BYOC), `research/website-localization.md`, `research/web-service.md`, `research/strategy-roadmap-2026-10-05.md`,
`research/gumroad-setup.md`, `research/frameworks.md`, `docs/linux.md` and `docs/compat.md`.

## Short answer

shotfleet is really two products with very different reach:

- **`check` is portable already.** It is stdlib Python plus an OCR engine. On Linux it uses Tesseract, which works today from source
  [R `docs/linux.md`]. Today I re-ran it the way a Linux user gets it (macOS text recognition switched off, Tesseract only) on a real
  18-language Android set of 72 screenshots. With the APK passed (`--app`), it gave the same verdict as macOS: 0 problems on the
  clean set, and all 3 planted faults caught (an English screen in `de/`, a copied image, a missing `ja` screen) [M]. **What a Linux
  user is missing is not capability. It is a way to install it**: no Linux build is published, the source is private, and the CI recipe in the README
  needs a macOS runner, which costs 10 times as much as a Linux runner [W GitHub pricing].
- **`run` is tied to macOS for iOS (that is Apple's rule, and it is permanent) and to Maestro.** Android `run` on Linux passed the fixture once,
  with one emulator [R `docs/linux.md`]. Reaching more people with `run` costs days and device experiments. Reaching more people with
  `check` costs hours.

So the plan is to make the free `check` usable by everyone, everywhere, in the form they already use (a Docker image, a CI step,
Homebrew, a web page), and to let `run` follow demand. Every extra `check` user is a free user who sees real problems in their own
screenshots. That is what sells `run`.

### Top 5 items (ranked by reach gained per day of work)

| # | Item | Expected reach (rough) | Effort | Horizon |
|---|---|---|---|---|
| 1 | **`check` as a Linux Docker image plus a GitHub Action that runs on `ubuntu-latest`** (built from the existing `packaging/build-linux.sh`; Tesseract inside) | Every Linux CI and every developer without a Mac or with an Intel Mac, for `check`. GitHub Actions is the most used CI in organizations (33%), and Linux minutes cost 1/10 of macOS minutes. INFERENCE: this opens `check` to roughly 2 to 3 times as many developers as "Apple silicon Mac only" | 2 to 2.5 days | this week (start), month (done) |
| 2 | **`check` first-class on fastlane snapshot and screengrab output** (in progress on `claude/015-check-any-capture`) | fastlane's audience is about 2.6 times Maestro's by stars, and fastlane is installed 145,610 times a year through Homebrew alone [R beyond-maestro] | about 1 day | this week |
| 3 | **Pricing reach at zero code**: document the Gumroad invoice generator, offer free licences for OSS and students through 100% codes, decide on Gumroad's purchasing-power discount | People who can't pay $29 to $49 or whose company needs an invoice. No data on size. It costs about 1 hour plus the owner's decision | 1 hour of docs plus owner decisions | this week |
| 4 | **Homebrew formula in the existing public `noloman/homebrew-tap`** (the blocker, versioned download URLs, has been gone since 0.1.3) | Mac developers who try `brew install` first. Modest, but it is trust and search | 2 to 3 hours | this week |
| 5 | **Small `check` fixes that remove false problems for the new audiences**: a plain `<locale>/` folder of Android screenshots checked without `--app` gets an "isn't an App Store size" problem on every image (72 of 72 measured); the HTML report has no `alt`, `lang` or non-colour marker | Every first-time `check` user without `--app`, screen-reader users of the report | 3 to 4 hours | this week |

After these: the client-side web checker (month), iOS bring-your-own-capture (month, on demand), Android-only `run` on Linux
(later, behind one 4-core experiment), and a Japanese site (later, behind a trigger). The full ranking is in section 3.

## 1. Who can't use shotfleet today, and how many of them are there?

Population numbers are shares of developers or of apps from public surveys. None of them counts shotfleet's real market. Read them as
"bigger or smaller than", not as head counts.

| Segment | What they can use today | Rough size | How rough |
|---|---|---|---|
| **Apple silicon Mac, macOS 13+** | everything | SO 2024: 31.8% of professional developers use macOS [W]. Mobile developers have a higher share, because iOS needs a Mac | survey share, not mobile-specific; INFERENCE: 45 to 60% of mobile developers have a Mac |
| **Intel Mac** | nothing (installer refuses, arm64 build) [R] | 14.4% of Macs on Steam, December 2025 [W]. Developers probably upgrade faster. INFERENCE: 5 to 15% of Mac developers, and shrinking. macOS 26 is Intel's last release, and Xcode 27 (needed for App Store uploads from April 2027 [R workarounds-reach]) needs macOS 27 | Steam is gamers, not developers |
| **No Mac: Linux or Windows Android-only developers** | `check` from source with Tesseract (Linux); nothing on Windows; `run` on Linux: one fixture, one emulator [R] | SO 2024 professional: Windows 47.6%, Ubuntu 27.7%, WSL 16.8% (multi-select) [W]. Android has 67.6% of mobile OS use (StatCounter, Aug 2026) [W]. Android-only publishers: an old Appfigures-era figure says 28% of Android developers were Android-exclusive (2014 [W]); I found no current count | INFERENCE: the largest group shotfleet doesn't serve, likely as big as the Mac group itself |
| **CI on Linux runners** (GitHub, GitLab, Jenkins, Bitrise Linux stacks) | nothing packaged; the README recipe needs `macos-15` [R] | 55% of developers use CI regularly; GitHub Actions 33% organizational, Jenkins 28% (JetBrains 2025) [W]. GitLab's hosted macOS runners are beta and Premium/Ultimate only [W]. Linux $0.006/min against macOS $0.062/min [W] | good shares, uncertain overlap with mobile |
| **XCUITest, Espresso, fastlane, Paparazzi teams** | `check` works on snapshot output; screengrab gives false "missing"; Paparazzi one language at a time; nothing to pay for [R beyond-maestro] | fastlane 42k stars, 215M gem downloads; Paparazzi 2.6k, Roborazzi 1.1k stars [R beyond-maestro] | stars and downloads are proxies |
| **Flutter, React Native/Expo** | `run` and `check` through translation files; one real app each (wger, obytes) [R `docs/compat.md`] | SO 2024: Flutter 9.4%, React Native 8.4% of all developers [W]. 15% of new apps in 2024 used React Native or Flutter (Appfigures) [W] | good |
| **KMP / Compose Multiplatform** | works; KotlinConf app run end to end [R README] | no good share data | |
| **.NET MAUI, Capacitor/Ionic** | strings readers and `init` detection; no real-app run [R `research/frameworks.md`, README] | SO 2024: MAUI 3.1%, Ionic 2.5%, Capacitor 1.8%, Cordova 2.2% [W] | good, small |
| **Unity and games** | `check` works for sizes, counts, missing and copies; language only if text is drawn and OCR can read it; Unity strings only from a Localization CSV export [R]. Text-free screens get a note, not a false problem [M] | games are 9.6% of App Store apps and 12.1% of Play apps (42matters, today) [W], but about 31% of downloads [W] | good |
| **SwiftUI-only apps** | everything (native strings) | SwiftUI in about 70% of new iOS apps (a secondary site, attributed to Appfigures) [W] | secondary source |
| **watchOS, tvOS, visionOS, macOS apps** | `check` knows the sizes; no capture (Maestro has no driver) [R] | small; Apple doesn't publish counts | |
| **Non-English readers of the site and docs** | English only (`<html lang="en">`) [R] | most developers are not native English speakers, but every screenshot-tool competitor and fastlane, Maestro and Expo are English-only too [R website-localization] | no keyword data (no Ahrefs access) |
| **People who can't pay $29 or $49** | `check` free; `run` 2 languages free [R README] | unknown. Gumroad offers 20 to 60% discounts by country (purchasing-power parity), currently off [R gumroad-setup] | no data |
| **Companies that need an invoice or seats** | Gumroad's own invoice generator exists, but nothing on our site says so; one key = 3 activations; no team product [R, W] | unknown; Team/CI interest box planned in the strategy note, no data yet | |
| **People who don't use the command line** | the MCP server and skills (an agent drives the CLI) [R README]; no GUI | ButterKit, AppScreens and others are GUI or web; INFERENCE: most of the screenshot-tool market is GUI, but those users design marketing frames, not verified captures | INFERENCE only |
| **Accessibility** | site images have `alt` [R]; the HTML report has none, no `lang`, and marks problems by a red border only [R `write_gallery`] | everyone who uses a screen reader on the report | |

## 2. Each segment: blocker, smallest unblock, effort, risk, revenue, maintenance

Effort is in agent-days of focused work (one day is about 6 to 8 hours), including tests. "Revenue" says whether the item reaches
**paid** use (`run`, `export`) or **free** use (`check`, which only feeds the funnel).

### 2.1 Linux and CI: `check` in a container (item 1)

- **Blocker.** There is no artifact to install. The source is private (DISTRIBUTION: "source not shipped as plain text"), `install.sh` refuses
  non-Macs, and the documented CI recipe needs a macOS runner [R].
- **What works already.** `packaging/build-linux.sh` builds a 20 MB unsigned PyInstaller folder in 13 s that ran `check` and `doctor` on Linux
  [R `docs/linux.md`]. CI runs the unit suite on `ubuntu-latest` with Python 3.11 and 3.13 [R `.github/workflows/ci.yml`]. Today's
  Tesseract-only run gave macOS parity with `--app` [M].
- **Smallest unblock.** A Dockerfile: Debian slim, `tesseract-ocr` plus language data, `aapt` (for `--app app.apk`), and the frozen Linux
  folder (not the source, which keeps the private-source rule). Publish it as `ghcr.io/noloman/shotfleet:<version>` from the release
  script. Then a composite or container Action in the public `noloman/shotfleet-releases` repo: `uses: noloman/shotfleet-releases@v0`
  with `path:` and `app:` / `strings:` inputs. The drafted macOS Action (`research/proposed-action/`) becomes the macOS variant. The
  Docker image also serves GitLab CI, Jenkins, Bitrise Linux stacks, Windows (Docker Desktop) and **Intel Macs** (Docker runs the x86_64
  image), with no Intel build.
- **Language data size.** `tesseract-ocr-all` is large. Ship a slim image with the common languages and document
  `--build-arg LANGS=...`, or a `-full` tag. INFERENCE: published Alpine Tesseract images are 75 to 106 MB compressed and Ubuntu ones are 400 to
  500 MB [W]. Measure it in experiment X1.
- **Effort.** Dockerfile and release hook, 0.5 day. Action and job summary (reuse `research/proposed-action/summarize.py`), 0.5 day. Docs
  and site, 0.5 day. One real CI run, 0.5 day. **About 2 to 2.5 days.**
- **Risk.** Low to medium. A second build per release (13 s, but it needs a Linux machine or container), and Tesseract versions differ from the
  ones measured here (5.5.3, Homebrew; Linux runs used 5.3.4 [R]). Claims: say "`check` runs on Linux in Docker", never "Linux
  support" (`run` is unproven).
- **Revenue.** Free. It enlarges the top of the funnel, and the Action is a GitHub Marketplace search surface. The paid Team/CI tier in the
  strategy note needs CI users first.
- **Maintenance.** One image per release (automate it in `publish.sh`), and one CI smoke job (`check` on the 72-screenshot set with `--app`;
  pass = 0 problems, planted = 3 problems).
- **Without `--app` or `--strings`, Linux `check` doesn't judge language at all**: "64 screenshot(s) ... were read by Tesseract without
  --app: it names no language, so their language was not checked" [M]. Copies and missing screens are still caught [M]. So the Action
  should ask for `app:` or `strings:`, and say clearly when neither is given. That costs nothing: the inputs already exist.

### 2.2 Teams on XCUITest, Espresso, fastlane, Paparazzi (item 2, then BYOC)

Covered in `research/beyond-maestro-2026-10-06.md`, build plan items 1 to 4. It is in progress as `claude/015-check-any-capture`, so I
don't repeat it. For reach: items 1 to 3 (screengrab timestamps, `--app` found by default, Paparazzi by docs) take about 1.5 days, are free,
and reach the biggest capture audience. Item 4 (iOS BYOC, 4 to 6 days plus about 3 hours of device time) is the only way these teams can
**pay**, so it belongs in the month horizon, gated on fastlane users actually showing up. All of it composes with item 1: a fastlane
team on Linux CI (screengrab) gets `check` through the Docker Action.

### 2.3 Intel Macs

- **Blocker.** arm64-only build; the installer refuses `uname -m` = x86_64 [R].
- **Smallest unblock: don't build Intel.** Point Intel users at (a) the Docker image (item 1) for `check`, and (b) the Action. For `run`
  there is no cheap path: a second x86_64 build, a second notarization and every release script changed, 12 to 16 hours plus an Intel Mac with
  Xcode 26, which shotfleet has never been run on [R workarounds-reach]. PyInstaller universal2 needs every binary fat, and
  python-build-standalone ships single-arch builds [R limits-platform-reach]. The Swift OCR helper is the easy part: a fat `ocr` compiled
  and `lipo`ed fine [R]. The simulators are the hard part, because nothing has been tested on Xcode 26 on Intel.
- **Revenue.** Small and shrinking. From April 2027 an Intel Mac can't upload an iOS build (Xcode 27 requirement, INFERENCE that Xcode 27
  won't run on macOS 26).
- **Also cheap.** The Rosetta false refusal in `install.sh` (`sysctl -n hw.optional.arm64`), a one-line fix [R], so Apple-silicon users in a Rosetta
  terminal aren't turned away.

### 2.4 Android-only developers without a Mac: `run` on Linux

- **Blocker.** No Linux release. E1 passed with one emulator on 2 cores (8 min 13 s, fixture, 13/13); two emulators failed on 2 cores; a
  real 18-language app was never run; Linux arm64 has no Google emulator; the licence gate in a frozen Linux build is untested [R
  `docs/linux.md`].
- **Smallest unblock.** (1) Experiment X2 (2 emulators on 4+ cores, one real app). (2) If it passes, publish the frozen Linux build as a
  tarball plus `install-linux.sh`, and the Docker image from item 1 grows an Android variant (KVM only works with `--device /dev/kvm`, so
  most CI containers can't run it; a bare runner can). (3) Test the licence on Linux (X4).
- **Effort.** About 3 to 4 days after X2 passes, plus claims work.
- **Revenue.** **Paid**, and it's the largest unserved group (INFERENCE). That makes it the best paid-reach item, but it depends on an
  experiment, and support costs grow (distro differences, KVM permissions, GPU flags).
- **Maintenance.** Medium to high: a second platform for every release gate, and a Linux device job the owner can't run on this Mac.
- **Windows.** No. Maestro and the emulator run there, but shotfleet assumes POSIX everywhere (paths, `sh`, signals). WSL2 with KVM
  maybe works through the Linux build (INFERENCE, untested). Revisit only if Linux `run` sells.

### 2.5 Frameworks

| Framework | Status | Smallest next step | Effort |
|---|---|---|---|
| Flutter, Expo | run end to end on one real app each [R] | one more real app each (bare React Native: none yet); `init` already finds the builds | device time, 2 h each |
| KMP/CMP | run end to end (KotlinConf) [R] | nothing | |
| .NET MAUI | reader and detection, no real run [R] | one real MAUI sample run (Microsoft's LocalizationDemo strings already read) | 0.5 day + device |
| Capacitor/Ionic | detection, strings through `--strings` [R] | one sample (i18next JSON is the usual format, already read) | 0.5 day + device |
| Unity, games | see 2.6 | docs | 1 h |
| SwiftUI-only | works | nothing | |
| watchOS, tvOS, visionOS, macOS | `check` sizes only | nothing; Maestro has no driver. Say so | |

`init` already covers every framework in that list [R README line 216]. "Better onboarding (`init` for more frameworks)" is mostly done;
what's missing is proof (real runs), not code. Add a MAUI run and a Capacitor run only when someone from those groups asks. Their combined share is
about 5% of developers [W].

### 2.6 Unity and canvas games: what `check` can still do (measured)

I made 6 text-free 1320x2868 "game" screenshots in en, de and ja and ran `check` Tesseract-only [M]:
- Sizes, counts, alpha and missing screens: checked as usual. 0 problems.
- Each screen got a **note, not a problem**: "could not read this screenshot (the text reader found nothing and the picture is not blank),
  so its language is unverified". There are no false failures.
- A text-free image copied from `en/` into `de/` was **not** reported as a copy (0 problems). That is right for text-free art (the same picture
  is fine in every language). Games that draw text in pixels get OCR-based language and copy checks like any app, because OCR reads pixels
  and doesn't care about the engine.
- Smallest step: one docs paragraph ("Games: sizes, counts and missing screens always; language when your screens show text; Unity
  strings via a Localization CSV export"). 1 hour, no code.

### 2.7 Non-English readers

`research/website-localization.md` (2026-10-02) already answers this: later, behind a trigger, **Japanese first, then Korean** (both large
paying App Store markets with peers localizing for them; Tuist added ja/ko docs for that reason). Nothing new changes it. The cost
I'd add: every localized page multiplies the claims audit (`research/site-claims-audit-2026-10-06.md` checks every sentence against
evidence). So localize only the home page, the free-`check` quickstart and the licence page, not the docs. Effort: 1 day per language with
native review. Maintenance: re-check on every claim change. The CLI's own messages stay English: they are what people paste into issues and
agents.

### 2.8 Price, invoices, seats

- **Invoices.** Gumroad generates one from the receipt (name, address, VAT number in "Additional notes"), and EU businesses get VAT refunded
  with a VAT ID [W Gumroad help 194, R gumroad-setup]. Gumroad is the merchant of record, and its terms say the seller doesn't issue invoices
  [R gumroad-setup]. **Smallest unblock:** one FAQ line on the licence page and in the README. 15 minutes. Purchase orders and bank transfer: say no.
- **Seats.** Gumroad licence keys support multi-seat purchases (`is_multiseat_license`, `quantity` in the verify response) [R gumroad-setup].
  Smallest unblock: turn on "Allow customers to choose number of seats" and let `activate` allow `3 x quantity` activations (a few lines in
  the licence code plus tests, about 0.5 day). Cheaper still: nothing in code, a "buy N keys" line. The strategy note's $149-per-repo Team/CI
  idea stays gated on its interest box.
- **Can't pay.** (a) Gumroad's purchasing-power parity, 20 to 60% off by country, is a switch [R gumroad-setup]. But it is **account-wide** (it also changes
  Keysi), and Gumroad applies the larger of PPP and a code, which interacts with `FOUNDER29`. Owner decision. (b) Free licences for OSS
  maintainers and students: 100%-off codes with a quantity of 1, given by email on request (a GitHub repo link or a student email). No code to
  write. A few minutes per request. (c) Don't widen the free tier: `check` free on existing sets is the stronger demo [R beyond-maestro].
- **Revenue.** PPP and seats can add paid sales; free licences cost nothing at 0 sales and buy goodwill and write-ups.

### 2.9 People who don't use the command line

- **What exists.** The MCP server and skills let an agent drive everything [R README]. For "I don't use a terminal" people, an agent in a
  GUI (Claude Desktop, Cursor) is already the front end. Document that path ("ask your agent to check your screenshots").
- **Client-side web checker (month).** A static page on shotfleet.com where you drop a folder. It checks sizes, counts, alpha, missing screens and
  copies (image hash) in the browser, **nothing is uploaded**, and it links the CLI for the language check. Two ways to build it: (a) port the
  store rules to JS (drift risk: a second implementation of `store_rules`; mitigate by generating a JSON rules table from `shotfleet.py`),
  or (b) run shotfleet's own stdlib `check` in Pyodide plus tesseract.js for OCR (no drift, but it **ships the check code to every browser**,
  which breaks the private-source rule, and the page weighs MBs). INFERENCE: (a) is 2 to 3 days and needs experiment X3 on Pyodide first if (b) is wanted.
  Reach: non-CLI people, plus a page that search engines and LLMs can cite ("check App Store screenshot sizes online"). Free.
- **Hosted upload `check`: no** (section 4).
- **GUI app (SwiftUI menu bar or local web UI): not now.** A SwiftUI app means another signed, notarized target per release, for Mac users
  who already have the CLI. The `check` report is already HTML. If anything, a `shotfleet check --open` that opens the report costs 30 minutes.

### 2.10 Accessibility of output and docs

- **Report (`write_gallery`) [R].** No `<html lang>`, `<img>` without `alt`, problems marked only by a red border and a tooltip, no `scope` on
  headers. Fix: `lang="en"`, `alt="<locale> <screen>"`, a text badge ("problem") next to flagged images, `<th scope>`. About 1 hour, with a test.
- **Site.** Images have `alt`, nav has `aria-label` [R]. A WCAG pass (contrast, focus, reduced motion) on 7 pages takes 0.5 day. Do it with the
  next site refresh, not separately.
- **CLI.** Plain text and `--json`, both already screen-reader friendly.

### 2.11 Distribution wrappers

| Wrapper | Verdict | Why |
|---|---|---|
| Homebrew formula in `noloman/homebrew-tap` (public, only a README today [M `gh api`]) | **yes, this week** | Drafted and `brew audit --strict` clean [R workarounds-reach]. The blocker (unversioned URL) is gone: 0.1.3 is served at `/download/<v>/` [R `docs/compat.md`]. Publish only the fully qualified `brew install noloman/tap/shotfleet` (Homebrew 7 tap trust). 2 to 3 hours plus a step in `publish.sh` |
| pipx | no | it ships readable source (private-source rule), and macOS's Python is 3.9 [R DISTRIBUTION] |
| npm / npx wrapper | no | a second registry to maintain for a 1-line `curl` install; the React Native audience can run the curl line. Revisit if an Expo community asks |
| Docker | yes, as item 1 | |

### 2.12 The plain-folder store assumption (found today)

A `<locale>/*.png` folder with no `--app` is treated as App Store screenshots (`find_screenshots`: the `*/*` pattern gets
`APP_STORE`) [R], so 72 Android 1080x1920 screenshots gave **72 "isn't an App Store screenshot size" problems** [M]. The rule is
platform-independent, so it hits Mac users too (INFERENCE from the code: same function, no OS branch). With `--app app.apk` it judged
Play correctly [M]. This is exactly the first run a new Linux or Docker user will make. Smallest fix: pick the store from the sizes when
every image is a Play size and none is an App Store size, and say which store was assumed, or add a `--store play|appstore` flag. 2 hours with tests.
That belongs in item 5.

## 3. Ranked roadmap

"Reach per day" is a rough, relative score: newly reachable people times how likely they are to use the result, divided by days. INFERENCE
throughout. The order matters more than the numbers.

### This week

| Rank | Item | Owner type | Days | Reach per day | Depends on | Experiments |
|---|---|---|---|---|---|---|
| 1 | Docs-only quick wins: invoice FAQ line; games paragraph (2.6); "Intel Mac or no Mac? Run `check` in Docker" (once the image exists); "ask your agent" path for non-CLI users; fix the Linux docs to "x86_64 only" | docs | 0.3 | very high (cost near zero) | none | none |
| 2 | `check` first-class on fastlane output (beyond-maestro items 1 to 3; already in progress) | code + docs | 1.5 | high | `claude/015-check-any-capture` | beyond-maestro E1 to E3 (no device) |
| 3 | `check` false-problem fixes: plain-folder store (2.12), report accessibility (2.10) | code | 0.5 | high (every first run) | none | none |
| 4 | Homebrew formula in `noloman/homebrew-tap` | code (release script) | 0.4 | medium | versioned URLs (done) | `brew install` from the real URL on this Mac; no device |
| 5 | Linux Docker image for `check`, built from `build-linux.sh` | code | 1 | very high | owner: public image on ghcr.io | X1 |
| 6 | Owner decisions on PPP, free OSS/student codes and seats (2.8) | business | 0 code | medium | none | none |

### This month

| Rank | Item | Owner type | Days | Depends on | Experiments |
|---|---|---|---|---|---|
| 7 | GitHub Action for `check` (Linux container by default, macOS variant from `research/proposed-action/`), Marketplace listing | code + business | 1 to 1.5 | item 5; owner accepts the Marketplace terms; public `noloman/shotfleet-releases` | X1b: one real Actions run |
| 8 | Site: a "free check" landing section that names fastlane, Linux CI, Docker and Intel; Action and Homebrew lines | site | 0.5 | items 2, 4, 7 | claims audit per sentence |
| 9 | Multi-seat licences (`3 x quantity` activations) | code + business | 0.5 | owner turns on seats in Gumroad | X5 (no device) |
| 10 | Client-side web checker for sizes, counts, alpha, copies and missing screens, nothing uploaded | site + code | 2 to 3 | rules table exported from `shotfleet.py` | X3 if Pyodide is considered |
| 11 | iOS bring-your-own-capture (XCUITest, under the licence): the paid path for non-Maestro teams | code | 4 to 6 | item 2 shipped and fastlane users asking | beyond-maestro E4, E5 (about 3 h of device time) |

### Later (each behind a trigger)

| Item | Owner type | Days | Trigger | Experiments |
|---|---|---|---|---|
| Android-only `run` on Linux (tarball, installer, Docker variant with KVM) | code | 3 to 4 after X2 | X2 passes and 3 independent asks, or the Linux `check` image shows real use (pulls, Action installs) | X2, X4 |
| Japanese, then Korean home page, `check` quickstart and licence page | site + business | 1 per language + native review | the website-localization note's trigger (traffic share from ja/ko or asks) | none |
| Android BYOC (Espresso/screengrab capture under the licence) | code | 3 to 4 | iOS BYOC used | beyond-maestro E6 |
| Team/CI licence ($149 per repo idea) | business + code | 0.5 to 1 | strategy note's interest box: 15 emails or 3 CI replies | none |
| One real run each for MAUI and Capacitor | code (device) | 0.5 each + device | someone from that group asks | device lock, 1 h each |
| Intel `run` build | code + release | 2 + an Intel Mac | 3 independent asks for `run` on Intel (Docker covers `check`) | needs Intel hardware |

### Experiments (none needs a simulator except where marked)

All follow the existing rules: one at a time, only while the 1-minute `vm.loadavg` is under 300, in a scratch folder, with a per-step kill limit
and a progress check, killing only what the experiment started.

| # | Proves | Steps | Time | Hard limits |
|---|---|---|---|---|
| X1 | the Docker image builds, its size, and `check` parity in a real Linux container | `docker build` (Debian slim + Tesseract + aapt + frozen folder), then `check` on the 72-screenshot set clean (expect 0) and planted (expect 3), with `--app` | 45 min | **Docker Desktop is not running on this Mac** (socket missing, today); starting it takes 2 to 4 GB of RAM on a shared Mac, so either the owner OKs starting it (stop it afterwards) or this runs on a GitHub `ubuntu-latest` job. 20 min kill on the build, 10 min on each `check` |
| X1b | the Action on GitHub | dispatch one workflow on `ubuntu-latest` in the public repo | 10 min | owner's yes for Actions use (Linux minutes cost $0.006 each, about $0.05 total; free if standard runners are free for public repos, not confirmed [W]); one run, no retries without a look at the log |
| X2 | Android `run` on Linux with 2 emulators and a real app | E1 on a 4+ core KVM machine, then CrossfitTracker's 18 languages | 1.5 h | KVM machine only (not this Mac); 30 min kill per `run`; whether public-repo `ubuntu-latest` runners have 4 vCPU is unverified, so check `nproc` first and stop if it prints 2 |
| X3 | Pyodide can run `check` without the OCR | load `shotfleet.py` in Pyodide in a local page, run store rules and hashing on 6 PNGs | 1 h | scratch only; no publish |
| X4 | the licence gate in a frozen Linux build | build with `build-linux.sh` in a container; `activate` with a made-up key (expect refused), `run --locales` without a key (expect the free-tier line) | 30 min | no device; made-up key only |
| X5 | multi-seat verify response | read Gumroad's verify response for a test multi-seat purchase made by the owner | 15 min | the owner makes the purchase; I don't |

## 4. What NOT to do, and why

- **No hosted upload-and-check service.** Compute is cents, but it takes people's unreleased screenshots onto a server, breaks the "nothing
  leaves your Mac" promise on the privacy page [R privacy.html], adds storage, retention and abuse handling, and the client-side page (item 10)
  gives the same no-install reach without uploads [R web-service].
- **No hosted iOS capture service, ever.** The macOS licence forbids service-bureau use [R web-service].
- **No Intel build now.** It means a second notarized build and changes to every release script, for a group that loses App Store uploads in
  April 2027. Docker covers their `check` (2.3).
- **No Windows port.** POSIX assumptions everywhere; WSL2 through the Linux build is the only cheap door, and only after Linux `run` sells.
- **No Linux `run` claim before X2.** One fixture with one emulator is not "Linux support" [R `docs/linux.md`].
- **No pipx or npm package.** They ship source or add a registry for nothing a one-line installer doesn't do (2.11).
- **No SwiftUI GUI app or menu-bar wrapper now.** It adds a signed target to every release for users who already have the CLI; agents (MCP)
  are the GUI for people who avoid the terminal.
- **No full-docs translation.** It multiplies the claims audit; localize three pages per language at most, behind the trigger.
- **No bigger free tier.** `check` on existing sets is a stronger, cheaper demo than more free `run` languages [R beyond-maestro].
- **No selector rewriting for XCUITest/Espresso code** [R beyond-maestro].
- **No capture for watchOS, tvOS, visionOS or macOS apps.** Maestro has no driver for them; `check` already knows the sizes.
- **No custom invoices or purchase orders outside Gumroad.** Gumroad is the merchant of record; its generator covers business buyers.

## 5. Decisions only the owner can make

1. **Public artifacts:** publish a Docker image on `ghcr.io/noloman/shotfleet` (the frozen build, not the source) and a public Action in
   `noloman/shotfleet-releases`; accept GitHub Marketplace's terms (I can't accept terms).
2. **Spending exception:** about $0.05 to $0.50 of GitHub Actions minutes for X1b (and X2 if run there), against the "run checks locally" rule.
   Or allow starting Docker Desktop on this Mac for X1.
3. **Purchasing-power parity in Gumroad:** account-wide, so it also changes Keysi; it overrides `FOUNDER29` when it's larger.
4. **Free licences for OSS maintainers and students:** yes or no, and what proof (repo link, school email).
5. **Seats:** turn on Gumroad multi-seat for the product (then the code honours quantity), or say "buy one key per developer" only.
   Separately, whether to test the $149-per-repo Team/CI price (strategy note).
6. **Invoice and purchase-order policy:** confirm "Gumroad's invoice generator; no purchase orders" for the FAQ.
7. **Linux `run` as a paid product:** only after X2; also whether Linux buyers get the same key (one key, any OS).
8. **Web checker:** client-side JS rules (keeps the source private) or Pyodide (ships the check code to browsers).
9. **Site languages:** confirm Japanese then Korean, and the trigger.

## Measurements (2026-10-06, this Mac, `vm.loadavg` 26 to 75 throughout)

**Linux-equivalent `check`.** The source of this branch with `shotfleet.vision_available = lambda: False` (the same switch `is_mac()` gives on
Linux), so `check` takes the Tesseract path it takes on Linux. Tesseract 5.5.3 (Homebrew, 163 language packs). Python 3.14 (Homebrew). This is
a simulation on macOS, not a Linux run; `docs/linux.md` has the real Linux runs (Tesseract 5.3.4). Script and outputs are in the session
scratchpad (`linuxcheck/`), not committed.

Data: CrossfitTracker's Android run from the 0.1.2 gate, `/Users/manu/Developer/shotfleet-rc-build/0.1.2/home-d-source-apk/out/raw`
(18 languages x 4 screens, 1080x1920), copied as plain `<locale>/` folders. "Planted" = `en/01_train.png` copied over `de/01_train.png`, and
`ja/02_log.png` deleted. APK: CrossfitTracker release build (66 MB, read only).

| Run | Exit | Time | Result |
|---|---|---|---|
| clean, `--app app.apk` | 0 | 89 s | `checked 72 screenshots in 18 languages: 0 problem(s)`; 72 of 72 judged by OCR against the app's strings |
| planted, `--app app.apk` | 1 | 75 s | 3 problems: `de/01_train.png: shows en strings (20 lines) more than de (6)`; `identical image in 2 languages: de/01_train.png, en/01_train.png`; `ja: missing 02_log.png` |
| clean, no `--app` | 1 | 10 s | 72 problems, all `1080x1920 isn't an App Store screenshot size` (section 2.12); note: 64 screenshots' language not checked (Tesseract names no language) |
| planted, no `--app` | 1 | 10 s | the copy and the missing screen found; the English screen in `de/` **not** found; the same 72 size problems |
| planted, no `--app`, **normal macOS mode** | 1 | 380 s | macOS text recognition "didn't answer in time" (ANECompilerService compiling, even at load 26) and `check` fell back to Tesseract, so the result was the same as the Linux-mode run. No clean Vision comparison was possible today; the 0.1.2 gate's Vision run on the same set gave 0 problems in 318 s [R `proofs.out`] |
| 6 text-free "game" screens (en, de, ja; 1320x2868 gradients) | 0 | under 10 s | 0 problems; 6 notes "could not read this screenshot ... its language is unverified" |
| the same with `en/01_level.png` copied into `de/` | 0 | under 10 s | 0 problems: copies of unreadable images are not reported |

**Other checks.** `docker info`: client 29.8.2, daemon not running (no socket), so no container was run. `gh api` on `noloman/homebrew-tap` and
`noloman/shotfleet-releases`: each holds only a README. `which tesseract`: present.

## Sources

- Stack Overflow Developer Survey 2024, technology (OS use; Flutter, React Native, MAUI, Ionic, Capacitor, Cordova): https://survey.stackoverflow.co/2024/technology
  (read through a summarizer; the 2025 page has no OS or mobile-framework section that I could read)
- StatCounter mobile OS share: https://gs.statcounter.com/os-market-share/mobile/worldwide (Android 67.6%, iOS 32.4%, August 2026, through a search summary)
- Appfigures, non-native development share of new apps: https://appfigures.com/resources/insights/20250307/1-non-native-development-hit-a-new-peak (search summary)
- SwiftUI share of new iOS apps (secondary): https://theswiftk.it.com/blog/flutter-vs-react-native-vs-swiftui
- 42matters store stats (games share, app counts, 2026-10-06): https://42matters.com/stats
- Games share of downloads: https://www.apptweak.com/en/reports/app-downloads-by-category (search summary)
- Steam Mac CPU share, December 2025: https://appleinsider.com/articles/26/01/12/forget-m1-m4-is-the-dominant-apple-silicon-chip-on-steam
- JetBrains, State of CI/CD 2025: https://blog.jetbrains.com/teamcity/2025/10/the-state-of-cicd/ (search summary)
- GitHub Actions runner pricing: https://docs.github.com/en/billing/reference/actions-runner-pricing
- GitLab hosted macOS runners: https://docs.gitlab.com/ci/runners/hosted_runners/macos/
- Gumroad invoices: https://gumroad.com/help/article/194-i-need-an-invoice.html
- Android-exclusive developers, 2014 (old): https://appdevelopermagazine.com/1715/2014/7/29/There-Are-506,742-Mobile-Developers-in-the-Three-Major-App-Stores:-And-They-Don%E2%80%99t-Play-Together/
- Tesseract Docker image sizes: https://hub.docker.com/r/jamesbrink/tesseract , https://hub.docker.com/r/wcchooi/tesseract-ocr (search summary)
- Repo notes named in each section.
