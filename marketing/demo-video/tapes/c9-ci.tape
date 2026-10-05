# Clip 9: the GitHub Actions recipe from the docs, and check's --json result and exit code (device-free, after c3).
Output rec/c9-ci.mp4
Source tapes/common.tape
Sleep 600ms
Type "cat .github/workflows/screenshots.yml"
Sleep 400ms
Enter
Sleep 7s
Type "clear; shotfleet check out-ios --json > check.json; echo exit code $?"
Sleep 400ms
Enter
Wait@180s /\$\s*$/
Sleep 1s
Type "python3 -m json.tool check.json | head -18"
Sleep 400ms
Enter
Sleep 7s
