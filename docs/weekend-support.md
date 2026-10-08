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
| "I lost my key / no email" | Ask for the order email; the buyer can use "Get your download link" on the product page, or find the sale in Gumroad Sales and resend the receipt **[unverified]** | Check spam; the key is in the receipt, never type it into chat |
| "Key is rejected / used too many times" | A key allows 5 activations (3 Macs plus 2 spare, from 0.1.6). In Sales, Manage license keys, reset Uses to 0 or the number of Macs still in use **[unverified]**. | "Reset done, run `shotfleet activate KEY` again" |
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
| macOS is older than 13 | Not supported |
| `doctor` shows MISSING for emulator, avdmanager, aapt2 or system image | Android only; `doctor` prints the exact `sdkmanager` commands. iOS-only users can ignore it |
| `doctor` says text recognition is slow, waited 60 s | First run on a Mac compiles macOS's text model once (ANECompilerService), up to a few minutes on a busy Mac. Wait, run `doctor` again; `check` waits for it by itself |
| iOS 27.0 simulator runtime problems | 0.1.7 adds a guard that prefers another runtime (for example 26.4) when one is installed; live is 0.1.6, so suggest installing an older iOS runtime |
| Maestro version | `doctor` lists the tested versions (2.0.10 and 2.11.0); for any other version, ask which one they run |

## Testing the forward

Do not test `hello@shotfleet.com` by mailing it from the Gmail account it forwards to: Gmail hides the forwarded copy of a message you sent yourself, and Cloudflare then mails a "Missing email?" notice. Send from a different address, or read the proof in Cloudflare, Email Routing, Activity log (a line with Result "Forwarded"). On 2026-10-08 a test from the owner's Gmail showed "Forwarded" there, so the route works.

## Rehearsed on 2026-10-08 (Gumroad creator test purchase, no charge)

Checkout with FOUNDER29 for a Dutch buyer: $49 - $20 = $29, VAT 21% added on top ($6.09), total $35.09. The seller got a "New sale" email and the buyer a receipt within seconds (receipt: from Gumroad, VAT line, the 14-day refund line, "Contact ... by replying", and replies go to `hello@shotfleet.com`). The content page showed the key and the "5 activations" text. With that key on the live 0.1.6 build in fake home folders: the first `activate` counted 1 use, repeating it in the same home counted none, four more fresh homes made 5, the sixth was refused ("this key has used all 5 activations. Email hello@shotfleet.com and I'll reset the count") and cost nothing, a CI key (`SHOTFLEET_KEY`) passed the licence gate, and without a key `export` was refused with the buy link. Creator test purchases do not appear in Sales, so a test sale cannot be refunded or reset; the reset, disable and refund steps above stay **[unverified]** until the first real sale.

## Who to tell

Anything that looks like a bug in shotfleet itself: open an issue note for the owner with the buyer's `shotfleet --version`, `shotfleet doctor` output and the command that failed. Do not paste the buyer's email or key.

## Monitoring this weekend

A launchd job on the owner's Mac (`/Users/manu/Developer/shotfleet-rc-build/weekend-watch/watch.sh`, every 30 minutes, log in `watch.log` next to it) probes the site, the install script, the download and its checksum, the live version (alerts if it is not 0.1.6), the Gumroad product page and the Gumroad licence API, and sends a macOS notification on a new failure and on recovery. Stop it after the weekend:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.shotfleet.weekendwatch.plist
```
