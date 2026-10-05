# Clip 8: export the passing screenshots into fastlane's folders (device-free, after c3 and c4). Record before c6 and c7.
Output rec/c8-export.mp4
Source tapes/common.tape
Hide
Type "rm -rf fastlane && clear"
Enter
Sleep 300ms
Show
Sleep 600ms
Type "shotfleet export out-ios --fastlane fastlane"
Sleep 400ms
Enter
Wait@120s /\$\s*$/
Sleep 2s
Type "shotfleet export out-android --fastlane fastlane"
Sleep 400ms
Enter
Wait@120s /\$\s*$/
Sleep 3s
Type "clear; find fastlane -name '*.png' | sort | head -20"
Sleep 400ms
Enter
Sleep 7s
