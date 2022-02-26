# tellocmdpy
There are two Python programs:
* telloCmd.py - a simple Python code that controls Tello drone via command line or file (contains commands).
* tello.py - GUI version of the Tello control either manually or from command file

The purpose of the GUI is not to compete the official Tello App but it is intended to run command files with ease and precisions.

# Getting Started
1. download/clone the respository.
2. Install the Python package DJITelloPy at https://github.com/damiafuentes/DJITelloPy.
3. Install OpenCV - opencv-python
4. Install Kivy (GUI only)
5. Start Tello drone and connect to its WiFi
6. In Windows 
    * command line: python3 telloCmd.py
    * GUI: python3 tello.py
7. In Android
    * install PyDroid 3 and dependencies
    * copy the files under android-landscape or android-portrait folder to the main folder
    * from Pydroid, open tell.py and run

# Configuration

## telloConfig.txt file
* Window.fullscreen - whether to use full screen mode
* Window.top - set the top position for the ExifPhotos window
* Window.left - set the left position for the ExifPhotos window
* Window.width - set the width for the ExifPhotos window
* Window.height - set the height for the ExifPhotos window
* DefaultSpeed - the default speed for the drone
* DelayForContinuousCommands - the delay (in seconds) between sending command while pressing the buttons like Up, Down, ...
* DefaultPhotoFolder - default folder for saving photo file
* DefaultVideoFolder - default folder for saving video file
* StatusUpdateInterval - specify how often to update the drone status (in second)

## Custom UI
The UI is based on Python Kivy, so custom UI can be done by changing the tello.kv file. Examples:
* change the Run Demo button to run different file by changing the file name of the .kv file.
```
        Button:
            id: RunDemoButton
            text: 'Run Demo'
            on_release: root.runCommandFromFileAsync('samples\video360.txt')
```

* add a new button to do flip
```
        Button:
            id: FlipLeftButton
            text: 'Flip Left'
            on_release: root.sendCommand('flip l')
```

* Besides editing the kv file directly, there are versions of .kv files in the repo. Just copy the files from the subfolder to main folder.
    * android-landscape - this folder contains .kv and config files for Android in landscape mode.
    * android-portrait - this folder contains .kv and config files for Android in portrait mode.
    * windows-landscape - this folder contains .kv and config files for Windows in landscape mode.

# TelloCmd.py Usage
On starting, telloCmd will connect to the Tello drone by sending "command" to the drone. Once connected, it prompts for user inputs to control Tello drone. Available commands:
* 0 or takeoff - send takeoff command to Tello drone
* 1 or land - send land command to Tello drone
* 2 or end - this instructs telloCmd to exit and send necessary commands to the drone (such as land, streamoff).
* p or photo - take a picture and save to file. The file name is yyyy-mmdd-hhmmss.png under the current folder.
* v or video - start/stop video recording. The video file is yyyy-mmdd-hhmmss.avi under the current folder.
* run <file> - load and execute commands from file. If no file is specified telloCmd load from telloCommands.txt. The run command can be nested but there is no check for infinite loop. See examples in the files under samples folder.
* sleep <sec> - sleep in seconds. The default value is 1.0. This is useful in the command file.
* help        - print help menu
* enter a valid Tello commands like "up 20", "left 50", "cw 90", "flip l". Available commands is defined in: https://dl-cdn.ryzerobotics.com/downloads/tello/20180910/Tello%20SDK%20Documentation%20EN_1.3.pdf

# Files
* myTello.py - MyTello is a simple wrapper class on top of djitellopy.Tello. It adds the basic support for taking photo and video. It also overrides some methods to handle errors (probably caused by unable to update Tello's firmware).
* tello.py - the main GUI module. It uses tello.kv for UI layout and telloConfig.txt for configuration.
* tello.kv - the Kivy UI file
* config.py - simple name-value text configuration
* telloCmd.py - this is the console command that takes user inputs and excute the command.
* pyUtils.py - contains some utilities
* The samples folder contains examples of command file that can be loaded/run by tello and telloCmd.

# Issues, Notes, and ToDos
* use Buildozer to build Android package. It's really hard to use Buildozer especially compared to other tools! It failed on multiple platforms (WSL, RPi)!

