---
name: shotfleet-review
description: Read a shotfleet check report (check.json and the shotfleet-check/index.html grid) and turn it into a fix list for the developer. Use when the user shares or asks about shotfleet problems, "shows de strings more than ja", "identical image in N languages", "missing screenshots", "the app has no de translation", store-rule problems, or wants to know which languages to recapture and whether the fix belongs in the app or the flow.
---

# Reading a shotfleet report

Inputs: `check.json` (from `shotfleet check ... --json`, or `<out>/check.json` after `run`) and the grid
`index.html` next to it (`shotfleet-check/index.html` by default). Read both; do not edit the screenshots or the
fastlane folder. `check.json` is `{"screenshots": [{"file", "src", "sha", "lang", "chars", "evidence"}], "problems": [...], "notes": [...]}`.

## Procedure

1. Count **issues, not lines**. Group `problems` by root cause; one wrong-language locale often produces several lines (wrong language, copy, missing). The issue count is the number of groups.
2. For each group name: the locales, the screens, the cause, who fixes it (app or flow or capture), and the command to verify.
3. Open `index.html` (a row per language, a column per screen, problems outlined in red, the reason under each cell) and confirm at least one screenshot per group by eye. Say which you looked at.
4. Report `notes` separately: they do not fail the check.
5. Finish with the order to fix in, and the recapture command. Do not say "all correct" unless `problems` is empty and `exit` is 0; say what the check could not judge (scripts macOS can't read, `check` run without `--app`).

## Problem lines and what they mean

| Line (fixed part) | Cause | Fix belongs to |
|---|---|---|
| `<locale>/<file>: shows <x> strings (N lines) more than <y> (M)` | the screenshot shows another language's strings | capture: recapture that locale. App: if `<x>` is the base language on only some screens, those strings are untranslated in the app |
| `<locale>/<file>: text looks like '<x>', expected '<y>'` | same, judged by language detection (no `--app`, or a short screen) | recapture; pass `--app` for a firmer verdict |
| `the caption is in <x> but the app UI shows ...` | a translated marketing caption over an untranslated app | app: translate the UI, or the listing has no honest screenshots in that language |
| `identical image in N languages: a, b, ...` | the same picture in several languages: a copy, or a screen with no text that changes | usually the same root cause as a wrong-language line; if the screen is legitimately language-neutral it is not a bug |
| `<locale>: missing a.png, b.png` | that locale lacks screens the others have | capture: the flow failed or skipped them; recapture, read the maestro log |
| `<locale>: the app has no <locale> translation, so this listing shows another language; translate the app into it or remove the listing` | a store listing exists for a language the app does not ship | product: translate the app into it, or remove that listing's screenshots; recapturing cannot fix it |
| `no text found (blank or still loading?)` | blank or half-loaded screen | flow: wait before `takeScreenshot` |
| `has transparency (an alpha channel); both stores reject it` | store rule | the images: flatten the PNG (no alpha channel) |
| `isn't an App Store screenshot size`, `is outside Google Play's 320-3840 px` | store rule | capture at a store size |
| `the App Store takes at most 10`, `Google Play takes at most 8` | too many screenshots in a listing | remove extras |
| `iPhone screenshots need a 6.9" or 6.5" set` | wrong iPhone size set | capture on a 6.9" device |
| `the app runs on iPad, so the App Store requires 13" iPad screenshots` | missing iPad set | add `"iPad Pro 13-inch (M5)"` to `device_types` |

## Which locale to recapture

- Wrong language or missing screens for locale L: recapture L only, `shotfleet run <config> --locales L`, then `shotfleet check` again.
- Several locales fail the same screen: the flow or the app is at fault, not the locales; fix that first, then recapture them together.
- A locale with `the app has no <locale> translation`: do not recapture.
- Store-rule problems apply to every file of the listing, usually one cause (the device size).

## When the fix belongs in the app

Tell the developer plainly, with the screen and language, when:

- a string shows in the base language in one locale only: it is missing from that locale's strings file (untranslated);
- a screen is only reachable in English: a button sits below the bottom edge in a longer language (shotfleet's real example: a Next button nobody could reach in Japanese, Korean, Chinese and Arabic); `scrollUntilVisible` in the flow only works around it, the layout needs fixing;
- a language is in the store listing but not in the app;

## When the fix belongs in the flow

A tap that hit the wrong element after a `warning ... also means ...` line, selectors listed as not found, late dialogs,
a screen captured before it loaded. See the `shotfleet` skill's `references/flow-writing.md`.

## Output template

```
Result: exit 1, 72 screenshots in 18 languages, 2 issues (5 problem lines), 1 note
1. de, 4 screens show English (lines 1-3: wrong language, copy of en). Cause: <...>. Recapture: shotfleet run shotfleet.toml --locales de
2. zh-Hant: the app has no zh-Hant translation (line 4). Product decision: translate or drop the listing.
Notes: ...
Not judged: <scripts macOS can't read / no --app>
```

## Do not

- Do not call screenshots fine because only `notes` remain without saying so.
- Do not recapture a language to fix an app-side problem; the same wrong screenshot comes back.
- Do not touch the user's fastlane folder, upload anything, or expose the licence key.
