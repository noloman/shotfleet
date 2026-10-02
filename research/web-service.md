# shotfleet as a website with credits: feasibility and unit economics (researched 2026-10-02)

Scope: should shotfleet (today a Mac CLI, $49 one-time, $29 launch) also be sold as a website where people buy credits, upload inputs and receive outputs? Read first in this worktree: `README.md`, `research/pricing-2026-10.md`, `research/limits-platforms.md`, `DISTRIBUTION.md`, `STRATEGY.md`, `site/worker.js` (+ `wrangler.toml`), and the `check`/`judge_screen`/`store_rules` code in `shotfleet.py`. Nothing was booted, run, bought or signed up for.

Evidence tags: **[V]** read on the vendor's own page or document today by me. **[S]** only seen in a web-search snippet (page not opened or it redirected), treat as unverified. **[I]** my inference or estimate, not measured. **[M]** from this repo.

## 0. Read this first (the honest summary)

1. **Compute is almost free; everything else is the cost.** Even the dearest variant costs under about $3 of machine time per 18-language run at low utilisation. What kills the idea is (a) Apple's licence for anything iOS, (b) running strangers' binaries, (c) support (broken flows, Xcode/runtime mismatches), and (d) that a credit price that is competitive with other tools is *more* than the $49 CLI after about four runs.
2. **Variant C (iOS on Macs as a pay-per-run service) is blocked by Apple's own licence text, not by money.** macOS's licence forbids use "in connection with service bureau, time-sharing, terminal sharing or other similar types of services, whether such services are being provided within your own organization or to third parties", and the only leasing carve-out needs a 24-hour exclusive lease, written notice to Apple and CI-style use (section 4.1). Verdict: never, as a self-run Mac service.
3. **Variant B (Android on Linux/KVM) is technically and legally fine** but needs the Linux port that is not built yet (`research/limits-platforms.md` section 2.3, 3-4 days and unmeasured: its experiment E1 and E2 are still open), plus a sandbox and a billing ledger. It would roughly be 17-20 days for something that competes with a Linux CLI the same owner already plans to ship.
4. **Variant A (check as a service) has the best fit as a funnel but weak value as a paid product**: free browser tools for the size rules already exist (section 3), and the part nobody has (the wrong-language check) needs the user's app strings. It is cheap to run (cents) and should be free.
5. **The real distribution gain of a website is not "upload and process"; it is a shareable report link and a no-install first look.** The cheapest way to get that is the hybrid in section 6 (`shotfleet check --share`, or a browser-only checker), which costs 2-3 days and almost no hosting.
6. **No demand data exists** (waitlist: 0 signups, nobody has paid; `research/pricing-2026-10.md` section 3). Everything below is a model. Section 8 gives a test that costs under $50 and needs no new infrastructure.

## 1. What the shotfleet code can reuse (this repo)

| Piece | Where | What it gives a web service | What is missing |
|---|---|---|---|
| Checks | `cmd_check` (L1505), `judge_screen` (L1356), `store_rules` (L1829), `external_ocr` + `TESSERACT_COMMAND` (L1486, L1452) | The whole language/duplicate/missing/size logic is stdlib-only Python and already has a Tesseract fallback | `ocr_tool()` is called unconditionally and needs `swiftc`/Vision, so a Linux server needs the gating listed in `limits-platforms.md` section 2.2 (about half a day); `plutil`/PlistBuddy are used to read iOS strings (replaceable by `plistlib`, stdlib) |
| Report | `out/index.html`, `check.json` | A review grid with problems outlined; `--json` output | Images are separate files next to the HTML, so sharing needs a bundle (thumbnails + JSON) |
| Android run | `android_run` etc. | Works on arm64 Macs today | Not runnable on Linux yet (SDK path, x86_64 image, `fit_parallel`, headless GPU flags, licence path) |
| Site | `site/worker.js`, `site/wrangler.toml`, KV `WAITLIST`, rate limiter | Worker + static assets + KV + per-IP limit exist; Polar is already the payment path (`shotfleet.py` licence code calls Polar's licence-key API) | No R2/D1/queue, no uploads, no accounts. KV is eventually consistent, so it must not hold a credit balance |
| Licence | Polar licence keys in the CLI | A key could double as a credit balance (section 5) | The CLI's licence is enforced only when frozen (`sys.frozen`); a server needs its own check |

## 2. Payments with a merchant of record (Polar), applied to credits

- Fees [V, https://polar.sh/docs/merchant-of-record/fees]: Starter "5% + 50¢" (Pro 3.8% + 40¢, Growth 3.6% + 35¢, Scale 3.4% + 30¢), +1.5% international cards, $15 per dispute, payout fees "$2 per month of active payout(s)" and "0.25% + $0.25 per payout", currency conversion 0.25% (EU) to 1% elsewhere. Initial transaction fees are not refunded when you refund. `DISTRIBUTION.md` quotes the same Starter rate.
- Polar as merchant of record handles "international sales taxes globally" including VAT, GST and US sales tax [V https://polar.sh/docs/merchant-of-record/introduction]. That page does not list seller countries or prohibited products; `DISTRIBUTION.md` says Netherlands is supported (not re-checked by me).
- Credits exist natively [V https://polar.sh/docs/features/usage-based-billing/credits]: a one-time product with a "Credits" benefit credits a usage meter once at purchase; you ingest events; balances are readable through Customer State or the Customer Meters API. Caveat in the docs: "Polar doesn't block usage if the customer exceeds their balance", so reservation and refusal are your code.
- Licence keys have a usage counter [V https://polar.sh/docs/features/benefits/license-keys]: `limit_usage` / `usage`, validation accepts `increment_usage`, plus `limit_activations` and expiry; the validate endpoint is `/v1/customer-portal/license-keys/validate` with `key` and `organization_id`. Whether `increment_usage` is accepted on that unauthenticated endpoint (versus an authenticated one) is not stated clearly; test it before relying on it.
- Effective fee on a pack (Starter, assuming an international card, ignoring the $2/month and per-payout cost): $9 pack = $1.11 (12.3%); $29 pack = $2.46 (8.5%); $79 pack = $5.83 (7.4%); the $49 CLI = $3.81 (7.8%) [I, arithmetic on the [V] rates]. Small packs are expensive; sell $29+ packs.
- Netherlands, no KvK: Polar removes VAT collection for the buyer side. It does not remove your own Dutch tax duties for income from recurring service sales, and cloud invoices (AWS, Hetzner) will be in your private name. I am not a tax adviser; ask the Belastingdienst/an accountant before a service with running costs, because "hobby income" status gets harder to claim as revenue and costs grow [unsure].

## 3. What existing products with this model charge, and how they describe credits

Every credit product I found sells **generated images (AI design, translation)**, not captures from the real app. I found **no product that takes an uploaded build plus a flow and returns localized store screenshots**; the nearest are device clouds (Appetize, Maestro Cloud, Device Farm, BrowserStack) that sell device time.

| Product | URL | Model and numbers | How credits are described | Tag |
|---|---|---|---|---|
| Screenies | https://screenies.app/ | One-time packs: $9 / 12 credits, $19 / 26, $39 / 55 (about $0.71-0.75 per credit) | 1 credit = one phone screenshot, 2 = one tablet screenshot, 0.10 credits per size per locale; "Credits never expire"; failed generations refund credits | V |
| framm.me | https://www.framm.me/ | Packs: $12 / 5 credits ($2.40 per set), $30 / 15 ($2.00), $70 / 40 ($1.75) | One credit produces one screenshot per raw screen you upload, i.e. a full set; no expiry; edits and re-renders free; refund on failure | V |
| Shots (Shots for Codex) | https://shots.run/pricing | Starter $15.83/mo (yearly) for 60 credits, Growth $49.17/mo for 240; top-ups $7 / 15, $20 / 60, $50 / 180 | New screenshot 3 credits, revision 2, translation 1 credit per screenshot per extra locale; subscription credits refresh monthly, top-ups never expire | V |
| Nuvex | https://nuvex.design/pricing | Packs from $5, subscription from $12/mo for 100 credits | Frames cost 2 / 3 / 7 credits by quality; credits do not expire | S |
| StoreShots (redirects to buffmy.app) | https://storeshots.co/ | $8.99/week for 50 credits, $39.99/mo for 250, packs from $9.99 | 1 credit = 1 screenshot, translation, resize or icon | S |
| AppScreens | https://appscreens.com/pricing | Free (no localization); Pro $99/yr (10 languages, store upload); Scale $180/yr (80+ languages) | No separate credits: localization is bundled in the plan | V |
| Screenshots.pro | https://screenshots.pro/pricing | Free; Standard $19/mo (localization); Extended $49/mo | Plans, no credits | V |
| ButterKit | https://butterkit.app/pricing | Free (watermarked, unlimited on-device translation); Pro $99 one-time; Supporter $39/yr | Runs on the Mac, "no accounts, no servers, no cloud storage" is its stated pitch | V |
| Maestro Cloud | https://www.maestro.dev/pricing | $250 per device per month ("a device is max concurrent executions"), unlimited hosted runs, no per-minute fee; local CLI free | Not credits: flat concurrency | V |
| AWS Device Farm | https://aws.amazon.com/device-farm/pricing/ | $0.17 per device-minute (first 1,000 minutes free); unlimited plan from $250/mo; private devices from $200/mo | Per device-minute | V |
| Appetize | https://appetize.io/pricing | Free 30 min/mo; Starter $59/mo (500 min, $0.06/min over); Premium $319/mo | Streaming minutes | V |
| Firebase Test Lab | https://firebase.google.com/pricing | Virtual devices $1 per device-hour (free up to 60 min/day), physical $5 per device-hour (30 min/day free) | Device time | V |
| BrowserStack App Automate | https://www.browserstack.com/pricing?product=app-automate | $175 or $225 per parallel per month on annual billing; whether Maestro runs was not on the page | Parallels | V |

What this tells us:
- The credit-pack price anchor for a "result" is **about $0.70 per credit and $1.75-2.40 per finished set**. Those tools have GPU/LLM cost per credit; shotfleet's marginal compute is far lower, so shotfleet could price lower and still keep margin, but the market anchors a localized *set* at a few dollars, not at tens.
- The only product with "device-time" semantics priced like a utility is Device Farm ($0.17/min) and Appetize ($0.06/min). One shotfleet 18-language run is about 54 device-minutes if done one language at a time on real devices (about $9.20 at Device Farm [I]).
- Free browser tools already cover store-size validation: e.g. https://screenhance.com/app-store-screenshot-size-checker ("in your browser, with nothing stored") and https://appmockupgenerator.com/screenshot-dimension-checker [S for both]. A paid "check" must sell the language/copies/missing check, not sizes.

## 4. Variant C first, because it decides the whole idea: Apple's licence

Documents read in full today: the Xcode and Apple SDKs Agreement (https://www.apple.com/legal/sla/docs/xcode.pdf) and the macOS Tahoe 26 licence (https://www.apple.com/legal/sla/docs/macOSTahoe.pdf). The macOS 27 text and Apple's licensing FAQ were not reachable; terms may differ. This is not legal advice; ask Apple Developer Relations through https://developer.apple.com/contact/macos-license/ (the form the licence itself names) before building anything.

### 4.1 What the texts say [V, quoted briefly]

- Xcode/SDKs Agreement section 2.2: a "limited, non-exclusive, personal, revocable, non-sublicensable, non-transferable, and internal use license" to install on Apple-branded computers "owned or controlled by You" to test and develop applications.
- Section 2.7: you may not "enable others to" run the software on non-Apple hardware, and "This Agreement does not allow the Apple Software or Services to be made available over a network where they could be run or used by multiple computers at the same time, unless otherwise expressly permitted in writing by Apple", nor "rent, lease, lend, upload to or host on any website or server ... or to enable others to do so".
- macOS licence section 2B(iii): up to two additional virtual macOS instances per Apple-branded computer, for development and testing, and it "does not permit you to use the virtualized copies or instances ... in connection with service bureau, time-sharing, terminal sharing, relay service or other similar types of services". Section 2I repeats the ban "whether such services are being provided within your own organization or to third parties" and limits remote desktop control to one device.
- macOS licence section 3, "Leasing for Permitted Developer Services": you may lease a Mac to a lessee only for "continuous integration services ... automated testing during software development", each lease "a minimum period of twenty-four (24) consecutive hours", the lessee needs "sole and exclusive use and control" of the software and the hardware, and "Each Lessor must provide Apple with advance notice prior to leasing". This is the clause behind AWS's own statement that EC2 Mac has "a 24-hour minimum allocation period to comply with the Apple macOS Software License Agreement" [V https://aws.amazon.com/ec2/instance-types/mac/].

### 4.2 What that means for shotfleet-as-a-service

- A shared Mac where many strangers' builds run one after another through your Xcode and Simulator, billed per run, matches "service bureau/time-sharing" and "made available over a network ... used by multiple computers" far more than it matches section 3 (24 h exclusive lease per customer). My reading is that **it is not permitted without written permission from Apple**. Larger CI vendors (GitHub, Codemagic, Bitrise) sell per-minute macOS; I assume they have arrangements with Apple, but I could not find what those are [unsure].
- A compliant but useless shape: each customer leases a whole Mac for 24 h (about $21 minimum on AWS M2, section 4.3), with you providing only support. That is not "credits".
- Compliant alternative with no Apple exposure: **the customer's own Mac or CI** runs the CLI (the existing GitHub Actions recipe, README "In CI"). Your service then sells software, not Mac time.

### 4.3 Cloud Mac prices [V unless marked]

| Option | Price | Minimum / notes |
|---|---|---|
| AWS EC2 Mac `mac2-m2.metal` (8 vCPU M2, 24 GiB) | $0.878/hour on-demand us-east-1 [V instances.vantage.sh/aws/ec2/mac2-m2.metal] | **24-hour minimum per Dedicated Host** [V AWS pages] = about $21.07 per allocation |
| AWS `mac2.metal` (M1) | $0.65/hour [S] | same minimum, about $15.60 |
| AWS `mac-m4.metal` | $1.23/hour [S, macyou.co] | about $29.50 per day; `mac-m4pro.metal` $1.97/h [S] |
| MacStadium dedicated Mac mini | M2.S $109/mo (8 GB), M4.S $149/mo (M4 10-core, 16 GB), M4.M $249/mo (24 GB), M4.L $349/mo (M4 Pro, 48 GB) [V https://www.macstadium.com/pricing] | Monthly pre-payment in USD |
| MacStadium Orka | Not on the public page; contact sales [unverified]. Apple's two-VM-per-Mac limit applies to any Orka host | |
| Scaleway Apple silicon (Paris) | M2-M (16 GB) EUR 115/mo or EUR 0.17/h; M4-S (16 GB) EUR 149/mo or EUR 0.22/h; M4-M (32 GB) EUR 199/mo; M4 Pro 64 GB EUR 335/mo [V https://www.scaleway.com/en/pricing/apple-silicon/] | 24-hour minimum commitment |
| GitHub-hosted macOS runner | $0.062/min (3-4 core), $0.102/min (5-core M2 Pro xlarge), $0.077/min (12-core Intel) [V docs.github.com runner pricing] | Per minute, rounded up; **you cannot resell it**; a customer's own repo can use it |
| Codemagic macOS M2 | $0.095/min pay-as-you-go [S]; 500 free minutes/month for personal accounts [S] | |
| GitHub arm64 macOS runners | No nested virtualisation [V, quoted in `limits-platforms.md`], so Android emulators with acceleration do not run on them | |

### 4.4 Unit economics for C (iOS capture, 18 languages)

Assumptions [I]: iOS run is 9 min of capture (README: 18 locales in 534 s) plus build install/boot, so a 15-minute slot; one Mac does one run at a time (4 simulators use the machine). Both platforms in one run is about 25-30 minutes on one Mac (README: iOS 9 min, Android 15 min), but Android should go to Linux (section 5) because acceleration is not available inside Mac VMs.

| Item | Value | Basis |
|---|---|---|
| Machine slot | 15 min | [I] |
| Always-on MacStadium M4.S, cost per run at 100% / 25% / 5% utilisation | $0.05 / $0.20 / $1.02 | $149 / 730 h = $0.204/h, 4 slots per hour [I] |
| AWS M2 host day, cost per run if 4 / 20 / 57 runs happen inside the 24 h | $5.27 / $1.05 / $0.37 | $21.07 per allocation [I] |
| GitHub-hosted equivalent (a customer running the CLI themselves) | $0.93 (3-core) to $1.53 (xlarge) per 15 min | $0.062-0.102 per min [V] |
| Proposed price per run | 36 credits (2 per language) = $19 at the $0.53 pack rate to $27 at $0.75 | section 7 |
| Polar fee | about 8.5% | section 2 |
| Support allowance per run | $1.50 | assumes 1 run in 10 needs 30 min of help at $50/h [I] |
| Margin per run (at $22) | about $18 | $22 - $1.9 fee - $0.30 compute - $1.50 support |
| Fixed cost per month | about $175 | one M4.S $149 + $26 other (domain, Workers paid plan $5, R2, Polar $2) [I] |
| Runs per month to cover fixed cost | about 10 | $175 / $18 |
| Runs to repay 30 days of build time at $50/h | about 670 | 30 d x 8 h x $50 = $12,000 / $18 |

Cash break-even is small; the problem is the licence (4.2), the 24-hour/one-run-at-a-time shape (a second customer waits 15 minutes, a burst needs another Mac, and AWS or Scaleway lock you in for 24 hours), and the points in 4.5.

### 4.5 Security and support for C

- **Security.** Apps in the iOS Simulator are ordinary macOS processes under the host user, so a hostile or merely careless build can read the host's files (other customers' uploads, tokens) unless each run is in its own macOS VM [I, well-known behaviour of the simulator]. Apple's licence allows at most two virtual macOS instances per Mac (2B(iii)), so isolation by VM caps concurrency at 2 per machine. Simulator builds need no signing identity, so never ask for certificates or provisioning profiles; accept only `Debug-iphonesimulator` `.app` bundles. The build still exposes the full app binary and resources.
- **Support.** The product's own documented friction is the flow ("writing a Maestro flow", README Limits and `research/pricing-2026-10.md` section 1). On a hosted service every failed run is your ticket: selectors that miss, apps that crash on the newest simulator runtime, builds with a different Xcode/runtime than yours, x86_64-only builds, apps that need login or network backends, permission prompts that stay English (README Tips). Expect most failures to be the customer's flow, with you as the helpdesk.

### 4.6 C: the five top risks and verdict

1. Apple licence: service-bureau/time-sharing ban and internal-use-only terms (4.1); needs Apple's written permission [high, blocking].
2. Two VMs per Mac and 24 h minimum on AWS/Scaleway: poor fit for bursty per-run sales.
3. Customer binaries and files on a shared Mac: breach or abuse falls on a person with no company.
4. Support load from flows and Xcode/runtime mismatches.
5. Unmeasured demand; the CLI buyer already owns a Mac.

**Verdict C: never** (as a hosted service). Keep CI instructions and the licence for people's own runners. Revisit only if Apple's Developer Relations gives written permission.

## 5. Variant B: Android capture as a service on Linux

### 5.1 What it needs
- The Linux port of the Android path (3-4 days, `limits-platforms.md` section 2.3), the AVD/`x86_64` image, Maestro, Java 17, and `/dev/kvm`. The Android emulator needs KVM; Firecracker-style microVMs expose none, so use bare metal or a VM with nested virtualisation [V https://www.pandastack.ai/blog/mobile-ci-android-emulator-microvm-limits/ for the Firecracker point].
- **Hetzner Cloud cannot do it**: its FAQ answers nested virtualisation with "No, this is not possible on cloud server" [V https://docs.hetzner.com/cloud/servers/faq/]. Hetzner cloud prices also rose sharply on 15 June 2026 (CCX33 EUR 62.49 to EUR 138.49 per month, CCX43 EUR 124.99 to EUR 275.99) [V https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/].
- AWS added nested virtualisation on C8i/M8i/R8i (and some 7th-gen Intel) in 2026 [V https://www.infoq.com/news/2026/03/aws-ec2-nested-virtualization/]. AWS itself says performance-sensitive hardware-virtualisation workloads "should continue using bare-metal instances". Android emulators under nested KVM are typically slower and flakier [I]; the Android part of shotfleet depends on timing (driver start timeouts already needed 240 s on tablets, `limits-platforms.md` section 3.2).

### 5.2 Compute price per run [I for the run time, V for the prices]

A run = 18 languages, 4 emulators, 8 vCPU / 16 GB, about 25 minutes of capture on x86 plus 5 minutes of boot and cleanup (the 15 minutes in the README was measured on Apple silicon, not on x86 KVM; the x86 number is the unknown to measure in experiment E1).

| Host | Price | Cost per 30-minute run | Comment |
|---|---|---|---|
| AWS `c8i.2xlarge` (8 vCPU, 16 GiB), nested KVM | $0.375/h on-demand, $0.216/h spot [V instances.vantage.sh] | $0.19 (spot $0.11) | Per-second billing, started per run; needs an AMI with the SDK and images baked in; nested-virtualisation speed unknown |
| GCP `n2-standard-8` (nested virtualisation is a documented GCP feature) | $0.388/h on-demand us-central1 [S, search snippet] | $0.19 | Same pattern |
| Scaleway Elastic Metal `EM-A610R-NVMe` (6 cores/12 threads, 32 GB) | EUR 39.99/mo (EUR 0.11/h) [V https://www.scaleway.com/en/pricing/elastic-metal/]; monthly orders also carry a one-month commitment fee | EUR 0.027 at 100% use, EUR 0.27 at 10% (about 146 runs per month) | Real KVM, always on; one run at a time; 6 cores is tight for 4 emulators |
| Hetzner dedicated `AX42-1` (8 cores/16 threads, 64 GB) | EUR 97.30/mo excl. VAT after 15 Jun 2026 [V price-adjustment page]; setup fee about EUR 49 [S] | EUR 0.067 at 100%, EUR 0.67 at 10% | Real KVM; a month's commitment |
| GitHub ubuntu 8-core x64 | $0.022/min [V] | $0.66 | KVM on larger runners not verified; not resellable |
| Firebase Test Lab virtual device | $1 per device-hour [V] | $1.00 if you ran 4 emulators for 15 min | Cannot run shotfleet's `adb`/locale pipeline; Maestro support not confirmed by my search |
| Maestro Cloud | $250 per device per month [V] | n/a | Competitor/supplier; one concurrent device; no evidence per-app locale control is available |
| AWS Device Farm | $0.17 per device-minute [V] | about $9.20 (54 device-minutes, one language at a time) [I] | Real devices, no locale rewriting |
| BrowserStack App Automate | from $175 per parallel per month annual [V] | n/a | Subscription for parallels |

Compute is a rounding error: choose on-demand c8i/n2 for zero idle cost (but expect cold starts of 1-3 minutes [I]) or one cheap Scaleway box for simplicity.

### 5.3 Unit economics for B (Android, 18 languages)

| Item | Value | Basis |
|---|---|---|
| Compute + storage + egress per run | about $0.26 | $0.19 c8i + EBS/snapshot/R2 [I], 20% reruns |
| Price | 18 credits (1 per language) = $9.50 at $0.53 per credit to $13.50 at $0.75 | section 7; mid case $11 |
| Polar fee (8.5% of $11) | $0.94 | section 2 |
| Support allowance | $0.83 | 1 run in 20 needs 20 min at $50/h [I] (Android flows are simpler than iOS, still a Maestro flow) |
| Margin per run | about $9 | $11 - $0.94 - $0.26 - $0.83 |
| Fixed per month | about $25 | Workers paid plan $5, R2/D1, domain, Polar $2/mo, AMI snapshot [I] |
| Runs per month to cover fixed cost | 3 | $25 / $9 |
| Runs to repay about 18 days of build time at $50/h ($7,200) | about 800 | |

Where this lands: 100 customers doing 2 runs a year is about $2,200 a year gross, about $1,800 after costs [I]. A CLI buyer pays $29-49 once and costs you nothing. Set against a Linux CLI at $49 (the plan in `limits-platforms.md` section 7, ranked 2), the hosted version is cheaper only for the first three runs, so it targets the buyer who will not install anything.

### 5.4 Billing credits, queueing, security

- **Billing.** Simplest: sell Polar packs that issue a licence key with `limit_usage`; the worker validates the key and calls `increment_usage` per language when a run starts, and gives credits back when a language fails for our reason (same refund behaviour as Screenies and framm.me, section 3). No accounts, no passwords. Fallback: Polar's Credits benefit + meter, which also needs your own reservation, because Polar does not block overuse [V]. Do not store balances in KV (eventually consistent); use D1 or a Durable Object if you keep your own ledger.
- **Queueing.** One run is one machine. A Cloudflare Queue (or a D1 `jobs` table polled by the VM) plus "start instance on job, terminate on finish" is enough; concurrency N = N machines; a burst costs money only while it lasts. Always-on bare metal means a single global queue and 25-minute waits.
- **Security of customers' APKs.** An APK is arbitrary code. Required: one fresh emulator/VM per run, no shared disk, egress allow-list or an outbound firewall (crypto-mining, scanning and spam abuse are the usual cases), size/time caps, delete inputs and outputs after 24 h, a terms-of-service clause on malware, and a data-processing statement (EU/GDPR, screenshots may include demo personal data; `site/privacy.html` would need an update). KVM isolates the emulated guest, but the emulator process runs on the host, so put the whole run on a disposable VM, not just in a container [I].

### 5.5 B: MVP effort, risks, verdict

| Work | Days | Reuses |
|---|---|---|
| Linux port + `doctor` + one CI run (E1) | 3-4 | `limits-platforms.md` section 2.3 plan |
| Tesseract check path on Linux, validated against Vision (E2) | 1-2 | `external_ocr`, `TESSERACT_COMMAND` |
| Upload (R2 presigned), job table, queue, runner start/stop | 4 | `site/worker.js` pattern, KV for rate limits |
| AMI/baked image, sandbox, egress rules, cleanup | 3 | |
| Credits via Polar licence-key usage, receipts, refunds | 2 | CLI's Polar calls |
| Result page + zip download | 1-2 | `out/index.html` |
| Terms, privacy update, abuse process | 1 | `site/terms.html`, `site/privacy.html` |
| Total | about 15-20 | |

Top 5 risks:
1. x86 KVM runs may be 2-3x slower or flaky (nested virtualisation, no GPU) [I]; unmeasured until E1.
2. Hostile or buggy APKs and abuse of your cloud account (no company, you are personally liable).
3. Support: customers' flows break; the owner becomes the helpdesk.
4. Cannibalises the Linux CLI and costs more than it after four runs (section 7).
5. Anyone with a key can drain a shared credit pool, so keys need per-key concurrency and rate limits.

**Verdict B: later.** Build the Linux CLI first (it validates E1/E2 for free). Only wrap it as a service after the Linux CLI sells and people ask for "no setup".

## 6. Variant A: check as a service, and the cheaper hybrids

### 6.1 What it needs and what it costs
- Inputs: store screenshots (PNG/JPEG) plus the app's strings. For a good check the user should supply strings, not the build: the CLI accepts `.strings`, `.xcstrings`, `strings.xml`, `.arb`, i18next JSON, XLIFF, `.po`, CSV (README Config). Text files are small and carry less IP than a build. An APK needs `aapt2` on the server; an iOS `.app` needs `plistlib` instead of `plutil`.
- Server: Linux container with Python 3.11, Tesseract and the language data (tessdata fast models are several MB per language; all needed languages total hundreds of MB [I]); the macOS Vision path is unavailable, so `check` runs the Tesseract path. One data point from `limits-platforms.md`: Tesseract read de/hi/ja/zh text from low-resolution samples but CJK lines came back with spaces between characters, and verdict parity with Vision is **untested** (E2). Without `--app`, language detection is lost on Linux, which makes the strings upload essential.
- Cost per check: the Mac measured about 25 s for 126 screenshots (README). Tesseract on a server is probably 1-3 s per screenshot per core [I]: a 72-screenshot check is about 2-4 CPU-minutes, so about $0.003-0.01 on pay-per-second containers or EUR 0.0004 of a EUR 0.11/h 12-thread Scaleway box [I]. Storage: 72 PNGs of about 1.5 MB = about 100 MB per check for as long as you keep it (delete after 24 h; R2 about $0.015 per GB-month [I, from memory, unverified]).
- Privacy: store screenshots are about to be public, so the real exposure is the strings and any unreleased feature screenshots. A browser-only design removes it (6.2).

### 6.2 Three ways to build A, cheapest first

| Option | What it is | Cost | Effort | Fit |
|---|---|---|---|---|
| A0: hosted report viewer (hybrid funnel) | `shotfleet check --share` uploads `check.json` plus small thumbnails (about 4 MB per report) and returns an unlisted link like `/r/<random-id>`; reports expire after 30 days; the page ends with "Run this in CI: buy the CLI" | R2 storage for 1,000 reports about 4 GB = under $0.1/month [I]; Worker request limits are free-tier scale | 2-3 days: one route in `worker.js` (PUT report, GET page), a static viewer reusing `out/index.html` markup, an opt-in prompt | Best funnel per day of work; solves "send the result to my designer/PM" |
| A1: browser-only checker | Everything runs client side: size and alpha rules, duplicate hashes and missing screens in JS; OCR with tesseract.js (WASM) per selected language; strings parsed in the browser | $0 compute, no upload, nothing to secure | 6-8 days (the check logic is Python: either port `judge_screen`/`store_rules` to JS or run `shotfleet.py` in Pyodide, which exposes the source) [I] | Strongest on privacy and cost; OCR in the browser is slow (minutes for 72 images) and heavy to download [I] |
| A2: server-side check, credits | Upload to R2, a queue job runs `cmd_check` in a Linux container, result page | cents per check | 7-9 days (Linux gating 0.5, container + tessdata 1.5, upload/queue/result 3, credits 2, privacy/terms 1) | Same output as A1 with more to run and secure |

### 6.3 Does A work as a free funnel for the paid CLI?
Yes, but modestly:
- For: no install, no Mac needed (works for Android-only and Windows/Linux developers), shareable link, fits "SEO for the problem" pages like "check localized app store screenshots" and the existing `alternatives.html`.
- Against: the CLI already has `check` free (STRATEGY.md); a free web check duplicates it for users who have a Mac. The funnel only helps if the web check ends with a reason to buy: "your German set shows English on 3 screens; capture them correctly in every language with `run`". That is true only for users who have the flow, i.e. few.
- Competition: many free size checkers exist [S]; the language check is the differentiator and needs the strings.
- A paid price for A: 1 credit = one full check up to 100 screenshots, packs from section 7; in practice keep the first check per day free. Unit economics at $0.75 per check (one credit from the $9 pack, which loses 12.3% to Polar): fee $0.09, compute $0.01, support $0.10, margin about $0.55; fixed cost about $15/month (Workers paid plan, R2, domain, Polar $2); **27 checks a month to cover fixed costs**, but at 27 checks a month the revenue is about $20; this is a funnel, not a business [I].
- Top 5 risks for A: (1) free browser tools set the expectation at $0; (2) Tesseract verdicts may differ from Vision's on CJK and RTL scripts (E2 untested), so wrong flags look like bugs; (3) unreleased screenshots/strings in a stranger's hands (breach, GDPR); (4) support for "why was this flagged" without a Mac to reproduce; (5) a free web check may satisfy people who would otherwise have installed the CLI and later bought `run`.
- **Verdict A: later, free only, starting with A0.** Do not charge for it.

## 7. Credit pricing proposal (one set of packs for all variants)

Why one pool: simpler to explain, and matches competitors (Screenies, framm.me, Shots all sell never-expiring packs). Use Polar licence keys with `limit_usage` (section 5.4). Avoid the $9 pack in practice because 12.3% goes to fees and Polar's fixed 50 cents; start at $19.

| Pack | Price | Credits | Per credit |
|---|---|---|---|
| Try | $9 | 12 | $0.75 |
| Release | $29 | 48 | $0.60 |
| Studio | $79 | 150 | $0.53 |

What one credit buys:

| Variant | One credit | An 18-language run costs | In dollars |
|---|---|---|---|
| A | one full check (up to 100 screenshots) | 1 credit | $0.53-0.75 (first check per day free) |
| B | one language on Android (up to 10 screens, with the check included) | 18 credits | $9.50-13.50 |
| C | one language on iOS = 2 credits | 36 credits (iOS only), 54 (both) | $19-27 and $29-40 |

Comparison: Screenies $0.71-0.75 per credit for one screenshot [V]; framm.me $1.75-2.40 for a full set [V]; Shots about $1.00 per new screenshot (3 credits at $0.33 each from the $20 top-up) [V]; AppScreens $99/year with 10 languages [V]; Screenshots.pro $19/month [V]; ButterKit $99 once [V]; shotfleet CLI $49 once (launch $29). An 18-language Android run at $11 is pricier than the $29 launch CLI after three runs and the $49 CLI after about four. That is the core conflict: **the credit product is the worse deal for exactly the repeat user, and the better deal only for a one-off user who would otherwise not pay at all.** Expect it to attract the one-off user.

## 8. The cheapest experiment (under 3 days, under $50, no new infrastructure)

**Concierge fake-door, Android and check only.** Do not offer iOS capture as a service (section 4).

1. Add one section to the existing landing page (static HTML, `site/public/index.html`): "Don't want to install anything? We run it for you", with three buttons: **"Check my screenshots, $9"** (send screenshots + a strings file, report within 24 h), **"Android set in 18 languages, $29"** (send an APK + a plain-English list of the screens, delivered within 48 h), and "join the waitlist for instant self-service" (existing `/api/signup`).
2. Create the two paid items as Polar one-time products (no code) with a clear 14-day refund line and "delivered by hand" wording. Polar's checkout page gives you the click-to-pay numbers; add a free Cloudflare Web Analytics beacon (or UTM tags) for visits.
3. Fulfil by hand on the owner's Mac with the existing CLI (`check`, and `run --platform android`). That is allowed: it is the owner using his own Mac for his own work product, not an Apple-hosted service to the public [unsure; fine at a handful of orders]. Cap at 10 orders and stop selling iOS.
4. Traffic: the launch posts already planned in `STRATEGY.md` section 3 (Reddit r/androiddev, r/iOSProgramming, Maestro Slack, Show HN) plus up to $30 of a small Reddit ad; total spend under $50 including Polar fees on the first orders.
5. Pre-commit the decision (the repo's own style is a decision rule in counts): within 21 days and at least 400 unique visitors to that page, **5 paid orders or 25 checkout starts means build A0 then the Linux CLI; fewer than 5 starts means drop the web idea**. Also record how many people open the page from "check" content versus "capture", and which of the two buttons is clicked.

Work: about 1 day for the page and two Polar products, 0.5 day for tracking, up to 1.5 days for the first five orders if they come.

## 9. Distribution: what a website really adds

| Advantage claimed | Reality |
|---|---|
| SEO for "localized app store screenshots" | That intent is "make/frame/translate screenshots" and is crowded by AppScreens, Screenshots.pro, Screenshot Otter, Screenies, framm.me and others (all appeared in search today [S]). shotfleet's different angle (capture each language correctly from one flow and verify it) has no known search volume; I did not find a volume tool, so treat it as unknown. Long-tail pages like "fastlane snapshot alternative", "App Store screenshot language check" and "why do my German screenshots show English" are cheap on the existing static site and need no service |
| No install | True and valuable for check (A); for capture the user still needs a Maestro flow and a build, so the install is not the main friction |
| Shareable report link | Real and rare among the CLI's competitors; a team can review a grid without installing anything; it is a 2-3 day feature (A0) |
| Credits are more profitable than a one-time licence | Only if repeat usage exceeds about four runs per customer and support stays small; per run the owner nets about $9-18 but pays in support and risk (sections 4-5). The one-time CLI has near-zero marginal cost and no Apple, abuse or privacy exposure |

## 10. Verdicts, side by side

| | A: check | B: Android capture | C: iOS + Android capture |
|---|---|---|---|
| Compute cost per run | $0.003-0.01 | $0.11-0.26 | $0.05-5 (iOS Mac host; Android on Linux) |
| Price per run (proposed) | 1 credit ($0.53-0.75), first check free | 18 credits ($9.50-13.50) | 36 credits iOS ($19-27), 54 both ($29-40) |
| Runs per month for cash break-even | about 27 (as paid), 0 revenue needed (as funnel) | about 3 | about 10 |
| MVP effort | A0 2-3 d; A1 6-8 d; A2 7-9 d | 15-20 d | 35+ d, and blocked |
| Top blocker | Free competitors, Tesseract parity | Linux port unmeasured, abuse, support | Apple licence |
| Verdict | **Later, free, start with A0** | **Later**, after the Linux CLI sells | **Never** (without Apple's written permission) |

## 11. Recommendation

Do not build a credits website now. The compute is trivial but the iOS half is blocked by Apple's service-bureau and internal-use terms, the Android half needs a Linux port and a sandbox you are personally liable for, and a credit price that matches other tools makes the CLI the better deal for anyone who repeats. Build the thing that actually moves distribution first: a shareable, expiring report link for the existing free `check` (A0, 2-3 days on the current Worker, with the owner's Polar checkout in the footer), and finish the Linux Android CLI that `limits-platforms.md` already ranks second. Run the concierge experiment in section 8 in parallel, it needs no code: if 5 people pay $9-29 for hand-delivered checks and Android sets within three weeks, build A0 as a self-service page and consider B on top of the Linux CLI; if not, you saved 20 days. Revisit C only after Apple Developer Relations answers in writing.

## 12. What I could not verify

- Apple's macOS 27 licence text and any Apple FAQ on cloud Macs; whether GitHub, Codemagic or Bitrise hold special permission from Apple.
- AWS `mac2.metal`, `mac-m4.metal` and GCP `n2-standard-8` hourly prices (snippets only); MacStadium Orka pricing; Hetzner AX42 setup fee.
- Whether Firebase Test Lab runs Maestro flows (search found only community CI examples); whether Maestro Cloud lets a user set per-app locale.
- Whether Polar accepts `increment_usage` on the unauthenticated validate endpoint, and Polar's Netherlands payout support (taken from `DISTRIBUTION.md`).
- Run times of the Android path on x86 KVM and of Tesseract on shotfleet's real screenshots (E1/E2 in `limits-platforms.md`).
- Search volume for any keyword; R2 and Workers prices (from memory).
- All support-time, failure-rate and utilisation numbers are my assumptions, labelled [I].
