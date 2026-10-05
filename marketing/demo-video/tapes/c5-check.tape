# Clip 5: check catches a planted wrong-language screenshot, then the real output passes (device-free, after c3).
Output rec/c5-check.mp4
Source tapes/common.tape
Hide
Type "rm -rf planted && clear"
Enter
Sleep 300ms
Show
Sleep 600ms
Type "cp -R out-ios planted"
Enter
Sleep 800ms
Type "cp out-ios/iphone-17-pro-max/raw/de/01_welcome.* planted/iphone-17-pro-max/raw/ja/"
Sleep 400ms
Enter
Sleep 1s
Type "shotfleet check planted"
Sleep 400ms
Enter
Wait@180s /\$\s*$/
Sleep 6s
Type "clear; shotfleet check out-ios"
Sleep 400ms
Enter
Wait@180s /\$\s*$/
Sleep 5s
