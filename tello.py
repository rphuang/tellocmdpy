import os
import sys
import logging
import time

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout

from IotLib.config import Config
from IotLib.log import Log
from IotLib.pyUtils import timestamp, startThread
from myTello import MyTello

class MainWidget(BoxLayout):
    """ The main/root widget for the ExifPhotos. The UI is defined in .kv file """
    def __init__(self, config):
        super(MainWidget, self).__init__()
        # init config values
        self.config = config
        self.defaultSpeed = config.getOrAddInt('DefaultSpeed', 100)
        self.runCmdDelay = config.getOrAddFloat('DelayForContinuousCommands', 0)
        self.defaultPhotoFolder = config.getOrAdd('DefaultPhotoFolder', '')
        self.defaultVideoFolder = config.getOrAdd('DefaultVideoFolder', '')
        self.statusUpdateInterval = config.getOrAddFloat('StatusUpdateInterval', 5.0)
        self.videoClassifier = config.getOrAdd('Video.Classifier', 'haarcascade_frontalface_alt.xml')
        self.videoStreaming = config.getOrAddBool('Video.Streaming', False)
        self.videoRedording = config.getOrAddBool('Video.Redording', False)
        self.videoStamping = config.getOrAddBool('Video.Stamping', False)
        self.defaultSpeed = int(self.ids.SpeedInput.text)
        self.videoWidth = int(self.ids.WidthInput.text)
        self.videoHeight = int(self.ids.HeightInput.text)
        # create MyTello (logging options: logging.DEBUG logging.WARNING logging.INFO)
        self.tello = MyTello(log_level=logging.WARNING, videoStamping = self.videoStamping,
                            commandCallback = self._showCommand, postCmdCallback = self._showCommandResult, faceClassifierFile = self.videoClassifier)
        self._setVideoSizePosition()

        # init the command dictionary
        self._commands = {}
        self._commandsBuffer = ['', '', '']
        # connected
        self.connected = False
        # start thread to update status
        self.updateStatus = True
        self.statusThread = startThread(context='Updating Tello status', target=self._updateStatus, front=True)

    def setSpeed(self, speed):
        """ set default speed """
        self.defaultSpeed = int(speed)
        self.ids.SpeedInput.text = str(self.defaultSpeed)
        if self.connected:
            self.sendCommand('speed %i' %self.defaultSpeed)

    def setVideoWidth(self, width):
        self.videoWidth = int(width)
        self._setVideoSizePosition()

    def setVideoHeight(self, height):
        self.videoHeight = int(height)
        self._setVideoSizePosition()

    def connect(self):
        """ connect to tello """
        self._showCommand('connect')
        self.connected = self.tello.connect(wait_for_state=True)
        if self.connected:
            # set tello speed
            self.sendCommand('speed %i' %self.defaultSpeed)
            if self.videoStreaming:
                self.startOrStopStreamVideoAsync()
            if self.videoRedording:
                self.startOrStopSaveVideoAsync()
        else:
            self._showStatus('Failed to Connect')

    def takeoff(self):
        """ take off """
        self.tello.executeCommand('takeoff')

    def land(self):
        """ land """
        self.tello.executeCommand('land')

    def sendRcControl(self, left_right_velocity, forward_backward_velocity, up_down_velocity, yaw_velocity, context: str = ''):
        """ Send RC control via four channels. Input RC values can be float that will be multiplied be default speed. """
        self.tello.send_rc_control(int(left_right_velocity * self.defaultSpeed), int(forward_backward_velocity * self.defaultSpeed), 
                                   int(up_down_velocity * self.defaultSpeed), int(yaw_velocity * self.defaultSpeed), context)

    def sendCommand(self, cmd):
        """ send a command to Tello """
        self.tello.executeCommand(cmd)

    def sendCommandAsync(self, cmd):
        """ send a command to Tello in a separate thread """
        startThread(context='Send command: %s' %cmd, target=self.tello.executeCommand, front=True, args=(cmd,))

    def startCommandAsync(self, cmd):
        """ start sending command to Tello continuously until stopCommand is called """
        # add cmd to self._commands
        self._commands[cmd] = cmd
        startThread(context='Run command: %s' %cmd, target=self._runCommand, front=True, args=(cmd,))

    def stopCommand(self, cmd):
        """ stop sending the command to Tello """
        # just remove cmd from self._commands
        self._commands.pop(cmd, None)

    def takePictureAsync(self):
        """ take a picture and save to file with current time as file name """
        fileName = '%s.png' %timestamp()
        fileName = os.path.join(self.defaultPhotoFolder, fileName)
        startThread(context='Save photo to file: %s' %fileName, target=self.tello.takePicture, front=True, args=(fileName,))

    def startOrStopStreamVideoAsync(self):
        """ start/stop video streaming in separate window """
        self.tello.startOrStopStreamVideoAsync()

    def startOrStopFaceTrackingAsync(self):
        """ start/stop video streaming in separate window """
        self.tello.startOrStopFaceTrackingAsync()

    def startOrStopSaveVideoAsync(self):
        """ start/stop a video and save to file with current time as file name """
        fileName = '%s.avi' %timestamp()
        fileName = os.path.join(self.defaultVideoFolder, fileName)
        self.tello.startOrStopSaveVideoAsync(fileName)

    def runCommandFromFileAsync(self, fileName):
        ''' load tello commands from file parse and send to tello '''
        startThread(context='Run command file: %s' %fileName, target=self.tello.runCommandFromFile, front=True, args=(fileName,))

    def _showStatus(self, state):
        """ display status on UI """
        self.ids.StatusLabel.text = state

    def _showCommand(self, cmd):
        """ display command on UI """
        #self.ids.CommandLabel.text = '%s\n%s' %(self.ids.CommandLabel.text, cmd)
        self._commandsBuffer.append(cmd)
        self._displayCommands()

    def _showCommandResult(self, cmd, msg):
        """ display command on UI """
        #self.ids.CommandLabel.text = '%s => %s' %(self.ids.CommandLabel.text, msg)
        if cmd == self._commandsBuffer[-1]:
            self._commandsBuffer[-1] = '%s => %s' %(self._commandsBuffer[-1], msg)
        else:
            self._commandsBuffer.append('%s => %s' %(cmd, msg))
        self._displayCommands()

    def _displayCommands(self):
        """ display last 7 commands """
        text = ''
        for item in self._commandsBuffer[-10:]:
            if len(text) == 0:
                text = item
            else:
                text = '%s\n%s' %(text, item)
        self.ids.CommandLabel.text = text

    def _runCommand(self, cmd):
        """ runs continuously to send the command (should be in a separate thread) """
        count = 0
        while cmd in self._commands:
            self.tello.executeCommand(cmd)
            count += 1
            time.sleep(self.runCmdDelay)

        Log.info('Run command %s for %i times' %(cmd, count))

    def _setVideoSizePosition(self):
        windowWidth, windowHeight = Window.size
        videoPosition = (Window.left + windowWidth, 0)
        self.tello.setVideoSizePosition(videoSize = (self.videoWidth, self.videoHeight), videoPosition = videoPosition)

    def _updateStatus(self):
        """ runs every self.statusUpdateInterval seconds to get battery status (should be run in a separate thread) """
        while self.updateStatus:
            try:
                if self.connected:
                    self.ids.ConnectButton.background_color = (0, 1, 0, 1)
                    if self.tello.is_flying:
                        self.ids.StatusLabel.text = 'Flying'
                    else:
                        self.ids.StatusLabel.text = 'Connected'
                    self.ids.BatteryLabel.text = str(self.tello.get_battery()) + '%'
                    self.ids.HeightLabel.text = str(self.tello.get_height())
                    self.ids.TempLabel.text = str(self.tello.get_temperature())
                    self.ids.FlighttimeLabel.text = str(self.tello.get_flight_time())
                    if 'StreamButton' in self.ids:
                        if self.tello.recordingVideo: self.ids.VideoButton.background_color = (0, 1, 0, 1)
                        else: self.ids.VideoButton.background_color = (1, 1, 1, 1)
                        if self.tello.streamingVideo: self.ids.StreamButton.background_color = (0, 1, 0, 1)
                        else: self.ids.StreamButton.background_color = (1, 1, 1, 1)
                        if self.tello.faceTracking: self.ids.FaceTrackButton.background_color = (0, 1, 0, 1)
                        else: self.ids.FaceTrackButton.background_color = (1, 1, 1, 1)
                else:
                    self.ids.ConnectButton.background_color = (1, 1, 1, 1)
                    self.ids.StatusLabel.text = 'Not Connected'
                    self.ids.BatteryLabel.text = '??%'
                    self.ids.HeightLabel.text = '??'
                    self.ids.TempLabel.text = '??'
                    self.ids.FlighttimeLabel.text = '??'
                    if 'StreamButton' in self.ids:
                        self.ids.VideoButton.background_color = (1, 1, 1, 1)
                        self.ids.StreamButton.background_color = (1, 1, 1, 1)
                        self.ids.FaceTrackButton.background_color = (1, 1, 1, 1)
            except:
                pass
            time.sleep(self.statusUpdateInterval)

# Kivy App
class telloApp(App):
    def __init__(self, config):
        super(telloApp,self).__init__()
        self.configuration = config

    def build(self):
        # return a MainWidget() as a root widget
        self.mainWidget = MainWidget(self.configuration)
        return self.mainWidget

if __name__ == '__main__':
    Log.WriteToConsole = True
    Log.WriteToLogging = False
    configFile='telloConfig.txt'
    if len(sys.argv) > 1:
        configFile = sys.argv[1]
    # apply config settings
    config = Config(configFile, autoSave = False)
    if config.getOrAddBool('Window.fullscreen', False):
        Window.fullscreen = True
    else:
        Window.size = (config.getOrAddInt('Window.width', 1600), config.getOrAddInt('Window.height', 1000))
        Window.top = config.getOrAddInt('Window.top', 40)
        Window.left = config.getOrAddInt('Window.left', 100)
    app = telloApp(config)
    app.run()
