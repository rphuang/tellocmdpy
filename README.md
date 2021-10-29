# tellocmdpy
This is a simple Python code that controls Tello drone via command line or file (contains commands).

# Getting Started
1. download/clone the respository.
2. Install the Python package DJITelloPy at https://github.com/damiafuentes/DJITelloPy.
3. Install OpenCV - opencv-python
4. Start Tello drone and connect to its WiFi
5. Run command: python3 telloCmd.py

# Usage
On starting, telloCmd will connect to the Tello drone by sending "command" to the drone. Once it it connected, it prompts for user inputs to control Tello drone. Available commands:
* 0 or takeoff - send takeoff command to Tello drone
* 1 or land - send land command to Tello drone
* 2 or end - this instructs telloCmd to exit and send necessary commands to the drone (such as land, streamoff).
* p or photo - take a picture and save to file. The file name is yyyy-mmdd-hhmmss.png under the current folder.
* v or video - start/stop video recording. The video file  is yyyy-mmdd-hhmmss.avi under the current folder.
* run <file> - load and execute commands from file. If no file is specified telloCmd load from telloCommands.txt. The run command can be nested but there is no check for infinite loop.
* sleep <sec> - sleep in seconds. The default value is 1.0. This is useful in the command file.
* help        - print help menu
* enter a valid Tello commands like "up 20", "left 50", "cw 90", "flip l". https://dl-cdn.ryzerobotics.com/downloads/tello/20180910/Tello%20SDK%20Documentation%20EN_1.3.pdf

# Files
* myTello.py - MyTello is a simple wrapper class on top of djitellopy.Tello. It adds the basic support for taking photo and video. It also overrides some methods to handle errors (probably caused by unable to update Tello's firmware).
* telloCmd.py - this is the console command that takes user inputs and excute the command.
* pyUtils.py - contains some utilities
* The samples folder contains examples of command file that can be loaded/run by telloCmd.

