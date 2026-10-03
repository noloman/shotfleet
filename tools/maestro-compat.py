#!/usr/bin/env python3
"""Check a Maestro against everything shotfleet relies on, without a device: tools/maestro-compat.py [MAESTRO_DIR | path/to/maestro]

Looks at what can be seen without booting anything:
  - `maestro --version` parses, and what shotfleet will say about it (tested / newer / older)
  - `maestro --help` and `maestro test --help` still list the flags shotfleet passes, and --format still offers JUNIT
  - the jars still contain the log line shotfleet parses to learn which emulator ran which flow, the variables it sets, and the flow keys
    it writes (a string that is gone from the jars is a strong sign the feature is)
  - whether this Maestro defines MAESTRO_DEVICE_UDID (an improvement for Android [inputs]; not required)

What the list is: shotfleet.MAESTRO_INTERFACE. This is a screen, not a test: a version that passes here still needs a real run
(tools/fixture-e2e.sh) before it goes into MAESTRO_TESTED. Exit 0 when nothing required is missing, 1 otherwise, 2 for a usage problem.
"""
import os, re, shutil, subprocess, sys, zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf


def find_maestro(arg):
    """(bin/maestro, lib folder) from a Maestro folder, the bin/maestro path, or shotfleet's own lookup."""
    cands = []
    if arg:
        p = Path(arg).expanduser()
        cands += [p / "bin/maestro", p / "maestro/bin/maestro", p]
    elif (found := sf.maestro_cmd()):
        cands.append(Path(shutil.which("maestro") if found == "maestro" else found))
    for c in cands:
        if c.is_file() and os.access(c, os.X_OK) and (c.resolve().parent.parent / "lib").is_dir():
            c = c.resolve(); return c, c.parent.parent / "lib"
    return None, None


def run(cmd, timeout=180):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env={**os.environ, **sf.java_env(), "MAESTRO_CLI_NO_ANALYTICS": "1",
                                                                                 "MAESTRO_DISABLE_UPDATE_CHECK": "1"})
    return r.stdout + r.stderr


def scan_jars(lib, needles):
    """{needle: [jar names]} for every needle found in the .class files of the Maestro jars. Needles are looked up as UTF-8 bytes."""
    found = {n: set() for n in needles}
    wanted = {n: n.encode() for n in needles}
    for jar in sorted(lib.glob("*.jar")):
        if not re.search(r"maestro|server", jar.name): continue  # third-party libraries say nothing about Maestro's interface
        try:
            with zipfile.ZipFile(jar) as z:
                for name in z.namelist():
                    if not name.endswith((".class", ".kotlin_module")): continue
                    data = z.read(name)
                    for n, b in wanted.items():
                        if b in data: found[n].add(jar.name)
        except (zipfile.BadZipFile, OSError): continue
    return found


def check(maestro, lib, out=print):
    """Run every check; returns (passed, failed, notes). `out` receives one line per check."""
    iface = sf.MAESTRO_INTERFACE
    passed = failed = 0
    def result(ok, what, detail=""):
        nonlocal passed, failed
        passed, failed = passed + ok, failed + (not ok)
        out(f"{'PASS' if ok else 'FAIL'}  {what}" + (f"  ({detail})" if detail else ""))

    version = sf.parse_maestro_version(run([str(maestro), "--version"]))
    result(bool(version), "maestro --version prints a version", version or "unreadable")
    if version:
        note = sf.maestro_warning(version)
        out(f"INFO  shotfleet's view: {'tested version' if note is None else note}")
        result(int(version.split(".")[0]) >= 2, "it is Maestro 2 or newer", version)

    for cmd, flags in iface["cli"].items():
        text = run([str(maestro), *cmd.split()[1:], "--help"])
        for flag in flags:
            result(bool(re.search(rf"(?<![\w-]){re.escape(flag)}(?![\w-])", text)), f"`{cmd} --help` lists {flag}")
        if cmd == "maestro test":
            for value in iface["format_values"]:
                result(value in text, f"`{cmd} --help` offers --format {value}")

    needles = [n for group in iface["class_strings"].values() for n in group] + iface["nice_to_have"]
    found = scan_jars(lib, needles)
    for group, names in iface["class_strings"].items():
        for n in names:
            result(bool(found[n]), f"jars still contain {group} string {n!r}", ", ".join(sorted(found[n]))[:60] if found[n] else "gone")
    for n in iface["nice_to_have"]:
        out(f"INFO  {n}: {'defined by this Maestro (' + ', '.join(sorted(found[n]))[:60] + ')' if found[n] else 'not defined'}")
    return passed, failed, version


def main(argv):
    maestro, lib = find_maestro(argv[1] if len(argv) > 1 else None)
    if not maestro:
        print("maestro-compat: no Maestro found; pass its folder (the one with bin/ and lib/) or bin/maestro", file=sys.stderr); return 2
    print(f"checking {maestro}")
    try: passed, failed, version = check(maestro, lib)
    except subprocess.TimeoutExpired:
        print("FAIL  maestro did not answer within 180 s (is Java installed? shotfleet doctor --fix)"); return 1
    print(f"\n{passed} passed, {failed} failed" + (f" for Maestro {version}" if version else ""))
    if failed: print("not compatible as it stands: look at the FAIL lines before trying a real run")
    else: print("nothing required is missing; a real run (tools/fixture-e2e.sh) is still needed before adding it to MAESTRO_TESTED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
