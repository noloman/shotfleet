#!/usr/bin/env python3
"""Compare Apple's App Store screenshot specification page with shotfleet's size table: tools/apple-specs-watch.py

Apple changed these rules three times in the three months to October 2026 (8 Jul no alpha, 19 Aug Watch, 9 Sep iPhone Duo and new Watch sizes), and
`check` tells buyers "this isn't an App Store screenshot size" from APPLE_SIZES in shotfleet.py. This fetches the page, reads every
"W x H pixels" size on it and reports sizes that are on the page but unknown to shotfleet, and sizes shotfleet knows that the page no longer lists.
Orientation does not matter (each size is compared as its shorter and longer side).

Exit 0: the table matches the page. Exit 1: they differ (update APPLE_SIZES, add a test, note it in CHANGELOG). Exit 2: the page could not be read or
no longer looks like the specification (fewer than MIN_SIZES sizes), which is reported as a failure, never as "no change".
It checks sizes only; Apple's count, alpha and required-set rules are prose and stay a human read (docs/handoff.md item 12).
SHOTFLEET_APPLE_SPECS_URL overrides the URL (tests use a local server); GITHUB_STEP_SUMMARY, when set, gets a short report.
"""
import html, os, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf

URL = os.environ.get("SHOTFLEET_APPLE_SPECS_URL",
                     "https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications")
MIN_SIZES = 40  # the page lists about 70 (portrait and landscape); far fewer means the layout changed under the parser


def page_sizes(page):
    """{(short side, long side)} for every 'W x H pixels' on the page, and how many mentions there were."""
    page = re.sub(r"(?is)<(script|style)\b.*?</\1>", "", page)
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)  # "1,320" is 1320
    found = re.findall(r"(\d{3,4}) ?[x×] ?(\d{3,4}) ?pixels", text)
    return {tuple(sorted((int(a), int(b)))) for a, b in found}, len(found)


def table_sizes():
    return {tuple(sorted(s)) for sizes in sf.APPLE_SIZES.values() for s in sizes}


def compare(page, table):
    """(sizes only on the page, sizes only in shotfleet's table)."""
    return sorted(page - table), sorted(table - page)


def main():
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": f"shotfleet-tools/{sf.VERSION}", "Accept": "text/html"})
        with urllib.request.urlopen(req, timeout=60, context=sf.tls_context()) as r: page = r.read().decode("utf-8", "replace")
    except OSError as e:
        print(f"apple-specs-watch: can't read {URL}: {e}", file=sys.stderr); return 2
    sizes, mentions = page_sizes(page)
    if mentions < MIN_SIZES:
        print(f"apple-specs-watch: only {mentions} sizes found on the page (expected about 70): the page changed shape or moved; read it by hand",
              file=sys.stderr); return 2
    new, gone = compare(sizes, table_sizes())
    lines = [f"{mentions} size mentions on the page, {len(sizes)} distinct, {len(table_sizes())} in shotfleet's table"]
    lines += [f"NEW on the page, unknown to shotfleet: {a}x{b} (as shorter x longer side)" for a, b in new]
    lines += [f"in shotfleet's table, no longer on the page: {a}x{b}" for a, b in gone]
    print("\n".join(lines))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write("### Apple screenshot sizes\n\n" + "".join(f"- {l}\n" for l in lines) + "\n")
    if new or gone:
        print("\nupdate APPLE_SIZES in shotfleet.py (and its test), then read the page for new prose rules: " + URL)
        return 1
    print("the size table matches Apple's page; count, alpha and required-set rules still need a human read")
    return 0


if __name__ == "__main__":
    sys.exit(main())
