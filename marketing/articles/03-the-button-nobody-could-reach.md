# Article 3: the button nobody could reach

Status: draft for Manu to publish on the new domain. Not published. Written 2026-10-02. This is the founder story that feeds Show HN, newsletters and Reddit comments, so the facts below are pinned to a commit and an image.

| Field | Value |
|---|---|
| Title (H1) | The button nobody could reach: how translated text broke my Android onboarding |
| Meta description (under 160 chars) | In Japanese, Korean, Chinese and Arabic the Next button sat below the screen on a small Android phone. How I found it, the 8-line fix, and how to test for it. |
| Slug | `/the-button-nobody-could-reach` |
| Target query | android button off screen translation / next button not visible small phone / text overflow localization android onboarding / jetpack compose verticalScroll long translations |
| Assets needed | `site/public/img/bug_zh.jpg` (Chinese Training Goals page, no Next button; exists in the repo as of 2026-10-02), and the review-grid image with red outlines once Manu renders it. Add alt text: "Chinese onboarding page with four goal cards and no Next button." |
| Canonical | Our domain; this is the article to submit to newsletters (Android Weekly, Kotlin Weekly, KMP Weekly) and to use in Show HN comments. |

## Internal link plan

- Product: one disclosed link in "How I found it" to `https://DOMAIN/`; last paragraph links `https://DOMAIN/#price`.
- Free command: mention `shotfleet check` only as what it does NOT catch here (honest), and link article 1.
- Article 2 (one Maestro flow per locale) for the "run it in every language" step.
- Site footer links this article. Do not put it behind a signup.

## TO VERIFY BEFORE PUBLISHING

1. App name. The site and flow say "WOD Tracker", the repo and README say CrossfitTracker, the package is `me.manulorenzo.crossfittracker.android.debug`. The draft says "my workout app". Pick one public name and use it everywhere (research/marketing-research.md 4.1 flags this).
2. Which languages were observed. Only the Chinese image is kept (claims C012). The commit message of 687ffccd in the CrossfitTracker repo (2026-10-01) names Japanese, Korean, Chinese and Arabic. Manu should confirm he saw all four stuck, or reword to "Chinese, and by the same layout Japanese, Korean and Arabic".
3. "1080x1920 phone": from the commit message and shotfleet's default emulator size (README: 1080x1920). The image is 360x640 as stored. Confirm density (dp) before you write "360 by 640 dp".
4. The code diff in the article is the real one from commit 687ffccd (8 insertions, 2 deletions in `OnboardingScreens.kt`, two `Column`s). Check that the repo owner is fine with showing the file path and snippet; strip the package path if not.
5. "Users could only leave onboarding via Skip": from the commit message; the image shows a Skip control ("跳过") top right. Confirm Skip really exits onboarding.
6. Whether a published release of the app shipped the bug. The article says "my app". It must not say real users were stuck unless Manu knows. The commit message says "those users could only leave onboarding via Skip", which implies the shipped layout; confirm and decide the wording.
7. How shotfleet found it: claims C013 says the capture got stuck (the run surfaced it) and that `check` would NOT find it. The article is written that way. Confirm from the run log if one exists (none is kept in the repo).
8. The free repro steps (`adb ... set-app-locales`, small AVD) are unrun; see article 2 item 4. The font-size line is not included on purpose.
9. Jetpack Compose snippet: it is the app's own change and compiles there; the generic text around it ("any scrollable container") is standard Android advice and was not run.

Sources: commit 687ffccd (read-only, CrossfitTracker repo, read 2026-10-02); `examples/crossfittracker/android.yaml` (the flow with `scrollUntilVisible`); claims C012 (evidence), C013, C014; README Tips; Maestro `scrollUntilVisible` page https://docs.maestro.dev/reference/commands-available/scrolluntilvisible (default: an element counts as visible when fully displayed).

---

# The button nobody could reach: how translated text broke my Android onboarding

My workout app is in 18 languages. Its onboarding has three intro pages, then experience level, training goals, equipment and a summary. Every page has a Next button at the bottom.

On a small Android phone, in Japanese, Korean, Chinese and Arabic, the Next button on the Training Goals page was below the bottom of the screen. The page did not scroll. English fit, so nobody had noticed, including me.

![Chinese onboarding page with four goal cards and no Next button](https://DOMAIN/img/bug_zh.jpg)

The screenshot above is the Chinese page on a 1080 by 1920 emulator. Four goal cards, a Skip link top right, and no way forward. The text in those four languages runs taller than English in the same font size, and the cards pushed the button off the bottom.

## How I found it

I was running my onboarding in every language the app ships, on a store-size emulator, to capture Play Store screenshots. The tool I built for that is shotfleet: it takes one English Maestro flow, rewrites the taps for each language and runs them in parallel. On the Android run, the capture for those four languages got stuck on the same page, because the flow could not tap Next. The tool's output lists any language that did not produce every screenshot, so the four languages stood out.

I want to be exact about this: the tool did not detect "a button is off screen". The capture got stuck, and I looked at why. Its `check` command, which reads finished screenshots, would not have found this either, because a screenshot of a page with a missing button is not wrong in any way it can see. What found the bug was running the real app, in every language, on a phone-sized screen, and looking at where it stopped.

## The fix

It was a small fix: the Training Goals and Experience Level pages got a vertical scroll, like the Equipment page already had. The change is 8 added lines and 2 removed in one file:

```kotlin
// Scrolls so Next stays reachable when long translations (ja, ko, zh, ar) outgrow small screens.
Column(
    modifier = Modifier
        .padding(horizontal = 24.dp)
        .verticalScroll(rememberScrollState()),
    horizontalAlignment = Alignment.CenterHorizontally,
) { /* the page content */ }
```

The Experience Level page had the same layout. It only fit by luck: its text happened to be short enough. I fixed both.

## Why a test flow did not save me

My Maestro flow already had a `scrollUntilVisible` before each Next tap:

```yaml
- scrollUntilVisible:
    element:
      text: "Next"
    direction: DOWN
```

That is the right habit for long languages, and it is in my own tips. But it only helps if the page can scroll. On a page with no scroll container there is nothing to scroll, the button stays hidden, and the step times out. Per Maestro's docs an element counts as visible only when it is fully displayed in the viewport by default, so a button that sits half under the edge counts as not visible too.

## How to test for this in your own app

1. Pick the languages with the longest text. In my case they were Japanese, Korean, Chinese and Arabic.
2. Use a small screen. A big emulator hides the problem. I used 1080 by 1920.
3. Walk the whole onboarding, not just the home screen, in each language, and fail loudly if the primary button is not visible. In Maestro, put an `assertVisible` on the button text at the end of each page, or use `scrollUntilVisible` and treat a timeout as a bug in the app, not in the test.
4. On Android 13 or newer you can set one app's language without changing the phone's. Article 2 shows the command and the traps.
5. Do it for every language you ship. I would not have guessed which four it would be.

If your layout is a fixed `Column`, make it scroll or pin the primary button outside the scrolling content. Either fixes this class of bug.

## What I did not find

This is one bug in one app, found on one screen size. I do not know how common it is, and I would not claim that a tool catches "all localization bugs". It does not. It found this one because it ran the whole flow in every language and the flow could not finish.

## When not to use shotfleet

If your app has a few languages and you already click through them before a release, you do not need it. If your onboarding is short and fixed, a manual run in your longest language on a small phone is enough. shotfleet needs an Apple silicon Mac, Maestro 2.x, Java 17+, the Android SDK with API 33+ emulators, and a Maestro flow you write; it makes no frames or captions and does not upload to the stores. Its `check` command is free and it is `run` that needs a licence beyond 2 languages: $29 for the first 100 buyers, then $49 once, with a 14-day refund (https://DOMAIN/#price).

If you ship in more than a handful of languages and have never watched your onboarding in all of them on a small phone, that is the thing I would do first.
