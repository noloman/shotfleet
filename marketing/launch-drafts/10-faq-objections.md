# FAQ and objections: short replies for comment threads

Plain answers you can paste and change. Answer what was asked, don't reply to criticism with the price, and say "I don't know, I'll check" when that's the truth. Longer versions of some of these are in `marketing/kit/show-hn.md`; where they differ, this file is newer (a real Flutter app has run since, and Homebrew exists).

Every reply already reads as you, the maker. In a thread where you haven't said it yet, start with "I made it, so I'm biased:".

---

### "Mac only? Why not Linux or Windows?"

> Yes, Apple silicon Macs only, macOS 13 or later. iOS simulators need a Mac, and check uses the text recognition built into macOS. There's no Intel build. My full runs were on macOS 27; on 14 and 15 I've run the installer, doctor and check, not full runs. If you're on Linux, I can't help you yet, sorry.

### "Only Maestro? We don't use Maestro."

> For capturing, yes, today it's Maestro: one flow in English, and shotfleet rewrites it for each language. Running your own XCUITest screenshot tests on iOS is coming in 0.1.6; it's not out yet. And `check` doesn't need Maestro at all: it works on screenshots from fastlane snapshot, screengrab or a plain folder per language, and it's free.

### "$49 for a screenshot tool? fastlane is free."

> Fair. fastlane is free and good. If your UI tests already run in every language and you're happy, you don't need this, and check is free anyway. What the licence pays for: one flow for iOS and Android instead of UI-test code per platform, no test code in your app, every language in one run, and the export. It's $29 for the first 100 buyers, then $49 once, not a subscription, with a 14-day refund. If you try the free parts first and don't see the point, don't buy it.

### "Why not fastlane snapshot / screengrab?"

> Keep them if they work for you. snapshot and screengrab need UI-test code (XCUITest and Espresso), separate for iOS and Android, and they don't check the language of what they captured. shotfleet uses one Maestro flow for both and reads every screenshot afterwards. They also work together: run shotfleet check on the folder snapshot or screengrab writes. On a real fastlane snapshot set, it found a German listing whose app was still in English.

### "How is this different from ButterKit or AppScreens?"

> Different job. They make frames, captions and marketing images (ButterKit also captures from the iOS Simulator and uploads). shotfleet makes the raw screenshots of your app in every language and checks they're really in that language. No frames, no captions. You can use shotfleet first and then put the results in ButterKit or AppScreens.

### "What leaves my machine? Privacy?"

> Your app and your screenshots are never uploaded; everything runs on your Mac. The licence key is checked with Gumroad when you activate and about once a week after that (the key and the product ID, no Mac name). check, doctor and init need no licence. The site's own privacy page has the details: https://shotfleet.com/privacy

### "Closed source and curl | sh? No thanks."

> Understood, and I won't argue it away. If you'd rather not pipe a script: `brew install noloman/tap/shotfleet` installs the same signed build. The install script is short, so you can read it first. And check needs no key and no account, so you can try the part that reads screenshots without paying or signing up.

### "What about refunds?"

> 14 days, no questions asked. Email hello@shotfleet.com with your order email. It goes back through Gumroad to the way you paid. check and the 2 free languages keep working after a refund.

### "What's free?"

> No account, no licence: check (on any screenshots, also fastlane folders), doctor, init, and run for up to 2 languages, on both platforms and every device size. The licence adds every language and export to fastlane. Open-source maintainers and students can email me for a free licence.

### "Does it work with Flutter / React Native?"

> It works from your translation files (for Flutter, ARB), because those apps don't keep their strings readable in the build. I've run one real Flutter app end to end (wger, iOS and Android) and one real Expo app (the obytes template). Not more yet, and not bare React Native. If you try yours, I'd like to hear how it goes.

### "Does it need changes in my app?"

> No code changes. You need a simulator build for iOS and emulators with Android 13 or newer for per-app languages. One case I haven't tested: apps with their own in-app language picker that overrides the system language.

### "How long does a run take?"

> One run on my M1 Pro: 18 languages x 4 screens, 9 minutes on iOS and 15 on Android, on Maestro 2.0.10. That's my app on my Mac. Yours will be different; startup time, memory and Mac load all matter. On a loaded Mac with little memory it uses fewer simulators and takes longer.

### "Does it catch every localization bug?"

> No. It reads text: wrong language, copies, missing screens, blank screens, store sizes. It doesn't judge layout. The unreachable Next button I talk about wasn't "detected": the run got stuck on that page and I looked at why.

### "Can it run in CI?"

> check can, on any macOS runner, with no simulator: `--json` for the result, exit code 0 for all good, 1 for problems, 2 for a setup error. The docs have a GitHub Actions setup. For run and export in CI you use a CI key (`SHOTFLEET_KEY`), which doesn't use one of your 3 Mac activations.

### "Is the $29 thing real or fake urgency?"

> Real: Gumroad applies the $29 price to the first 100 sales by itself, then it's $49. I can't show a live count of what's left, because Gumroad doesn't give me one to show. [If asked how many are sold: say the true number. It was 0 on 2026-10-06.]

### "Why should I trust a solo developer's tool?"

> You shouldn't, blindly. That's why the check is free and the refund is 14 days. Everything the site claims has a dated record of what I ran (https://shotfleet.com/demo). If something on it is wrong, tell me and I'll fix it.
