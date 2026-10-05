# shotfleet feature clips

Nine short clips, one per feature, from one real session on the repo's fixture apps (`tools/fixture-app`, `tools/fixture-app-android`):
1920x1080 and 1080x1080 MP4 (H.264, 30 fps, silent), subtitles burned in and also shipped as `.srt` next to each MP4.
Nothing here is uploaded anywhere; the owner decides placement.

CLIP_TABLE

## What is real and what is composited

- **Real:** every terminal frame is a VHS recording of the real command running in a real shell on this Mac (`tapes/*.tape`), and every
  screenshot in the grids is a PNG that run wrote (`session/myapp/out-ios`, `out-android`). One device run (clips 3 and 4) feeds clips 5 to 9.
- **Not live:** shotfleet runs from this repo's source (`session/bin/shotfleet` calls `shotfleet.py`), not from the installed program;
  the install line is shown as text and was not run. Clip 2 copies a prepared config and flow in, visibly (`cp ../edits/...`).
  The planted problems (clips 5 and 7) are made on copies of the real output, visibly, in the recording.
- **Composited (Remotion):** intro and outro cards, subtitles, the "sped up" badge, fades, the screenshot grids' layout and motion,
  the square crop. Sped-up stretches are cut with ffmpeg (frames dropped, not blended) and are always labelled with the factor
  on screen and the real time in the subtitle.

## Rebuild

```sh
sh marketing/demo-video/session.sh                     # fresh demo project in ~/Developer/shotfleet-rc-build/demo-video/session (wipes myapp/)
cd ~/Developer/shotfleet-rc-build/demo-video/session
vhs tapes/c1-doctor.tape; vhs tapes/c2-init.tape       # device-free tapes write rec/<clip>.mp4
python3 <repo>/marketing/demo-video/record_devices.py   # c3 + c4: detached, waits for and takes the shared device lock, releases it
vhs tapes/c8-export.tape; vhs tapes/c5-check.tape; vhs tapes/c6-check-existing.tape; vhs tapes/c7-store-rules.tape; vhs tapes/c9-ci.tape
sh <repo>/marketing/demo-video/render.sh               # prep.py + Remotion: out/<clip>.mp4, <clip>-square.mp4, <clip>.srt, poster.png
```

- `prep.py` cuts and speeds up the recordings (ffmpeg), copies the grid screenshots and the `.srt` files into `remotion/public/`,
  checks the subtitle rules (at most 42 characters a line, 2 lines, 1.5 s or more) and prints each clip's timeline (when the terminal,
  grid and outro start) so the `.srt` can be retimed. The waits that are sped up are set in `prep.py` (`wait=`, and runs).
- Change wording: edit `clips/<clip>.srt`, then `sh render.sh` (no re-recording).
- Preview and tweak: `cd remotion && npx remotion studio`.
- Outro price lines: in `remotion/src/Clip.tsx` (`PRICE`); they are the site's own sentences. Remove them when the launch price ends.
- The device tapes need simulators and emulators: follow `docs/device-queue.md`. `record_devices.py` waits until the lock has been
  free 3 minutes and `/tmp/shotfleet-quiet-check.sh` passes, holds it with a hard limit per tape (40 and 30 min), shuts down only the
  pool simulators and 57xx emulators that appeared during its run, and releases the lock.

## Tools and licences

- VHS 0.12.1 and ttyd 1.7.7 (Homebrew; VHS is MIT), ffmpeg (already installed), Node 26.
- Remotion 4.0.533 (`remotion/package.json`): free for individuals and companies of up to 3 people, commercial use allowed
  (https://www.remotion.pro/license); the owner is a solo developer. Its first render downloads Chrome headless shell into
  `remotion/node_modules/.remotion` (193 MB, not committed).
- The Remotion agent skills (github.com/remotion-dev/skills: best-practices, captions, render, markup, create) were installed
  project-scoped in the worktree's `.claude/skills/` for authoring and are kept out of git (`.git/info/exclude`).
- Font: Geist Mono (SIL OFL 1.1), copied from `site/public/fonts` by `prep.py`. No music, no voice.
