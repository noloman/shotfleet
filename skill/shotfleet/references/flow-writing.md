# Writing the English flow

One [Maestro](https://maestro.mobile.dev) flow, written in English, serves every language and both platforms.
shotfleet rewrites the text selectors for each language from the strings compiled into the build (or from the
files named by `strings`). Never write one flow per language.

`shotfleet init` writes this starter; extend it:

```yaml
- launchApp
- waitForAnimationToEnd:
    timeout: 5000
- takeScreenshot: 01_home
# - tapOn: "Settings"
# - takeScreenshot: 02_settings
```

No `appId:` header is needed: shotfleet sets each build's own id, so one flow serves iOS and Android.

## What gets translated

Text written in these keys is replaced by the language's string (or a pattern matching every translation of it):
`tapOn`, `doubleTapOn`, `longPressOn`, `assertVisible`, `assertNotVisible`, `scrollUntilVisible`, `copyTextFrom`,
`text`, `visible`, `notVisible`, and the anchors `below`, `above`, `leftOf`, `rightOf`, `childOf`, `containsChild`.
Both `tapOn: "Next"` and `tapOn: { text: "Next", optional: true }` work.

Write the label exactly as it appears in the English strings ("Next", not "next"). If "Next" has two keys, the
selector matches both translations. Labels with numbers ("Round 2 of 12") are matched and translated with the same
numbers, in every plural form. Selectors with `id:` pass through untouched: use them for icons and for anything
without text.

## What is not translated

- **Typed text**: `inputText` is not rewritten, so demo data (a name, a search term) stays the same in every language. Pick demo data that reads fine everywhere.
- **System dialogs** (permission prompts) are drawn in the device language, which stays English even when the app runs in German. Write those taps in English: `tapOn: "Allow While Using App"`, `"Don’t Allow"`, `"OK"`; shotfleet keeps the English text matchable (and also matches the app's own translated button).
- Labels that are not in the app's strings are left as written and listed under `selectors not found in the app's strings`. Fix by writing the exact English string, using `id:`, or `[overrides.<lang>]` (see config.md).

## Screenshots

- `takeScreenshot: 01_home` per store image. Number them: names sort the grid's columns, and every language must produce the same set of names.
- shotfleet counts the `- takeScreenshot:` steps; a language that ends with fewer files fails (`flow passed but took N of M screenshots`) and is retried once. So never put a `takeScreenshot` behind an `optional` or conditional branch that can differ per language.
- The map form also works: `- takeScreenshot:` with `path: 01_home` below.
- Take the shot after the screen settles: `waitForAnimationToEnd`, or `assertVisible: "<a label on that screen>"`. A blank or half-loaded screen is reported as `no text found (blank or still loading?)`.
- Screenshots are 1320x2868 on iOS (iPhone 17 Pro Max, App Store 6.9") and 1080x1920 on Android phones, with the status bar fixed at 9:41.

## Collisions

`warning tr: 'Next' -> 'İleri' also means 'Advanced'; anchor that step (below:/above:) if it taps the wrong element`
means two different English labels share one translation, so a tap could hit the wrong one. Fix before the full run:

```yaml
- tapOn:
    text: "Next"
    below: "Step 2 of 3"
```

or pin the translation for that language in the config:

```toml
[overrides.tr]
"Next" = "İleri"
"Advanced" = "re:Gelişmiş.*"     # "re:" means a regular expression
```

## Dialogs that appear late

Disclaimers and consent screens show up after a variable delay. Loop until the first real screen is visible, not a
fixed wait:

```yaml
- repeat:
    while:
      notVisible: "Welcome"
    times: 15
    commands:
      - tapOn: { text: "Accept", optional: true }
```

## Long languages push buttons off-screen

Longer languages wrap or grow text. A button that is reachable in English may sit below the bottom edge of a
small phone (this is how shotfleet found a Next button nobody could reach in Japanese, Korean, Chinese and Arabic).
Add a scroll before tapping (write the label under `text:` so it is translated):

```yaml
- scrollUntilVisible:
    element:
      text: "Next"
- tapOn: "Next"
```

If the button cannot be reached even by scrolling, that is a bug in the app's layout, not in the flow: tell the user.

## launchApp

- The first `launchApp` becomes shotfleet's fresh-state launch (clean install, language arguments added). Later `launchApp` steps also get the language arguments.
- Options can be a block (below) or on one line, `- launchApp: { permissions: { all: allow } }`; shotfleet reads both. `- launchApp: com.example.app` sets the app id:

```yaml
- launchApp:
    permissions:
      all: allow
```

- `permissions: all: allow` skips the iOS permission prompts altogether. On Android shotfleet installs with every permission granted.
- Do not use `clearState` to reset between languages: each language already starts from a clean install. On Android `clearState` would also erase the app language, so shotfleet drops it from the flow and clears the app's data itself.

## Dry checks before a long run

1. `shotfleet run <config> --locales en` (the flow in the base language; boots simulators, takes minutes).
2. Then one hard language: `--locales de` (long) or `--locales ja` (CJK), read the `warning` and `selectors not found` lines.
3. Open `<out>/index.html`: a row per language, a column per screen, problems outlined in red.
4. Only then the full `shotfleet run`.
