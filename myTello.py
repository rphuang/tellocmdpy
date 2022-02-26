import os
import time
import logging
from djitellopy import Tello
from djitellopy.enforce_types import enforce_types
from pyUtils import timePrint, timestamp, startThread
try:
    import cv2
    cv2Ok = True
except:
    cv2Ok = False

@enforce_types
class MyTello(Tello):
    ''' override Tello '''
    def __init__(self, host=Tello.TELLO_IP, retry_count=Tello.RETRY_COUNT, log_level=logging.INFO, defaultPhotoFolder='', defaultVideoFolder='', commandCallback = None, postCmdCallback = None):
        Tello.LOGGER.setLevel(log_level)	# logging.DEBUG logging.WARNING logging.INFO
        super(MyTello, self).__init__(host, retry_count)
        self.recordingVideo = False
        self.defaultPhotoFolder = defaultPhotoFolder
        self.defaultVideoFolder = defaultVideoFolder
        self.commandCallback = commandCallback
        self.postCmdCallback = postCmdCallback

    def connect(self, wait_for_state=True):
        """ override connect (enter SDK mode) to log battery status """
        try:
            super(MyTello, self).connect(wait_for_state)
        except:
            self.LOGGER.error('Connect Failed')
            return False

        try:
            # log battery, temperature, and speed
            if wait_for_state:
                battery = str(self.get_battery())
            else:
                battery = str(self.query_battery())
            timePrint('Connected to Tello - Battery: %s Speed: %s Temperature: %s' %(battery, str(self.query_speed()), str(self.query_temperature())))
        except:
            self.LOGGER.error('Error getting Tello status')
        return True

    def send_control_command(self, command: str, timeout: int = Tello.RESPONSE_TIMEOUT) -> bool:
        ''' override to handle error conditions and print time of the command '''
        timePrint('Send command: %s' %command)
        #return super(MyTello, self).send_control_command(command, timeout)
        response = "max retries exceeded"
        for i in range(0, self.retry_count):
            cmdKey = '%s %i' %(command, i)
            if self.commandCallback is not None:
                self.commandCallback(cmdKey)
            response = self.send_command_with_return(command, timeout=timeout)
            if self.postCmdCallback is not None:
                self.postCmdCallback(cmdKey, response)
            response = response.lower()
            if 'ok' in response:
                return True
            elif 'error auto land' in response:
                self.LOGGER.error(response)
                break
            elif 'unknown command' in response:
                self.LOGGER.error(response)
                break
            elif 'error motor stop' in response:
                self.LOGGER.error(response)
                break

            self.LOGGER.debug("Command attempt #{} failed for command: '{}'".format(i, command))

        self.raise_result_error(command, response)
        return False # never reached

    # override with simplified message 
    def raise_result_error(self, command: str, response: str) -> bool:
        """Used to reaise an error after an unsuccessful command
        Internal method, you normally wouldn't call this yourself.
        """
        tries = 1 + self.retry_count
        raise Exception("Command '{}' was unsuccessful after {} tries."
                        .format(command, tries))

    def send_read_command(self, command: str) -> str:
        ''' override to print response of the command '''
        response = super(MyTello, self).send_read_command(command)
        #timePrint('Read %s: %s' %(command, response))
        return response

    def query_speed(self):
        """ override query speed setting (cm/s) to return float. returns negative number on error """
        try:
            response = self.send_read_command('speed?')
            return float(response)
        except:
            return -1.0

    def query_temperature(self):
        """ override Query temperature to return string """
        return self.send_read_command('temp?')

    def end(self):
        """ override end method to stop video recording if still running """
        self.stopVideo()
        super(MyTello, self).end()

    def takePicture(self, fileName, useDefaultFolder = True):
        ''' take a picture and save to a png file '''
        if cv2Ok:
            if useDefaultFolder:
                fileName = os.path.join(self.defaultPhotoFolder, fileName)
            msg = 'Save picture to %s' %fileName
            timePrint(msg)
            try:
                if self.commandCallback is not None:
                    self.commandCallback(msg)

                if not self.stream_on:
                    self.streamon()

                frame_read = self.get_frame_read()
                cv2.imwrite(fileName, frame_read.frame)

                msg = 'Saved picture to %s' %fileName
                timePrint(msg)
                if self.postCmdCallback is not None:
                    self.postCmdCallback(msg, 'Saved')
                return True
            except Exception as e:
                err = 'Error taking picture: ' + str(e)
                timePrint (err)
                if self.commandCallback is not None:
                    self.commandCallback('Failed to save picture to %s' %fileName)
                self.LOGGER.error(err)
        return False

    def startOrStopVideo(self, fileName, useDefaultFolder = True):
        if not self.recordingVideo:
            self.startVideo(fileName, useDefaultFolder)
        else:
            self.stopVideo()

    def startVideo(self, fileName, useDefaultFolder = True):
        ''' start a video and save to a avi file '''
        if cv2Ok:
            if useDefaultFolder:
                fileName = os.path.join(self.defaultVideoFolder, fileName)
            if not self.stream_on:
                self.streamon()
            self.recordingVideo = True
            self.recorder = startThread(context='Video Recording to %s' %fileName, target=self._videoRecorder, front=True, args=(fileName,))

    def stopVideo(self):
        if self.recordingVideo:
            self.recordingVideo = False
            self.recorder.join()

    def _videoRecorder(self, fileName):
        # create a VideoWrite object, recoring to avi file
        cmdKey = 'Start video recording to file %s' %(fileName)
        if self.commandCallback is not None:
            self.commandCallback(cmdKey)
        frame_read = self.get_frame_read()
        height, width, _ = frame_read.frame.shape
        timePrint('Starting video recording (%ix%i) to file %s' %(width, height, fileName))
        video = cv2.VideoWriter(fileName, cv2.VideoWriter_fourcc(*'XVID'), 30, (width, height))

        while self.recordingVideo:
            video.write(frame_read.frame)
            time.sleep(1 / 30)

        video.release()
        msg = 'Stopped video recording'
        timePrint(msg)
        if self.postCmdCallback is not None:
            self.postCmdCallback(cmdKey, 'Stopped')

    def runCommandFromFile(self, fileName):
        ''' load tello commands from file parse and send to tello '''
        timePrint('Loading command file: %s' %fileName)
        with open(fileName, 'r') as file:
            if self.commandCallback is not None:
                self.commandCallback('Run ' + fileName)
            for line in file:
                line = line.strip()
                if len(line) == 0:
                    pass
                elif '#' == line[0]:
                    pass
                else:
                    self.executeCommand(line)
            if self.commandCallback is not None:
                self.commandCallback('End of ' + fileName)

    def executeCommand(self, cmdstr):
        ''' execute the command str. returns False on error '''
        msg = cmdstr.lower()
        try:
            ok = True
            if 'land' == msg:
                self.land()
                if self.is_flying:
                    ok = False
            elif 'takeoff' == msg:
                self.takeoff()
                if not self.is_flying:
                    ok = False
            elif 'p' == msg or 'photo' == msg:
                fileName = '%s.png' %timestamp()
                self.takePicture(fileName)
            elif 'v' == msg or 'video' == msg:
                fileName = '%s.avi' %timestamp()
                self.startOrStopVideo(fileName)
            elif '?' == msg[-1]:
                # send read command
                val = self.send_read_command(msg)
            elif 'sleep' in msg:
                if self.commandCallback is not None:
                    self.commandCallback(msg)
                value = float(self._getValue(cmdstr, 1.0))
                timePrint('Sleeping %f seconds ...' %value)
                time.sleep(value)
            elif 'run' in msg or 'load' in msg:
                fileName = self._getValue(cmdstr, 'telloCommands.txt')
                self.runCommandFromFile(fileName)
            else:
                # send control command
                ok = self.send_control_command(msg)
            return ok
        except Exception as e:
            timePrint ('Error: ' + str(e))
            if self.commandCallback is not None:
                self.commandCallback('%s => Failed: %s' %(msg, str(e)))
            return False

    def _getValue(self, cmdstr, default):
        ''' get the command value from the str '''
        try:
            cmd, value = cmdstr.split(' ')
            return value
        except:
            return default

