# Clip 3: run on iPhone and iPad (DEVICES: recorded by record_devices.py under the device lock). Real time; render.py speeds it up.
Output rec/c3-run-ios.mp4
Set Framerate 10
Source tapes/common.tape
Sleep 600ms
Type "shotfleet run --platform ios"
Sleep 400ms
Enter
Wait@80m /\$\s*$/
Sleep 5s
