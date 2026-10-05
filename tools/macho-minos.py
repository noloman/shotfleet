#!/usr/bin/env python3
"""Which macOS does a built shotfleet folder need? Reads every Mach-O file's minimum macOS (LC_BUILD_VERSION `minos`, or the old
LC_VERSION_MIN_MACOSX `version`) and its architectures, prints one line per (architectures, minos) and the highest minos.

    python3 tools/macho-minos.py dist/shotfleet            # informational, exit 0
    python3 tools/macho-minos.py dist/shotfleet --max 14   # exit 1 when some file needs a newer macOS than 14

Why: Homebrew's Python is built for the macOS it was built on (27.0 measured on 2026-10-05), so a PyInstaller folder made from it needs that
macOS; a python.org or python-build-standalone interpreter needs macOS 11 (research/limits-platform-reach-2026-10-05.md). Needs `otool`, `lipo`, `file` (macOS).
"""
import collections, subprocess, sys
from pathlib import Path


def minos(otool_l):
    """The minimum macOS in `otool -l` text, as a tuple like (13, 0), or None. Only macOS platforms count: an iOS-simulator file's minos is an iOS version."""
    lines = [l.split() for l in otool_l.splitlines()]
    for i, w in enumerate(lines):
        if w[:1] == ["cmd"] and w[1:] == ["LC_VERSION_MIN_MACOSX"]:
            return next((tuple(int(x) for x in v[1].split(".")) for v in lines[i:i + 4] if v[:1] == ["version"]), None)
        if w[:1] == ["cmd"] and w[1:] == ["LC_BUILD_VERSION"]:
            block = lines[i:i + 8]
            if not any(v[:2] == ["platform", "MACOS"] or v[:2] == ["platform", "1"] for v in block): continue
            return next((tuple(int(x) for x in v[1].split(".")) for v in block if v[:1] == ["minos"]), None)
    return None


def scan(folder):
    """{(architectures, minos tuple or None): [files]} for every Mach-O file under folder."""
    found = collections.defaultdict(list)
    for f in sorted(Path(folder).rglob("*")):
        if f.is_symlink() or not f.is_file(): continue
        if "Mach-O" not in subprocess.run(["file", "-b", str(f)], capture_output=True, text=True).stdout: continue
        archs = subprocess.run(["lipo", "-archs", str(f)], capture_output=True, text=True).stdout.strip() or "?"
        found[(archs, minos(subprocess.run(["otool", "-l", str(f)], capture_output=True, text=True).stdout))].append(f)
    return found


def main(argv):
    folder = argv[0] if argv else "dist/shotfleet"
    limit = (*(int(x) for x in argv[argv.index("--max") + 1].split(".")), 0)[:2] if "--max" in argv else None  # "14" means 14.0
    found = scan(folder)
    if not found: print(f"no Mach-O files under {folder}"); return 0
    for (archs, m), files in sorted(found.items(), key=lambda kv: (kv[0][1] or (0,), kv[0][0])):
        print(f"{len(files):4} file(s)  {archs:<14} needs macOS {'.'.join(map(str, m)) if m else 'unknown'}")
    top = max((m for _, m in found if m), default=None)
    if top: print(f"this build needs macOS {'.'.join(map(str, top))} or newer (not a promise that it works there: only a run on that macOS shows that)")
    return 1 if limit and top and top > limit else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
