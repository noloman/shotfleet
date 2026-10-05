# Licence and free tier

| Command | Without a licence | With one |
|---|---|---|
| `check`, `doctor`, `init` | free, always | same |
| `run` | captures 2 languages (the first two of the list; `--locales a,b` picks others) | every language |
| `export` | refused: `need a licence` (exit 2) | works |

`check` needs no account and no licence. Price (https://shotfleet.com): $29 for the first 100 buyers, then $49 once per developer, a
year of updates, a 14-day refund; up to 3 of the user's Macs plus their CI. Details are on the site's terms page.

## Activate

The user gets a key in the Gumroad receipt email (also in their Gumroad library). They run it themselves:

```bash
shotfleet activate <key>
```

- Do not ask for the key in chat, and do not run `activate` with a key that was pasted into chat or found in a file: tell the user to run it in their own terminal.
- Success prints `activated on <hostname>. Thanks for buying shotfleet!`. The key and the product ID are sent to Gumroad, which keeps one count of activations per key; nothing else, and no Mac name.
- Failure prints `that key didn't activate: <reason>`. Wrong key, revoked or refunded key, or no network. Keys come with the purchase.
- A key has 3 activations. Activating again on a Mac that already holds the key counts nothing. `shotfleet deactivate` removes the key from this Mac but cannot give the activation back (Gumroad needs the seller's token for that). A key with all 3 used says `activations. Email hello@shotfleet.com`: the user emails and the developer resets the count in Gumroad.

## Where the key lives

`~/Library/Application Support/shotfleet/licence.json` on the Mac, in plain text, with the key inside. Treat the file
like a password:

- never `cat`, print, copy or attach it; never include it in a diagnostic, a bug report, a commit or chat;
- never add it to a repo or a project folder;
- do not read it to "check whether the user is licensed": ask the user, or note that an unlicensed `run` prints `free tier: capturing` and an unlicensed `export` refuses.

## How it is checked

The licence is checked online once at activation and about weekly after that, and works offline for 30 days after the
last good check (`couldn't reach the licence server for 30 days` after that; this applies to an activated Mac, not to `SHOTFLEET_KEY`). A refunded or revoked key stops
working (`this licence is no longer valid`).

## CI

Set `SHOTFLEET_KEY` in the CI secret store (not an activation, no slot used). It is checked online on each run and fails open on
purpose: with Gumroad unreachable the run counts as licensed, and a CI key has no offline limit (the 30 days above apply only to a
Mac where `shotfleet activate` was run). So an outage hides a refunded key until a run reaches Gumroad. Details in ci.md.

## What to tell the user

- Free tier hit: say `run` captured 2 languages and that `export` and the other languages need a licence; give the price once, from https://shotfleet.com, and let the user decide. Do not buy, and do not enter payment details.
- Never describe the licence as a subscription. Updates for a year are included; after that the installed version keeps working while macOS, Xcode and Maestro allow.
