# Clip 2: init finds the builds and their languages (device-free). Resets the project, so run session.sh first.
Output rec/c2-init.mp4
Source tapes/common.tape
Hide
Type "rm -f shotfleet.toml flow.yaml && clear"
Enter
Sleep 300ms
Show
Sleep 600ms
Type "ls build"
Enter
Sleep 1s
Type "shotfleet init build/FleetFixture.app build/FleetFixture.apk"
Sleep 400ms
Enter
Wait@60s /\$\s*$/
Sleep 4s
Type "cp ../edits/shotfleet.toml ../edits/flow.yaml ."
Sleep 300ms
Enter
Sleep 600ms
Type "clear; head shotfleet.toml flow.yaml"
Sleep 300ms
Enter
Sleep 8s
