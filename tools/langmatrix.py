"""Measure shotfleet's language check on every language AndroidX is translated into (~85).

For each language L it renders a phone screen of real UI strings, then asks judge_screen three questions:
  ok:      L's screen filed as L                -> must pass
  english: the English screen filed as L        -> must be flagged
  near:    a close language's screen filed as L -> must be flagged (uk/ru, nb/da, pt-PT/pt-BR, sr/sr-Latn, ...)
Usage: python3 tools/langmatrix.py <app.apk> [out_dir] [--tesseract]
--tesseract: languages macOS can't read are read by Tesseract (as `check` does when it's installed)
"""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

KEYS = ["abc_activitychooserview_choose_application", "abc_action_mode_done", "abc_activity_chooser_view_see_all",
        "abc_searchview_description_search", "call_notification_answer_action", "call_notification_decline_action",
        "close_sheet", "fallback_menu_item_copy_link", "fallback_menu_item_open_in_browser",
        "fallback_menu_item_share_link", "confirm_device_credential_password", "fingerprint_not_recognized"]
NEAR = {"uk": "ru", "ru": "uk", "be": "ru", "bg": "mk", "mk": "bg", "sr": "mk", "sr-Latn": "hr", "hr": "bs", "bs": "hr",
        "nb": "da", "da": "nb", "sv": "nb", "pt-PT": "pt-BR", "pt-BR": "pt-PT", "pt": "pt-PT", "es": "pt", "es-US": "es",
        "ca": "es", "gl": "pt", "it": "es", "fr": "fr-CA", "fr-CA": "fr", "en-GB": "en", "en-AU": "en", "en-CA": "en",
        "en-IN": "en", "en": "en-GB", "cs": "sk", "sk": "cs", "sl": "hr", "ms": "in", "in": "ms", "hi": "mr", "mr": "hi",
        "ne": "hi", "ur": "fa", "fa": "ar", "ar": "fa", "zh-CN": "zh-TW", "zh-TW": "zh-HK", "zh-HK": "zh-TW", "ja": "zh-CN",
        "ko": "ja", "th": "lo", "lo": "th", "bn": "as", "as": "bn", "de": "nl", "nl": "af", "af": "nl", "et": "fi", "fi": "et",
        "lv": "lt", "lt": "lv", "tl": "in", "sw": "zu", "zu": "sw", "kk": "ky", "ky": "kk", "uz": "kk", "az": "tr", "tr": "az"}

def main(apk, out, tesseract=False):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    strings = {lp: t for lp, t in sf.load_strings_apk(apk).items() if lp not in ("en-XA", "en-XC", "ar-XB")}
    keys = [k for k in KEYS if all(k in t for t in strings.values())]
    tables = sf.string_tables(strings)
    jobs = [{"out": str(out / f"{lp}.png"), "lines": [strings[lp][k] for k in keys]} for lp in strings]
    (out / "jobs.json").write_text(json.dumps(jobs, ensure_ascii=False))
    subprocess.run([str(Path(sf.__file__).parent / ".build/render"), str(out / "jobs.json")], check=True)
    ocr = sf.ocr_tool()
    with ThreadPoolExecutor(max_workers=8) as ex:
        ocrs = dict(zip(strings, ex.map(lambda lp: json.loads(subprocess.run([ocr, str(out / f"{lp}.png")],
                                                     capture_output=True, text=True).stdout), strings)))
    def unreadable(lp):
        lang = sf.canon(lp).split("-")[0]
        return sf.LEGACY.get(lang, lang) not in sf.readable_languages() | {"zh"}
    def seen_as(img_lp, as_lp):  # what check would read from img_lp's screen in as_lp's folder
        if tesseract and unreadable(as_lp):
            return sf.external_ocr(sf.TESSERACT_COMMAND, out / f"{img_lp}.png", as_lp)
        return ocrs[img_lp]
    rows = []
    for lp in sorted(strings):
        near = NEAR.get(lp, "en" if lp != "en" else "de")
        res = {"lang": lp, "ok": sf.judge_screen(lp, seen_as(lp, lp), tables)[1] is None,
               "english": lp.startswith("en") or sf.judge_screen(lp, seen_as("en", lp), tables)[1] is not None,
               "near": near, "near_caught": strings[near] == strings[lp] or sf.judge_screen(lp, seen_as(near, lp), tables)[1] is not None,
               "verified": sf.judge_screen(lp, seen_as(lp, lp), tables)[0] is not None,
               "english_without_app": lp.startswith("en") or sf.judge_screen(lp, ocrs["en"], {})[1] is not None,
               "ok_without_app": sf.judge_screen(lp, ocrs[lp], {})[1] is None,
               "ok_problem": sf.judge_screen(lp, seen_as(lp, lp), tables)[1], "ocr_chars": ocrs[lp]["chars"]}
        rows.append(res)
    (out / "matrix.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    bad = [r for r in rows if not (r["ok"] and r["english"] and r["near_caught"])]
    print(f"{len(rows)} languages: ok {sum(r['ok'] for r in rows)}, english caught {sum(r['english'] for r in rows)}, "
          f"near caught {sum(r['near_caught'] for r in rows)}, verified by reading {sum(r['verified'] for r in rows)}")
    print(f"without --app: ok {sum(r['ok_without_app'] for r in rows)}, english caught {sum(r['english_without_app'] for r in rows)}")
    for r in rows:
        if not (r["ok_without_app"] and r["english_without_app"]):
            print(f"  without --app {r['lang']:8} ok={r['ok_without_app']} english={r['english_without_app']}")
    for r in bad:
        print(f"  {r['lang']:8} ok={r['ok']!s:5} english={r['english']!s:5} near({r['near']})={r['near_caught']!s:5} {r['ok_problem'] or ''}")

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--tesseract"]
    main(args[0], args[1] if len(args) > 1 else "langmatrix", "--tesseract" in sys.argv)
