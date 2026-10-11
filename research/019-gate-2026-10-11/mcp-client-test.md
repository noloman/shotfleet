# MCP client test of the signed 0.1.9 build, 2026-10-11

Run from the 0.1.9 release folder with `mcp-client-test.sh`, a throwaway MCP config and an empty temp HOME (the real Claude config is not touched). The raw stream is not kept here, because it carries account details.

1. Raw stdio: `initialize` answered, `tools/list` returned check, doctor and run. Read-only hints: doctor true, check false, run false (check writes its report, so it is not read-only).
2. `claude -p` with that config: the shotfleet server showed as connected. Claude called `doctor` (it said Maestro was missing on this Mac, which is true) and then `check` on a copy of the 72-screenshot, 18-language fixture set with the app's APK. The check tool returned: exit 0, 72 screenshots, 18 languages, 0 problems, 0 notes.

A first attempt the same day failed only because the test was given a relative path to the program and the script changes folder; the server showed as not connected. It passed with the absolute path. Nothing in shotfleet was wrong.
