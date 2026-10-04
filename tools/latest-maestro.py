#!/usr/bin/env python3
"""Screen the newest Maestro release against what shotfleet relies on: tools/latest-maestro.py

Finds the newest stable cli-X.Y.Z release of mobile-dev-inc/maestro, downloads its maestro.zip (checked against the release's
checksums_sha256.txt when it has one), and runs tools/maestro-compat.py on it. Exit 0: nothing required is missing. Exit 1: something
shotfleet needs is gone (the job that runs this weekly turns red, which is the alarm). Exit 2: no release could be found or fetched.

It prints whether that version is one shotfleet was tested with (MAESTRO_TESTED). A compatible but untested version is NOT an error: it
means "worth a real run" (docs/handoff.md item 1). SHOTFLEET_MAESTRO_RELEASES overrides the releases URL (tests use a local server);
GITHUB_TOKEN, when set, is sent to avoid the anonymous API rate limit; GITHUB_STEP_SUMMARY, when set, gets a short report.
"""
import importlib.util, json, os, re, shutil, sys, tempfile, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf

RELEASES = os.environ.get("SHOTFLEET_MAESTRO_RELEASES", "https://api.github.com/repos/mobile-dev-inc/maestro/releases?per_page=30")


def load_compat():
    spec = importlib.util.spec_from_file_location("maestro_compat", ROOT / "tools/maestro-compat.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def newest_cli_release(releases):
    """(version, zip url, checksums url or None) of the newest published, non-pre-release cli-X.Y.Z release that has a maestro.zip, else None."""
    best = None
    for r in releases:
        m = re.fullmatch(r"cli-(\d+)\.(\d+)\.(\d+)", str(r.get("tag_name", "")))
        if not m or r.get("draft") or r.get("prerelease"): continue
        assets = {a.get("name"): a.get("browser_download_url") for a in r.get("assets", [])}
        if not assets.get("maestro.zip"): continue
        key = tuple(int(g) for g in m.groups())
        if best is None or key > best[0]: best = (key, ".".join(m.groups()), assets["maestro.zip"], assets.get("checksums_sha256.txt"))
    return best[1:] if best else None


def checksum_for(text, filename="maestro.zip"):
    """The SHA-256 listed for `filename` in a checksums file ("<hash>  <name>" lines), or None."""
    for line in (text or "").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip("*").split("/")[-1] == filename and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]): return parts[0].lower()
    return None


def version_tuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def verdict(version):
    """One line on where `version` stands against the versions shotfleet was tested with."""
    if version in sf.MAESTRO_TESTED: return f"{version} is a version shotfleet was tested with"
    newest_tested = max(sf.MAESTRO_TESTED, key=version_tuple)
    if version_tuple(version) > version_tuple(newest_tested):
        return f"{version} is newer than anything shotfleet was tested with ({', '.join(sf.MAESTRO_TESTED)}): if it passes below, it still needs a real run (docs/handoff.md item 1)"
    return f"{version} is older than the tested versions ({', '.join(sf.MAESTRO_TESTED)})"


def main():
    headers = {"Accept": "application/vnd.github+json", "User-Agent": f"shotfleet-tools/{sf.VERSION}"}
    if os.environ.get("GITHUB_TOKEN"): headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    try:
        with urllib.request.urlopen(urllib.request.Request(RELEASES, headers=headers), timeout=60, context=sf.tls_context()) as r:
            releases = json.loads(r.read())
        release = newest_cli_release(releases)
    except (OSError, ValueError) as e:
        print(f"latest-maestro: can't read the release list: {e}", file=sys.stderr); return 2
    if not release:
        print("latest-maestro: no stable cli-X.Y.Z release with a maestro.zip in the list", file=sys.stderr); return 2
    version, zip_url, sums_url = release
    print(f"newest Maestro release: {version}\n{verdict(version)}")

    work = Path(tempfile.mkdtemp(prefix="latest-maestro-"))
    try:
        want = None
        if sums_url:
            want = checksum_for(sf.fetch_text(sums_url))
            print(f"checksum from the release: {want[:16] + '...' if want else 'not listed for maestro.zip'}")
        else:
            print("the release publishes no checksum file; the download is not verified")
        zpath = sf.download(zip_url, work / "maestro.zip", sha256=want, label=f"Maestro {version}")
        sf.extract_zip_safely(zpath, work / "x")
        top = next((d for d in (work / "x" / "maestro", work / "x") if (d / "bin/maestro").is_file()), None)
        if not top:
            print("latest-maestro: the download has no bin/maestro"); return 1
        compat = load_compat()
        lines = []
        passed, failed, found = compat.check(top / "bin/maestro", top / "lib", out=lambda l: (lines.append(l), print(l)))
        summary = f"Maestro {version}: {passed} passed, {failed} failed. {verdict(version)}"
        print(f"\n{summary}")
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
                f.write(f"### {summary}\n\n" + "".join(f"- {l}\n" for l in lines if l.startswith(("FAIL", "INFO"))) + "\n")
        return 1 if failed else 0
    except sf.Fail as e:
        print(f"latest-maestro: {e}", file=sys.stderr); return 2
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
