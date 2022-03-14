# tellocmdpy
This is a simple Python GUI to control Tello drone. It provides following features that is not supported in the official Tello App.
* face tracking
* run Tello commands from a file
* set/adjust drone speed
* set/adjust stream/video resolution
* time stamp on video and photos with drone height and latest command
* extensible UI that can be customized

Also a simple command line tool is included (telloCmd.py).

# Getting Started
1. download/clone the respository.
2. Install Python packages
    * DJITelloPy at https://github.com/damiafuentes/DJITelloPy.
    * OpenCV - opencv-python
    * Kivy 
    * dlib
    * IotDevicesPy at https://github.com/rphuang/IotDevicesPy (only dlib dependency is required others like flask and pylgbst are not required)
3. Start Tello drone and connect to its WiFi
4. For Windows machine, 
    * run command: python tello.py
    * click Connect
    * click Takeoff
    * click Stream, Video, Photo, Face Tracking to enable corresponding drone image function (see default folders for saved file)
    * click any buttons of the lower section to send command and release the button to stop the command

# Configuration

## telloConfig.txt file
* Window.fullscreen - whether to use full screen mode
* Window.top - set the top position for the ExifPhotos window
* Window.left - set the left position for the ExifPhotos window
* Window.width - set the width for the ExifPhotos window
* Window.height - set the height for the ExifPhotos window
* DefaultPhotoFolder - default folder for saving photo file
* DefaultVideoFolder - default folder for saving video file
* StatusUpdateInterval - specify how often to update the drone status (in second)
* Video.Classifier - the classifier used to detect and track faces
* Video.Streaming - whether to start video streaming after connect
* Video.Redording - whether to start video recording after connect
* Video.Stamping - whether to stamp flight information on video

## UI Inputs
The following inputs allow user to change default settings.
* Speed - the default speed for the drone and also used for sending RC control to Tello (all the lower buttons use RC control)
* Video Width - the width of the video and photo
* Video Height - the height of the video and photo

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

# UI Usage
There are three sections on the UI
* Buttons on the top - the specified action/command will be performed when the button is released.
* The section in the middle is used to display commands to the drone (left) and inputs/status on the right. The inputs are:
    * Speed - the speed will be sent to the drone and used for all the buttons on the bottom section to control the flight.
    * Width, Height - the resolution of the stream, video, and photo.
* Buttons on the bottom section - these buttons will send corresponding command to Tello when they are clicked and command will be cleared when the button is released.

# TelloCmd.py Usage
On starting, telloCmd will connect to the Tello drone by sending "command" to the drone. Once connected, it prompts for user inputs to control Tello drone. Available commands:
* 0 or takeoff - send takeoff command to Tello drone
* 1 or land - send land command to Tello drone
* 2 or end - this instructs telloCmd to exit and send necessary commands to the drone (such as land, streamoff).
* p or photo - take a picture and save to file. The file name is yyyy-mmdd-hhmmss.png under the current folder.
* v or video - start/stop video recording. The video file is yyyy-mmdd-hhmmss.avi under the current folder.
* s or stream - stream video in separate window
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
* The samples folder contains examples of command file that can be loaded/run by tello and telloCmd.

# Issues, Notes, and ToDos
* face tracking, video, and photo were only tested on Windows.
* use Buildozer to build Android package. It's really hard to use Buildozer especially compared to other tools! It failed on multiple platforms (WSL, RPi)!
* In Android
    * install PyDroid 3 
    * In PyDroid 3, install dependencies mentioned in Getting Started
    * In PyDroid 3, install IotDevicesPy at https://github.com/rphuang/IotDevicesPy
        * copy all files of IotDevicesPy to Android folder pydroid3/files/IotDevicesPy
        * with pydroid's terminal, cd to the the folder above
        * run: pip install .
    * copy all files of tellocmdpy to Android folder pydroid3/files/tellocmdpy
    * copy the files under android-landscape or android-portrait folder to the main folder
    * from Pydroid, open tello.py and run
* stamp time and drone status on video and photo
* features: follow me or object, fly path, gesture control
