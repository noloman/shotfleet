# Clip 7: store rules. Recorded on the iPhone-only output (no iPad set), then a copy with one screenshot resized (device-free).
Output rec/c7-store-rules.mp4
Source tapes/common.tape
Hide
Type "rm -rf wrong-size shotfleet-check && clear"
Enter
Sleep 300ms
Show
Sleep 600ms
Type "ls out-ios"
Enter
Sleep 1200ms
Type "shotfleet check out-ios"
Sleep 400ms
Enter
Wait@180s /\$\s*$/
Sleep 5s
Type "clear; cp -R out-ios wrong-size"
Enter
Sleep 800ms
Type "sips -z 2000 1000 wrong-size/iphone-17-pro-max/raw/de/02_settings.png > /dev/null"
Sleep 400ms
Enter
Sleep 1500ms
Type "shotfleet check wrong-size"
Sleep 400ms
Enter
Wait@180s /\$\s*$/
Sleep 6s
