#!/usr/bin/env python3
"""Web versions of the rendered clips, for shotfleet.com, into marketing/demo-video/web/:

    python3 marketing/demo-video/web.py [OUT]      # OUT = render.sh's folder (default ~/Developer/shotfleet-rc-build/demo-video/out)

<slug>.mp4 (1280x720) and <slug>-square.mp4 (1080x1080): H.264, yuv420p, faststart, no audio; CRF raised until each is <= 4 MB.
<slug>-poster.webp (<= 150 KB, a frame from the terminal part), <slug>.en.vtt (from clips/<clip>.srt), manifest.json.
Descriptions use only site claims or what the clip shows; edit them here (DESC).
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Developer/shotfleet-rc-build/demo-video/out"
WEB = HERE / "web"
MAX_MB, POSTER_KB = 4.0, 150

# slug: (title, description). Every sentence is a site claim (tests/claims.json, site/public/*.html) or visible in the clip.
DESC = {   # same wording as site/public/demo.html (branch claude/site-human-voice); c3 and c8 differ: this run had no iPad set
    "c1-doctor": ("Is this Mac ready?", "shotfleet doctor --fix checks Maestro, Java, Xcode and the Android SDK, and fetches what is missing after asking once."),
    "c2-init": ("Set up a project", "shotfleet init reads an iOS simulator build and an Android APK, lists the languages each one has, and writes a config and an English flow."),
    "c3-run-ios": ("Every language on iPhone", "The English Maestro flow runs in every language the app has, on several iPhone simulators at once. Then every screenshot is checked."),
    "c4-run-android": ("Every language on Android", "The same English flow runs in every language on Android emulators. Then every screenshot is checked."),
    "c5-check": ("Catching the wrong language", "I put a German screenshot in the Japanese folder, and shotfleet check caught it. The real output passes with 0 problems."),
    "c6-check-existing": ("Checking screenshots you already have", "shotfleet check reads fastlane folders or a plain folder of screenshots. You don't need a simulator for this."),
    "c7-store-rules": ("Store rules", "shotfleet check flags screenshot sizes the stores refuse. It also flags a missing 13-inch iPad set."),
    "c8-export": ("Export to fastlane", "One command puts the passing Google Play screenshots into fastlane's folders."),
    "c9-ci": ("In CI", "The GitHub Actions setup from the docs, with the --json result and the exit code from check."),
}
# poster: the second of the clip that shows the result (not the intro card)
POSTER_AT = {"c1-doctor": 12.0, "c2-init": 19.0, "c3-run-ios": 27.0, "c4-run-android": 26.5, "c5-check": 14.0,
             "c6-check-existing": 18.0, "c7-store-rules": 23.0, "c8-export": 13.0, "c9-ci": 22.0}

def run(*a): return subprocess.run(a, capture_output=True, text=True, check=True).stdout
def dur(p): return float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)))

def encode(src, dst, scale):
    for crf in (24, 27, 30, 33, 36):
        run("ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", f"scale={scale}:flags=lanczos,format=yuv420p", "-c:v", "libx264",
            "-preset", "slow", "-crf", str(crf), "-profile:v", "high", "-movflags", "+faststart", "-an", str(dst))
        if dst.stat().st_size <= MAX_MB * 1e6: return crf
    return crf

def vtt(srt):
    body = re.sub(r"(\d\d:\d\d:\d\d),(\d\d\d)", r"\1.\2", srt.read_text(encoding="utf-8").strip())
    return "WEBVTT\n\n" + body + "\n"

def main():
    WEB.mkdir(exist_ok=True)
    m = json.loads((HERE / "remotion/src/manifest.json").read_text())
    fps, items = m["fps"], []
    for slug, c in m["clips"].items():
        master = OUT / f"{slug}.mp4"
        if not master.is_file(): continue
        files = {}
        crf = encode(master, WEB / f"{slug}.mp4", "1280:720"); files["mp4"] = f"{slug}.mp4"
        if (OUT / f"{slug}-square.mp4").is_file():
            encode(OUT / f"{slug}-square.mp4", WEB / f"{slug}-square.mp4", "1080:1080"); files["square"] = f"{slug}-square.mp4"
        t = POSTER_AT[slug]
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "p.png"
            run("ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(WEB / f"{slug}.mp4"), "-frames:v", "1", str(png))
            im = Image.open(png).convert("RGB")
            for q in (80, 70, 60, 50, 40):
                im.save(WEB / f"{slug}-poster.webp", "WEBP", quality=q, method=6)
                if (WEB / f"{slug}-poster.webp").stat().st_size <= POSTER_KB * 1024: break
        files["poster"] = f"{slug}-poster.webp"
        (WEB / f"{slug}.en.vtt").write_text(vtt(HERE / "clips" / f"{slug}.srt")); files["captions"] = f"{slug}.en.vtt"
        title, desc = DESC[slug]
        sped = []
        if c["speed"] > 1:
            sped.append(dict(from_s=round((m["intro"] - m["fade"] + c["spedFrom"]) / fps, 1), shown_s=round(c["spedFrames"] / fps, 1),
                             factor=int(c["speed"]), real_s=c["spedReal"]))
        items.append(dict(slug=slug, title=title, description=desc, duration_s=round(dur(WEB / f"{slug}.mp4"), 1),
                          files={k: dict(path=v, bytes=(WEB / v).stat().st_size) for k, v in files.items()},
                          sped_up=sped, facts=FACTS.get(slug, []), burned_in_subtitles=True))
        print(f"{slug}: crf {crf}, " + ", ".join(f"{v} {(WEB / v).stat().st_size / 1e6:.2f} MB" for v in files.values()))
    (WEB / "manifest.json").write_text(json.dumps(dict(
        note="Real terminal recordings (VHS) and real screenshots from one run of the repo's fixture apps; cards, subtitles, badges and grid layout composited with Remotion. Source: marketing/demo-video/README.md",
        clips=items), indent=1, ensure_ascii=False) + "\n")
    total = sum(p.stat().st_size for p in WEB.iterdir())
    print(f"web total {total / 1e6:.1f} MB")

FACTS = json.loads((HERE / "facts.json").read_text()) if (HERE / "facts.json").is_file() else {}

if __name__ == "__main__": main()
