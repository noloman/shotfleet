# shotfleet product video (Gumroad page)

`shotfleet-product.mp4`: 44.2 s, 1920x1080, 30 fps, H.264, silent, burned-in captions, about 1.9 MB. `poster.png`: 1280x720 cover, built by the same script (the seven-language grid with the site headline, not a frame of the video). Nothing is uploaded or committed.

**What is NOT in the video:** there is no live screen recording and no device was used. The terminal text is replayed (typed out) from a saved log of a real run, and says so on screen; the flow and config text is copied from real files; the screenshots are the real images already on the site. The 18-language run, the review grid, `init` and `check` are not shown, and no failure is planted.

## Scene table

Times are in the final video. Every caption is on screen for 2.6 s or more. Each scene fades through the dark background for 0.25 s at its start and end.

| Time | On screen | Caption | Source in the repo | Statement behind the caption |
|---|---|---|---|---|
| 0.0-8.8 | Chinese onboarding page, slow zoom toward the empty bottom. Left: "zh / Android, small phone". From 3.0 s a yellow bracket "Next should be down here." labelled "(annotation, not part of the screenshot)" | 0.3-3.0 "Chinese, small Android phone: Next is off-screen." / 3.0-5.8 "Japanese, Korean, Chinese and Arabic all got stuck here." / 5.8-8.8 "English fit, so nobody noticed." | `site/public/img/bug_zh.jpg` | C012, C106; site section "The first run found a button nobody could reach" (text: "English fit, so nobody noticed.") |
| 8.8-12.2 | Code card of a real flow, `"Next"` in yellow | 9.1-12.0 "You write one flow, in English." | `examples/crossfittracker/ios.yaml` lines 26-29, verbatim | C001, C018 |
| 12.2-15.6 | Code card of a real config | 12.5-15.4 "Plus a short config: your app and your languages." | `research/experiments-2026-10-04/C/shotfleet.toml` lines 1-4. Only the two long paths are cut in the middle with a visible `…` (and the source line says so) | C018 (the site says "a two-line config"; this real file has four lines because the sample needs `strings` and `locales`, so the caption says "short", not "two-line") |
| 15.6-20.0 | Three cards appear one by one: English flow, German, Japanese | 15.9-19.8 "shotfleet rewrites the text for every language." | `research/experiments-2026-10-04/C/flow.yaml` lines 4-5; `translated-de.yaml` lines 11-12; `translated-ja.yaml` lines 11-12, all verbatim | C015, C001. Same real run as the log below (commit cbf5f38) |
| 20.0-28.4 | Terminal card labelled "OUTPUT OF A REAL RUN, REPLAYED FROM A SAVED LOG. NOT LIVE." and "2 languages, 1 simulator, a sample app. Replayed fast: the real run took 394 s." Lines typed at 80 characters per second; the last line gets a green box around `0 problem(s)` | 20.3-24.2 "Then shotfleet run captures every language." / 24.2-28.2 "And reads each screenshot back to check it." | `research/experiments-2026-10-04/C/run.log` lines 1-7 verbatim (line 6 is empty and shown as an empty line). Typing starts: line 1 at 20.6 s, line 2 21.6, line 3 22.5, line 4 23.0, line 5 24.6, line 7 25.8. The trailing `run rc=0 secs=510` line of the file is not shown | C003, C009, C048 ("capture up to 2 languages"). The run is the .NET MAUI LocalizationDemo sample (experiment C), 2 of the 18 languages, 1 simulator; the screen says "a sample app" |
| 28.4-35.8 | Seven screenshots appear one by one (0.45 s apart), language code and a green check under each | 28.7-32.2 "Seven of 72 screenshots from one real run, all checked." / 32.2-35.8 "18 languages x 4 screens: 9 minutes on iOS, 15 on Android." | `site/public/img/train_ar.jpg, train_de.jpg, train_es.jpg, train_fr.jpg, train_ja.jpg, train_ko.jpg, train_ru.jpg` (not the stressi_* and cairn_* images: the site says those are real store screenshots, not shotfleet output) | C005 (seven of 72, WOD Tracker, M1 Pro, "checked" on each), C007, C105; hero text in `site/public/index.html` |
| 35.8-44.2 | End card, staged: name 36.2 s; free line 37.4 s; price lines 39.4 s; requirements and `shotfleet.com` 41.2 s | none (text only) | `site/public/llms.txt`, "Price and licence" bullets, read at build time: "`check` is free for everyone. `run` is free for up to 2 languages." and the first sentence of the next bullet, "A licence unlocks every language and `export`: $29 for the first 100 buyers, then $49, once per developer." Backticks are not drawn; the code words `check`, `run`, `export` are yellow. Requirements line "Apple silicon Mac, Maestro 2.x, Java 17+" joins two llms.txt "Requirements" bullets ("An Apple silicon Mac." and "Maestro 2.x and Java 17+") | C032, C048, C042, C033 |

The price lines are only true while the sale is live. Without them: `PRICE=0 bash src/build.sh`.

Source tags (small grey text at the bottom of each scene) name the repo file shown. The header mark is `site/public/favicon.svg`.

## Fonts

- Geist Mono, variable weight (SIL Open Font License 1.1): `site/public/fonts/geist-mono-latin.woff2`, licence in `site/public/fonts/LICENSE.txt`. All Latin text.
- Hiragino Sans W3 (macOS system font, `/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc`) for the Japanese characters in the translated flow card only (Geist Mono has no CJK). It is rendered into the video, not shipped.
- Terminal and code text is 36-40 px at 1080p, about 27-30 pt equivalent.

## Rebuild

```
bash marketing/gumroad/video/src/build.sh     # about 75 s; needs python3 + Pillow, ffmpeg with libx264, rsvg-convert
```

`src/build.py` reads every image, log line, flow line and licence sentence from the repo paths above at build time (line ranges are in the script), draws each frame with Pillow and pipes raw frames to ffmpeg. There are no intermediate frame files. Captions are the only text typed in the script; they are listed above. This ffmpeg build has no drawtext, which is why the text is drawn with Pillow.

ffmpeg 9.0.2 (Homebrew build on this Mac). Exact encode command (the script's own):

```
ffmpeg -y -f rawvideo -pix_fmt rgb24 -s 1920x1080 -r 30 -i - \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p" \
  -c:v libx264 -preset slow -crf 18 -profile:v high -level 4.0 \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -movflags +faststart -an shotfleet-product.mp4
```

## Before you upload

- Cut the price lines (`PRICE=0`) if the Gumroad sale is not live.
- Not made: the optional 20 s cut and a square crop.
