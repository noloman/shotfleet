# Gumroad image set

Written 2026-10-05 (rebuilt the same day after a worktree reset). Nothing here is uploaded or committed. Total folder size under 1 MB.

## Gumroad specs

Gumroad's own help pages could not be read: `gumroad.com/help/article/42-adding-a-product-to-your-account` and `.../45-product-thumbnail-and-cover` return only an empty "Gumroad Help Center" shell (the page is rendered by script), and `help.gumroad.com/article/44-product-images-and-cover` redirects (302) to `gumroad.com/help`. So these sizes are **not confirmed from Gumroad itself**. What was found, all third party:

- https://www.pixelmeasures.com/platform-sizes/gumroad/ : product cover 1280 x 720 (16:9), thumbnail 600 x 600 (1:1), profile picture 600 x 600. The page itself says Gumroad does not consistently publish exact sizes and calls these practical targets (page last verified 3 May 2026). It names no maximum file size.
- Web search summaries (topbubbleindex.com, justhandledlabs.com, pixelmeasures.com): cover 1280 x 720; thumbnail at least 600 x 600; if no thumbnail is set Gumroad crops one from the centre of the cover, so keep key content centred.
- `research/gumroad-setup.md`, "Product tab": thumbnail 600 x 600.

Decision: 1280 x 720 covers, 600 x 600 thumbnail, all PNG, sRGB, 8 bit, all under 300 KB each. Max file size is unknown; nothing here is near any plausible limit. Check the upload dialog for any warning.

## Files

| File | Size | Purpose and where it goes |
|---|---|---|
| `thumbnail-600.png` | 600 x 600 | Product tab, **Thumbnail** (shown in the library, Discover, and the profile grid). Checked at 200 x 200. |
| `cover-1.png` | 1280 x 720 | Product tab, **Cover 1** (the one people see first): hero. |
| `cover-2.png` | 1280 x 720 | **Cover 2**: the problem and the fix. |
| `cover-3.png` | 1280 x 720 | **Cover 3**: one flow, every language. |
| `cover-4.png` | 1280 x 720 | **Cover 4**: the check, with one planted failure. |
| `icon-1024.png` | 1024 x 1024, RGBA | Master icon (transparent rounded corners). Keep for any store or listing that wants a large icon. |
| `icon-512.png` | 512 x 512, RGBA | Gumroad **profile picture** (Settings, Profile) and general icon use. The glyph fits inside a circle if Gumroad crops round. |
| `icon-64.png` | 64 x 64, RGBA | Small placements. Checked at 64 and 32 px (the 32 px render is not saved; export it from `icon.svg` if needed). |
| `icon.svg` | vector | Editable master of the icon. |
| `src/build.py` | script | Builds the thumbnail and the four covers (Pillow). |

Rebuild:

```sh
python3 marketing/gumroad/images/src/build.py
cd marketing/gumroad/images
rsvg-convert -w 1024 -h 1024 icon.svg -o icon-1024.png   # likewise -w 512, -w 64
```

## Icon

The mark is the one in `site/public/favicon.svg`: same flag glyph (`M7 8h18l-4.5 8L25 24H7z` in a 32 unit box), same rounded square (radius 7/32). Two changes: the glyph is enlarged from 56% to 64% of the width so it holds at 32 px, and the colours are the site tokens `--ink` #0b1220 and `--yellow` #f5c400 instead of the favicon's #0d1b2a and #f6c21b (the brief limits the palette to the tokens; the difference is not visible). If you want the favicon and the icon identical, change the two fills in `icon.svg`.

## Text on each image and where it comes from

IDs are in `tests/claims.json`; "site" means `site/public/index.html`, "llms" means `site/public/llms.txt`.

**thumbnail-600.png**
- "shotfleet": the name.
- "Store screenshots in every language your app ships." (3 lines): the hero `<h1>` in site, verbatim. The same sentence is the og.jpg headline.

**cover-1.png**
- Chip "Mac command-line tool · Apple silicon": site hero flag; C002 (Mac command-line tool), C033 (Apple silicon Mac).
- Headline: the site `<h1>`, verbatim.
- "One English Maestro flow, every language, iOS and Android.": site hero sub; C001.
- "shotfleet captures them all and checks every screenshot.": site hero sub; C003.
- Footnote "Seven of 72 screenshots from one run on my app, WOD Tracker: 18 languages × 4 screens on an M1 Pro.": site, under the hero grid; C005.
- Language codes ar de fr es ja ko ru under the phones; green check on each phone (the "checked" stamp of the site hero, C005).
- Tile "+11 more languages in the same run": site, last tile of the hero row; C005.
- Screenshots (all WOD Tracker, one screen "Train", from the real 18-language run, same files as the site hero): `site/public/img/train_ar.jpg`, `train_de.jpg`, `train_fr.jpg`, `train_es.jpg`, `train_ja.jpg`, `train_ko.jpg`, `train_ru.jpg`.

**cover-2.png**
- "THE PROBLEM", "THE FIX": labels.
- "A flow that taps "Next" only works in English.": **not a claims.json statement**. It restates `marketing/kit/demo-video.md` shot 2 ("A Maestro flow taps English buttons") and the site's flow section (C015: the flow says Next, each language gets its own word). Reword or drop it if you want only verbatim site text.
- "Japanese, Korean, Chinese and Arabic all got stuck on one onboarding page of my app: Next was below the bottom of a small phone. English fit, so nobody noticed.": site "catch" section; C012, C106. Real bug, not planted. It does not say shotfleet detected it.
- Red chip "zh · Next is off-screen": the site's own label on this image (C012).
- "shotfleet reads the translations compiled into your build and rewrites every text selector.": site flow section, verbatim; C015.
- Screenshot: `site/public/img/bug_zh.jpg` (Chinese onboarding page, small Android phone). No scaling above 100%.

**cover-3.png**
- "One flow, every language.": heading; C001.
- "Your flow says Next. Each language gets its own word.": the site's flow-section `<h2>`, verbatim; C015.
- `flow.yaml` card, three lines `- tapOn: "Next"`, `- tapOn: "Log"`, `- takeScreenshot: 02_log`: real lines, in file order, from `examples/crossfittracker/ios.yaml` (other lines of the file sit between them). "(English, once)" is a caption; C001, C018.
- `shotfleet.toml` card, `[ios]` and `app = "MyApp.app"`: the two-line config as the site shows it (site bento, docs "The whole config can be this"); C018. The experiment config in `research/experiments-2026-10-04/C/shotfleet.toml` has four lines and a local path, so it was not used. "(two lines)" is a caption.
- "what each language runs": German `tapOn: '(Nächste|Weiter)'`, Japanese `tapOn: '次へ'`, Turkish `tapOn: 'İleri'`: site flow row, verbatim; C015, C016. "Warning before the run: it also means "Advanced".": site; C017 (set apart from the Turkish line with extra space).
- Screenshots: the same seven `train_*.jpg` as cover 1, cropped at the bottom edge (shown from the top of the screen down).

**cover-4.png**
- "Then every screenshot is checked.": heading; C003.
- "Every image is read back and compared with your app's own strings.": site run section, verbatim; C009.
- "Problems are outlined in red.": site docs ("problems are outlined in red"); C029.
- "planted to test the check" (red chip) and "The Spanish slot holds the French image. Copies: the same image in two languages.": demo-video.md rule 3. **The red tile is a planted failure**: the `es` slot shows `train_fr.jpg` on purpose, next to the real `fr` tile. "Copies: the same image in two languages." is C025 (also llms). Nothing on the image presents it as a bug found in the wild.
- "check is free for everyone. run is free for up to 2 languages.": llms "Price and licence", verbatim (without the backticks); C032, C048, C049. No price is on the image because the Gumroad page shows it.
- Layout: the real review grid has a row per language and a column per screen (C029). Only one real screen exists per language in `site/public/img`, so the tiles are laid out as one row of languages. No tool output text is reproduced or retyped.
- Screenshots: `train_ar.jpg`, `train_de.jpg`, `train_fr.jpg` (twice, planted in the `es` slot), `train_ja.jpg`, `train_ko.jpg`, `train_ru.jpg`.

## Rules checked (marketing/kit/demo-video.md, "Rules for the footage")

- Only screenshots from `site/public/img` (the WOD Tracker `train_*` set from the real run, and `bug_zh.jpg`). The Stressi and Cairn images are store screenshots of other apps, not shotfleet output, so they are not used.
- No other company's logo. The WOD Tracker screens contain a sample user first name ("Jason") inside the app, as on the live site; no other personal data.
- No claim about frames, captions, store upload, Flutter, React Native, or Maestro endorsement. "Maestro" appears only as the tool the flow is written for (site wording).
- No numbers other than those in C005 (72, 18, 4, +11, M1 Pro) and the "2 languages" free tier.

## Fonts and colours

- Geist Mono (SIL OFL 1.1; `site/public/fonts/geist-mono-latin.woff2` and `-latin-ext.woff2`, licence in `site/public/fonts/LICENSE.txt`), variable weight, used for all text. The latin-ext file supplies the Turkish dotted capital I.
- Hiragino Sans W6 (macOS system font) for the Japanese word 次へ on cover 3 only.
- Colours: `--ink` #0b1220, `--blue` #1b3fd1, `--yellow` #f5c400, `--paper` #f1f2f4, `--line` #cfd5de, `--muted` #55627a, terminal text #dbe6f3 and dim #7f93ab, `--red` #c8281c and `--pass` #17693a (dark-theme #ff6b5e on the dark cover), all from `site/public/site.css`.
