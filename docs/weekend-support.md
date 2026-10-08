# Support sheet for a launch weekend

One page for whoever answers `hello@shotfleet.com` (it forwards to the owner's Gmail). Facts come from `site/public/terms.html`, `site/public/install.sh`, `shotfleet.py` messages and `docs/refund-runbook.md`. Gumroad screens marked **[unverified]** were not seen live (nobody has bought yet); trust the screen over this page.

Rules: reply within two business days; never ask for or paste a licence key, card detail or buyer email into a chat or repo; never buy shotfleet with your own card (Gumroad treats it as card testing); never delete or recreate the Gumroad product (every key would stop working).

## What a buyer should be able to do

1. Buy on Gumroad (receipt email has the key, four groups of 8 letters and digits).
2. `curl -fsSL https://shotfleet.com/install.sh | sh` (Apple silicon, macOS 13 or later; the installer refuses Intel Macs).
3. `shotfleet doctor` (add `--fix` to fetch Maestro and Java), `shotfleet init`, `shotfleet activate KEY`, `shotfleet run`.

`check` and 2 languages in `run` are free without a key.

## Common requests

| Request | What to do | Reply gist |
|---|---|---|
| Refund inside 14 days | Gumroad, Sales, the sale, Refund fully **[unverified]**. Full steps: `docs/refund-runbook.md` section 2 | Template A in the runbook. The key locks at its next weekly check |
| Refund after 14 days | Runbook section 7 (ask what failed first; refund up to about 30 days if unfixable) | Template B |
| "I lost my key / no email" | Self-service: the buyer enters the purchase email at https://gumroad.com/license-key-lookup (linked as "Already bought this? View your information" on the product page) and Gumroad emails the receipt with the key. Tested 2026-10-08: it answered "emailed to you" and the mail arrived within seconds, for an older purchase; a shotfleet key through it is unproven because creator test purchases are not found. Fallback: find the sale in Gumroad Sales and resend the receipt **[unverified]** | Check spam; never type the key into chat |
| "Key is rejected / used too many times" | A key allows 5 activations (3 Macs plus 2 spare, from 0.1.6). In Sales, open the sale, License key card: Reset (sets Uses to 0; asks to confirm) or Edit to the number of Macs still in use. Both tested 2026-10-08. | "Reset done, run `shotfleet activate KEY` again" |
| "That doesn't look like a shotfleet key" | The key shape is four groups of 8. Other stores' keys are refused on purpose | Point to the Gumroad receipt |
| Install fails | See the table below | Ask for `shotfleet --version` and `shotfleet doctor` output |
| Chargeback or dispute | Runbook section 6: reply within 72 hours (120 if a weekend falls inside), do not refund as well without asking Gumroad first | |
| Free licence (maintainer or student) | A 100%-off Gumroad code for the same licence. A 100%-off sale has no refund button | |

## Install and first-run problems

| Symptom | Cause and answer |
|---|---|
| `shotfleet: command not found` after install | The installer prints a line to add its folder to PATH; open a new Terminal window afterwards |
| "needs an Apple silicon Mac" | Intel Mac: not supported, offer the refund |
| "download is corrupt (checksum mismatch)" | Retry; if it repeats, tell the owner (the watchdog should also have alerted) |
| macOS is older than 13 | Not supported. Live 0.1.6 is proven on macOS 14.8.9, 15.7.9 and 27 (`research/macos-14-15-live-0.1.6-2026-10-08.md`); macOS 13 and 26.0 to 26.1 are not tested |
| `doctor` shows MISSING for emulator, avdmanager, aapt2 or system image | Android only; `doctor` prints the exact `sdkmanager` commands. iOS-only users can ignore it |
| `doctor` says text recognition is slow, waited 60 s | First run on a Mac compiles macOS's text model once (ANECompilerService), up to a few minutes on a busy Mac. Wait, run `doctor` again; `check` waits for it by itself |
| iOS 27.0 simulator runtime problems | Since 0.1.7, `run` skips iOS 27.0 when another runtime (for example 26.4) is installed, and `doctor` says which one it will use (0.1.8). Ask them to update to the live version and install iOS 26.4 if they only have 27.0 |
| Maestro version | `doctor` lists the tested versions (2.0.10 and 2.11.0); for any other version, ask which one they run |

## Testing the forward

Do not test `hello@shotfleet.com` by mailing it from the Gmail account it forwards to: Gmail hides the forwarded copy of a message you sent yourself, and Cloudflare then mails a "Missing email?" notice. Send from a different address, or read the proof in Cloudflare, Email Routing, Activity log (a line with Result "Forwarded"). On 2026-10-08 a test from the owner's Gmail showed "Forwarded" there, so the route works.

## Rehearsed on 2026-10-08 (Gumroad creator test purchase, no charge)

Checkout with FOUNDER29 for a Dutch buyer: $49 - $20 = $29, VAT 21% added on top ($6.09), total $35.09. The seller got a "New sale" email and the buyer a receipt within seconds (receipt: from Gumroad, VAT line, the 14-day refund line, "Contact ... by replying", and replies go to `hello@shotfleet.com`). The content page showed the key and the "5 activations" text. With that key on the live 0.1.6 build in fake home folders: the first `activate` counted 1 use, repeating it in the same home counted none, four more fresh homes made 5, the sixth was refused ("this key has used all 5 activations. Email hello@shotfleet.com and I'll reset the count") and cost nothing, a CI key (`SHOTFLEET_KEY`) passed the licence gate, and without a key `export` was refused with the buy link. 

Second rehearsal the same day, a real $0 sale (single-use 100%-off code, bought logged out with `hello@shotfleet.com`; the code is deleted): the sale appeared in Sales, five activations then a refused sixth, **Reset** in the sale's License key card (confirm dialog) set Uses to 0 and the sixth Mac then activated, **Resend receipt** ("Receipt resent") arrived through the `hello@` forward, and **Disable** (a second click was needed) made the licence API answer 404 "This license key has been disabled." The live 0.1.6 build then refused that key on a Mac whose weekly check was due ("the key was disabled, as Gumroad does after a full refund"), on a new Mac and as a CI key, and kept the licence file. That is the same signal a full refund produces; only the Refund fully button and a refund disabling the key by itself remain unseen, because a $0 sale has no refund button.

## If the watchdog alerts

Each alert line names the failing probe. Check it yourself first (`curl -sI` the URL) before acting; a single failure can be a network blip, and the watchdog only notifies on a new failure and again on recovery.

| Alert | Likely cause | What to do |
|---|---|---|
| a site page or `install.sh` is not 200 | Cloudflare or a bad deploy | Check https://www.cloudflarestatus.com. If the site was just deployed, roll back by hand: `docs/engineering/06-packaging-and-release.md` section 6.13 B (the earliest `rollback-<version>-*.txt` in `shotfleet-rc-build/release-archive/state/` holds the id; `cd site && npx wrangler@latest rollback <id> -y`, then check `/download/VERSION`) |
| live version is not 0.1.8 | An unannounced publish | Ask the coordinator session; roll back as above if it was not intended. If a newer version was published on purpose, change `EXPECT_VERSION` in `weekend-watch/watch.sh` |
| download missing or checksum mismatch | Half-finished deploy or cache | Retry in 5 minutes; if it persists, roll back as above. Buyers see "download is corrupt" from the installer and are not harmed |
| Gumroad product page down, unpublished or price changed | Gumroad outage, or the product was edited | Open the product in Gumroad (id `naydxx`) and check Published and the $49 price with the FOUNDER29 banner. Never delete or recreate the product |
| Gumroad licence API unexpected answer | Gumroad outage | Nothing to fix on our side: a key already on a Mac keeps working for up to 30 days offline. Tell any buyer who cannot activate to try again later |

## Who to tell

Anything that looks like a bug in shotfleet itself: open an issue note for the owner with the buyer's `shotfleet --version`, `shotfleet doctor` output and the command that failed. Do not paste the buyer's email or key.

## Monitoring this weekend

A launchd job on the owner's Mac (`/Users/manu/Developer/shotfleet-rc-build/weekend-watch/watch.sh`, every 30 minutes, log in `watch.log` next to it) probes the site, the install script, the download and its checksum, the live version (alerts if it is not 0.1.6), the Gumroad product page and the Gumroad licence API, and sends a macOS notification on a new failure and on recovery. Stop it after the weekend:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.shotfleet.weekendwatch.plist
```
