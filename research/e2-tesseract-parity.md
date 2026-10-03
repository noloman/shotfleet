# E2: does `check` give the same verdicts on Tesseract alone as with macOS text recognition? (2026-10-03)

Question (research/limits-platforms.md, E2): a Linux build has no macOS Vision, so `check` would run on Tesseract only.
Method: `cmd_check` with macOS recognition forced off (every screenshot read by `tesseract ... -l eng+<lang>`) on three real
sets, compared with the macOS-recognition runs of the same day.

| Set | macOS recognition | Tesseract only |
|---|---|---|
| CrossfitTracker iOS, 72 screenshots, 18 languages, app strings | 0 problems | 0 problems (62-66 s) |
| CrossfitTracker Android, 72 screenshots, 18 languages | 0 problems | 0 problems (136-321 s, load varied) |
| Planted set (4 planted mistakes: de screen in English, ko screen is Japanese, two copies) | 3 problems + 2 copies | first run missed the Japanese-in-Korean screen |

The miss: told `-l eng+kor`, Tesseract reads a Japanese screen as Latin gibberish plus a few stray Hangul characters, so
neither string matching nor the "enough Korean characters" test objects, and Tesseract reports no language. Fix: for ja, ko
and th listings, also run Tesseract's script detection (`--psm 0 -l osd`, `osd.traineddata` ships with tesseract-lang) and
treat a different script at confidence 1.0 or more as the wrong language (`tesseract_script`, `judge_screen`).

Script detection on the 144 clean real screenshots: right on 142; the 2 wrong (Korean read as Japanese) scored 0.20 and
0.06, the planted Japanese screen 1.51. So the threshold separates them on this data, but with thin margins: 144 screens, one
planted case. Treat it as a measured heuristic, not a guarantee.

Result with the fix: all three sets match macOS recognition (0, 0, and every planted mistake found).

What this does NOT show: Linux itself (E1: emulator speed under KVM, a Linux box is needed), Tesseract versions other than
5.x from Homebrew, languages outside the 18 on these sets (the 85-language reading measurement is tools/langmatrix.py
`--tesseract`: 84/85).
