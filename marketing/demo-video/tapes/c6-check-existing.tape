# Clip 6: check screenshots made elsewhere: a plain folder, --locale, no simulator (device-free, after c3).
Output rec/c6-check-existing.mp4
Source tapes/common.tape
Hide
Type "rm -rf my-shots shotfleet-check && clear"
Enter
Sleep 300ms
Show
Sleep 600ms
Type "mkdir my-shots && cp out-ios/iphone-17-pro-max/raw/ja/*.png my-shots/"
Sleep 400ms
Enter
Sleep 1s
Type "ls my-shots"
Enter
Sleep 1500ms
Type "shotfleet check my-shots --locale de --app build/FleetFixture.app"
Sleep 400ms
Enter
Wait@180s /\$\s*$/
Sleep 7s
