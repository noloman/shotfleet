# 4. Export and store rules

Back to the [index](../ARCHITECTURE.md). Anchors are `shotfleet.py:LINE` at `origin/main` `285e099`. Sources of truth for the numbers:
`research/store-specs.md` (raw page text of Apple's and Google's rules fetched 2026-10-01) and `tools/apple-specs-watch.py` (compares Apple's page with
`APPLE_SIZES`).

## 4.1 Export

`export <out> --fastlane <dir>` (`cmd_export`, `:4691`; wrapped by `export_with_hooks`, `:5268`, which runs the `before_export` and `after_export`
hooks found through `run.json`'s `config` path). It needs a licence in released builds (`main_dispatch`, `:5368`). It **copies**; it never uploads and
never deletes a screenshot it did not replace.

Steps:

1. **Multi-device runs.** If `out` holds `out/<device>/run.json` sub-folders (`device_runs`, `:4678`), refuse when an iPad-capable app has no 13" iPad
   set (`ipad_set_missing`, `:1857`), then export each sub-folder with the file-name prefix `<device>_` so the iPhone and iPad sets can share one
   language folder (sizes differ; the screen names are the same on every device).
2. **Preconditions.** `out/run.json` (a shotfleet run) or loose `*/*.png` (a hand-made set); and `out/check.json` must exist, else `Fail("hasn't been
   checked. Run 'shotfleet check ...' first")`. The hand-made case is App Store layout only, PNG only (a `ponytail:` comment says so).
3. **Which languages are bad.** A language is skipped if any problem line names it (the first path segment of `<locale>/<file>: ...`; for
   `identical image in ...` lines every file named), or if `run.json` says it failed (`ok` false) or its folder has no PNGs. A bad screenshot
   can therefore never replace a good listing.
4. **Map app locales to store listings.** `store_code(app_locale, store)` (`:272`) returns the listing code in `APP_STORE` or `PLAY`, or `None` ("skip:
   the App Store has no listing in that language"). Examples: `de` to `de-DE`, `nb` to `no`, `zh-Hant-HK` to `zh-Hant`, `iw` to `iw-IL`, `es-MX` to
   `es-419`. When a language has several listings and the locale names no region, `PRIMARY` (`:260`) picks one (`en` to `en-US`, `pt` to `pt-BR`,
   `zh` to `zh-Hans`). The tables are exactly fastlane's `deliver` and `supply` folder names (`marketing/store-locales.md`, 2026-10-01).
5. **Keep the user's spelling.** If the fastlane folder already has `nb-NO` or `he-IL` for that language, that folder is used, not a new `no/`.
6. **Fill sibling listings.** A listing the user already has in the same language (`en-GB`, `es-419`, `pt-PT`) that the app has no translation for
   gets the screenshots of the app language (`en`, `es`, `pt`), with a printed line saying so.
7. **Write.** iOS: `<fastlane>/screenshots/<listing>/`. Android: `<fastlane>/metadata/android/<listing>/images/<folder>/` where `<folder>` is
   `phoneScreenshots`, `tenInchScreenshots` or `sevenInchScreenshots` from the run's `device`. Inside it, existing PNGs **of the same pixel size** as
   the new ones are replaced (`png_size`); PNGs of other sizes (iPad, a 6.5" set) stay. Files are copied with `shutil.copy2`. The destination folder is built with `inside(root, ...)` (`:52`), which refuses a path that resolves outside the fastlane folder (security finding S3), so a listing name cannot walk out of it.
8. **Result.** Prints `exported N listings to <dir>: ...`, fills `EXPORT_RESULT` (`exported`, `skipped`) for `--json`, returns 0, or 1 if any language was
   skipped.

fastlane layouts shotfleet reads or writes:

| Tool | Layout | Notes |
|---|---|---|
| `deliver` (iOS upload) | `screenshots/<store locale>/*.png` | written by `export`; also the layout `check` reads for iOS |
| `supply` (Play upload) | `metadata/android/<store locale>/images/{phone,sevenInch,tenInch}Screenshots/*.png` | written by `export`; read by `check` |
| `snapshot` (iOS capture) | `screenshots/<locale>/*.png` | no `export` needed; point `check` at it |
| `screengrab` (Android capture) | `metadata/android/<locale>/images/phoneScreenshots/<name>_<13-digit ms timestamp>.png` | `check` strips the timestamp when matching screens |
| supply with the locale in names | `de-DE/1_de-DE.png` | `check` strips the locale suffix only when every file in the folder has it |

shotfleet does not touch `Fastfile`; the README shows lanes that run `shotfleet check` between `snapshot`/`screengrab` and `deliver`/`supply`.

## 4.2 Store size and count rules

`store_rules(images, android, ipad=False, tablet=False)` (`:4583`) is pure: it takes `{label: [files]}` and returns `(problems, notes)`. **Problems are
what the store rejects; notes are worth knowing and do not block an upload.** Image size and alpha come from `image_info` (`:4556`), which reads the
PNG header or the first JPEG SOF marker; no image library is used.

### Both stores

- **Not a PNG or JPEG the stores accept:** problem.
- **Alpha channel:** `png_alpha` (`:4527`) distinguishes "no alpha", "opaque alpha" and "transparent". Both stores forbid the channel itself, so
  both are problems with different wording ("has an alpha channel, though every pixel is opaque" versus "has transparency"), and both say how to fix
  it (`sips -s format jpeg in.png --out out.jpg`). XCUITest attachments and design tools save the opaque kind. It tells opaque from transparent without
  decoding pixels: PNG filters work byte by byte on the same byte of the previous pixel or row, so an all-opaque alpha channel filters to one fixed
  pattern per filter type, and any row that differs holds a see-through pixel. A `tRNS` chunk or an interlaced PNG counts as transparent without a closer
  look (a `ponytail:` comment).

### App Store (`android` is False)

`APPLE_SIZES` (`:4509`, Apple's table of 2026-10-01, Duo added 2026-10-03) maps display classes to accepted pixel sizes:

| Class | Sizes (portrait; iPhone and iPad also accepted rotated) |
|---|---|
| iPhone 6.9" | 1260x2736, 1290x2796, 1320x2868 |
| iPhone 6.5" | 1284x2778, 1242x2688 |
| iPhone 6.3", 6.1", 5.5", 4.7", 4", 3.5" | listed in the constant |
| iPhone Duo (outer, inner) | 1398x2034, 2007x2853 |
| iPad 13" | 2064x2752, 2048x2732 |
| iPad 11", 10.5", 9.7" | listed in the constant |
| Apple Watch | six sizes from 422x514 down to 312x390 |
| Mac | 1280x800, 1440x900, 2560x1600, 2880x1800 |
| Apple TV / Vision Pro | 1920x1080, 3840x2160 (the 4K size is both) |

Problems: a size in no class ("isn't an App Store screenshot size"); more than 10 screenshots of one class in a listing; iPhone screenshots with
neither a 6.9" nor a 6.5" set; an app that runs on iPad (`UIDeviceFamily` contains 2 in `Info.plist`) with no 13" iPad set; Apple Watch screenshots whose size
differs from the usual one across languages (Apple wants one Watch size in every localization).

### Google Play (`android` is True)

Problems: a side under 320 or over 3,840 px; more than 8 phone screenshots in a listing.
Notes: more than 2:1 (Google's rule says no; Play has accepted 20:9 in practice); fewer than 4 screenshots at 1080 px or more in exactly 9:16 or 16:9
(Google then will not consider the listing for recommendations; the emulator sizes are chosen to make this pass); tablet screenshots (`tablet`
is true for 7" and 10" folders) under 1080 px on the short side.

### Unknown store (`android` is None)

Only what **both** stores reject is a problem: "fits neither store" (not an App Store size and outside 320-3,840). Alpha and format rules still apply.

### Why these are in `check`, not only in `export`

Screenshots made elsewhere (fastlane, designers, Paparazzi) never pass through `export`, and a size or alpha rejection is discovered after upload,
the most expensive moment. Apple changed these rules three times in the three months to October 2026 (no alpha on 8 July, Watch on 19 August, iPhone Duo and
new Watch sizes on 9 September), so `tools/apple-specs-watch.py` compares the live page with `APPLE_SIZES` and `tools/watch-upstream.sh` runs it with the Maestro
watcher on the maintainer's machine (no scheduled GitHub Action; the workflow is `workflow_dispatch` only). It checks sizes only; count, alpha and
required-set rules are prose and need a human read.

## 4.3 Changing a store rule

1. Update the constant (`APPLE_SIZES`, the limits in `store_rules`, or `ANDROID_DEVICES` sizes for emulators).
2. Add a unit test in `tests/test_shotfleet.py` (the store-rule classes) that builds tiny PNGs and asserts the problem or note line.
3. Update `research/store-specs.md` with the page text and date (the file keeps raw text on purpose), and `CHANGELOG.md`.
4. If a site or README sentence names the rule ("at most 10 (App Store) or 8 (Play) per listing"), it is a claim row; the claims test names the file to update.
5. Run `python3 tools/apple-specs-watch.py` to confirm the table now matches Apple's page.
