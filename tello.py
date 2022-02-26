import os
import sys
import logging
import time

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout

from config import Config
from myTello import MyTello
from pyUtils import timePrint, timestamp, startThread

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
        # create MyTello (logging options: logging.DEBUG logging.WARNING logging.INFO)
        self.tello = MyTello(log_level=logging.WARNING, defaultPhotoFolder=self.defaultPhotoFolder, defaultVideoFolder=self.defaultVideoFolder, commandCallback = self._showCommand, postCmdCallback = self._showCommandResult)	
        # init the command dictionary
        self._commands = {}
        self._commandsBuffer = ['', '', '']
        # connected
        self.connected = False
        # start thread to update status
        self.updateStatus = True
        self.statusThread = startThread(context='Updating Tello status', target=self._updateStatus, front=True)

    def connect(self):
        """ connect to tello """
        self._showCommand('connect')
        self.connected = self.tello.connect(wait_for_state=True)
        if self.connected:
            # set tello speed
            self.sendCommand('speed %i' %self.defaultSpeed)
        else:
            self._showStatus('Failed to Connect')

    def takeoff(self):
        """ take off """
        self.tello.executeCommand('takeoff')

    def land(self):
        """ land """
        self.tello.executeCommand('land')

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
        startThread(context='Save photo to file: %s' %fileName, target=self.tello.takePicture, front=True, args=(fileName,))

    def startOrStopVideoAsync(self):
        """ start/stop a video and save to file with current time as file name """
        fileName = '%s.avi' %timestamp()
        startThread(context='Save video to file: %s' %fileName, target=self.tello.startOrStopVideo, front=True, args=(fileName,))

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
        for item in self._commandsBuffer[-7:]:
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

        timePrint('Run command %s for %i times' %(cmd, count))

    def _updateStatus(self):
        """ runs every self.statusUpdateInterval seconds to get battery status (should be run in a separate thread) """
        while self.updateStatus:
            try:
                if self.connected:
                    if self.tello.is_flying:
                        self.ids.StatusLabel.text = 'Flying'
                    else:
                        self.ids.StatusLabel.text = 'Connected'
                    self.ids.BatteryLabel.text = str(self.tello.get_battery()) + '%'
                    self.ids.HeightLabel.text = str(self.tello.get_height())
                    self.ids.TempLabel.text = str(self.tello.get_temperature())
                    self.ids.FlighttimeLabel.text = str(self.tello.get_flight_time())
                    self.ids.SpeedLabel.text = str(self.tello.query_speed())
                else:
                    self.ids.StatusLabel.text = 'Not Connected'
                    self.ids.BatteryLabel.text = '??%'
                    self.ids.HeightLabel.text = '??'
                    self.ids.TempLabel.text = '??'
                    self.ids.FlighttimeLabel.text = '??'
                    self.ids.SpeedLabel.text = str(self.defaultSpeed)
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
