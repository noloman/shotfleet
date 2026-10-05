#!/usr/bin/env python3
"""Markdown for the GitHub job summary from shotfleet's --json output. `summarize.py --count FILE` prints the number of problem lines.
Reads only the documented fields: exit, screenshots, problems, notes, reports."""
import json, sys

def load(path):
    try:
        with open(path) as f: return json.load(f)
    except (OSError, ValueError): return None

def main(argv):
    if argv[0] == "--count":
        d = load(argv[1]); print(len((d or {}).get("problems", []))); return 0
    code, path, errlog = argv[0], argv[1], argv[2]
    d = load(path)
    print("## shotfleet")
    if d is None:
        print(f"exit code {code}; no JSON report (setup error, or the doctor command). The last lines of the log:\n")
        try: tail = open(errlog).read().splitlines()[-15:]
        except OSError: tail = []
        print("```\n" + "\n".join(tail) + "\n```"); return 0
    probs = d.get("problems", [])
    print(f"exit code {d.get('exit', code)}: {len(d.get('screenshots', []))} screenshots, {len(probs)} problem line(s)\n")
    for p in probs: print(f"- {p}")
    for n in d.get("notes", [])[:20]: print(f"- note: {n}")
    return 0

if __name__ == "__main__": sys.exit(main(sys.argv[1:]))
