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

The mark is built by `marketing/logo/build.py` (see `marketing/logo/README.md`): three fanned phones, the front one yellow with a check. `icon.svg` and `icon-1024/512.png` are the master icon (gradient, soft shadows); `icon-64.png` is the flat favicon version, which holds better at small sizes. The covers and thumbnail draw the master icon's cards without the tile.
