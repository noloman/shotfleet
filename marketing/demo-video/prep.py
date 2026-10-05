#!/usr/bin/env python3
"""Prepare the Remotion project's inputs from the session recordings (ffmpeg only; no devices).

    python3 marketing/demo-video/prep.py [--session DIR]

For every clip whose recording exists in SESSION/rec/: cut and speed up the terminal recording into remotion/public/rec/<clip>.mp4
(a `run` keeps its first RUN_HEAD and last RUN_TAIL seconds in real time and squeezes the middle into RUN_SHOWN seconds), copy the
run's 01_welcome screenshots for the grid into public/shots/, copy clips/<clip>.srt into public/srt/ after checking the subtitle
rules, and write remotion/src/manifest.json (durations, speed, grid). Prints each clip's timeline so the .srt can be timed.
"""
import json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO, RM = HERE.parents[1], HERE / "remotion"
SESSION = Path(sys.argv[sys.argv.index("--session") + 1]) if "--session" in sys.argv else \
    Path.home() / "Developer/shotfleet-rc-build/demo-video/session"
FPS, INTRO, OUTRO, FADE = 30, 60, 60, 10           # frames; FADE = each transition's overlap
RUN_HEAD, RUN_TAIL, RUN_SHOWN = 4.0, 6.0, 12.0

# label: the intro card; grid: the run output folder shown after the terminal, and for how long (s);
# wait: (from s, to s, shown s) of the recording where a command was working with nothing new on screen: played faster, with a badge
CLIPS = {
    "c1-doctor":         dict(label="Is this Mac ready?", wait=(2.4, 7.2, 1.6)),
    "c2-init":           dict(label="Set up a project"),
    "c3-run-ios":        dict(label="Every language on iPhone", run=True, grid=("out-ios", 6.0)),
    "c4-run-android":    dict(label="Every language: Android", run=True, grid=("out-android", 5.0)),
    "c5-check":          dict(label="Catch the wrong language"),
    "c6-check-existing": dict(label="Check the screenshots you have"),
    "c7-store-rules":    dict(label="Store rules, checked"),
    "c8-export":         dict(label="Export to fastlane"),
    "c9-ci":             dict(label="In CI"),
}

def duration(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True, check=True).stdout)

def ff(*a): subprocess.run(["ffmpeg", "-y", "-v", "error", *a], check=True)

def srt_cues(path):
    """[(start, end, lines)]; fails on a cue that breaks the owner's rules (<= 42 chars, <= 2 lines, >= 1.5 s)."""
    cues = []
    for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8").strip()):
        ls = block.strip().splitlines()
        g = [int(x) for x in re.match(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", ls[1]).groups()]
        a, b = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        lines = ls[2:]
        assert 1 <= len(lines) <= 2 and all(len(l) <= 42 for l in lines) and b - a >= 1.5, f"{path.name} cue {ls[0]} breaks the rules"
        cues.append((a, b, lines))
    return cues

def main():
    pub = RM / "public"
    for d in ("rec", "shots", "srt", "fonts"): (pub / d).mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO / "site/public/fonts/geist-mono-latin.woff2", pub / "fonts")
    shutil.copy(REPO / "site/public/favicon.svg", pub)
    manifest = {}
    for name, c in CLIPS.items():
        src = SESSION / "rec" / f"{name}.mp4"
        if not src.is_file(): continue
        dur, dst = duration(src), pub / "rec" / f"{name}.mp4"
        # real time, then the squeezed stretch (frames dropped, not blended), then real time again
        a, b, shown = (RUN_HEAD, dur - RUN_TAIL, RUN_SHOWN) if c.get("run") else c.get("wait", (0, 0, 0))
        speed = (b - a) / shown if shown else 1.0
        if speed > 1:
            ff("-i", str(src), "-filter_complex",
               f"[0:v]trim=0:{a},setpts=PTS-STARTPTS[a];[0:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{speed}[b];"
               f"[0:v]trim={b},setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3,fps={FPS}[v]",
               "-map", "[v]", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-an", str(dst))
        else:
            ff("-i", str(src), "-vf", f"fps={FPS}", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-an", str(dst))
        body = round(duration(dst) * FPS)
        grid, grid_f = [], 0
        if "grid" in c:
            out, secs = c["grid"]
            for dev in sorted(p for p in (SESSION / "myapp" / out).iterdir() if (p / "raw").is_dir()):
                items = []
                for lang in sorted(p.name for p in (dev / "raw").iterdir() if (p / "01_welcome.png").is_file()):
                    rel = f"shots/{name}/{dev.name}/{lang}.jpg"
                    (pub / rel).parent.mkdir(parents=True, exist_ok=True)
                    ff("-i", str(dev / "raw" / lang / "01_welcome.png"), "-vf", "scale=-2:900", "-q:v", "3", str(pub / rel))
                    w, h = map(int, subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0",
                                                    str(pub / rel)], capture_output=True, text=True).stdout.strip().split(","))
                    items.append(dict(lang=lang, src=rel, w=w, h=h))
                grid.append(dict(device=dev.name, items=items))
            grid_f = round(secs * FPS)
        scenes = [INTRO, body] + ([grid_f] if grid_f else []) + [OUTRO]
        total = sum(scenes) - FADE * (len(scenes) - 1)
        srt = HERE / "clips" / f"{name}.srt"
        if srt.is_file():
            cues = srt_cues(srt)
            assert cues[-1][1] <= total / FPS + 0.01, f"{srt.name} runs past the clip ({total / FPS:.2f} s)"
            shutil.copy(srt, pub / "srt" / srt.name)
        else: print(f"  note: no {srt.relative_to(REPO)} yet")
        manifest[name] = dict(label=c["label"], body=body, grid=grid, gridFrames=grid_f, speed=round(speed, 1),
                              spedFrom=round(a * FPS), spedFrames=round(shown * FPS), spedReal=round(b - a), total=total)
        t, starts = 0, []
        for s in scenes: starts.append(t / FPS); t += s - FADE
        print(f"{name}: {total / FPS:.2f} s; scenes start at " + ", ".join(f"{x:.2f}" for x in starts)
              + (f"; body {a:.1f}-{a + shown:.1f} s sped up {speed:.0f}x ({b - a:.0f} s real)" if speed > 1 else ""))
    (RM / "src" / "manifest.json").write_text(json.dumps(dict(fps=FPS, intro=INTRO, outro=OUTRO, fade=FADE, clips=manifest), indent=1))

if __name__ == "__main__": main()
