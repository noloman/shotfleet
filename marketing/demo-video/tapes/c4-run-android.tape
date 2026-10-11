# Clip 4: the same flow on Android emulators (DEVICES: recorded by record_devices.py under the device lock).
Output rec/c4-run-android.mp4
Set Framerate 10
Source tapes/common.tape
Sleep 600ms
Type "shotfleet run --platform android"
Sleep 400ms
Enter
Wait@40m /\$\s*$/
Sleep 5s
