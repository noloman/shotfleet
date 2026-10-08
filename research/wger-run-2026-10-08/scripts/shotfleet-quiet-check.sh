#!/bin/sh
# Exit 0 only when the Mac is quiet enough for a shotfleet device job (overnight rule). Prints why when not.
# Used by the device queue: /tmp/shotfleet-device-queue.md
h=$(date +%H); h=${h#0}; [ -z "$h" ] && h=0
# window: 00:00-07:00 local, or any time if the Mac is quiet anyway
free_pct=$(memory_pressure 2>/dev/null | sed -n 's/.*free percentage: *\([0-9]*\)%.*/\1/p' | tail -1)
load=$(sysctl -n vm.loadavg | tr -d '{}' | awk '{print int($1)}')
other_emu=$(ps axo command | grep "[q]emu-system-aarch64" | grep -cE -- "-port 57[0-9][0-9]")  # only shotfleet's own 57xx emulators count; an unowned one on 5566 (pid 32402) does not
other_xcb=$(ps axo command | grep "[x]codebuild" | grep -vc "shotfleet")
why=""
[ "${free_pct:-0}" -ge 20 ] || why="$why free memory ${free_pct:-?}% (<20%);"
[ "$load" -lt 300 ] || why="$why load $load (>=300);"
[ "$other_emu" -eq 0 ] || why="$why $other_emu Android emulator(s) running;"
# other projects' xcodebuild runs no longer block (they kept the load above 100 all night); the load limit covers them
if [ -z "$why" ]; then echo "quiet: free ${free_pct}%, load $load"; exit 0; fi
echo "not quiet:$why"; exit 1
