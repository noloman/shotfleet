# Clip 8: export the passing Android screenshots into fastlane's folders (device-free, after c4). The iOS set has no iPad set, so export refuses it.
Output rec/c8-export.mp4
Source tapes/common.tape
Hide
Type "rm -rf fastlane && clear"
Enter
Sleep 300ms
Show
Sleep 600ms
Type "shotfleet export out-android --fastlane fastlane"
Sleep 400ms
Enter
Wait@120s /\$\s*$/
Sleep 3s
Type "clear; find fastlane -name '*.png' | sort | head -20"
Sleep 400ms
Enter
Sleep 7s
