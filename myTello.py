import os
import time
import logging
from djitellopy import Tello
from djitellopy.enforce_types import enforce_types
from CameraLib.faceTracking import FaceTracker
from IotLib.log import Log
from IotLib.pyUtils import timestamp, startThread
try:
    import cv2
    cv2Ok = True
except:
    cv2Ok = False

@enforce_types
class MyTello(Tello):
    ''' override Tello '''
    def __init__(self, host=Tello.TELLO_IP, retry_count=Tello.RETRY_COUNT, log_level=logging.INFO,
                commandCallback = None, postCmdCallback = None, videoWidth = 960, videoHeight = 720,
                faceClassifierFile=''):
        Tello.LOGGER.setLevel(log_level)	# logging.DEBUG logging.WARNING logging.INFO
        super(MyTello, self).__init__(host, retry_count)
        self._videoWorkerThread = None
        self.recordingVideo = False
        self.streamingVideo = False
        self.faceTracking = False
        self.videoWidth = videoWidth
        self.videoHeight = videoHeight
        self.faceClassifierFile = faceClassifierFile
        self.faceTracker = None
        self.videoFileName = ''
        self.videoFrame = None
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
            Log.info('Connected to Tello - Battery: %s Speed: %s Temperature: %s' %(battery, str(self.query_speed()), str(self.query_temperature())))
        except:
            self.LOGGER.error('Error getting Tello status')
        return True

    # override to handle error conditions and print time of the command
    def send_control_command(self, command: str, timeout: int = Tello.RESPONSE_TIMEOUT) -> bool:
        """Send control command to Tello and wait for its response.
        Internal method, you normally wouldn't call this yourself.
        """
        Log.info('Send command: %s' %command)
        #return super(MyTello, self).send_control_command(command, timeout)
        response = "max retries exceeded"
        for i in range(0, self.retry_count):
            cmdKey = '%s %i' %(command, i)
            self._logCommand(cmdKey)
            response = self.send_command_with_return(command, timeout=timeout)
            self._logCommandResult(cmdKey, response)
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

    # override to handle callback 
    def send_command_without_return(self, command: str):
        """Send command to Tello without expecting a response.
        Internal method, you normally wouldn't call this yourself.
        """
        # Commands very consecutive makes the drone not respond to them. So wait at least self.TIME_BTW_COMMANDS seconds
        self._logCommand(command)
        super(MyTello, self).send_command_without_return(command)

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
        #Log.info('Read %s: %s' %(command, response))
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

    def takePicture(self, fileName):
        ''' take a picture and save to a png file '''
        if cv2Ok:
            cmd = 'Save picture to %s' %fileName
            self._logCommand(cmd)

            try:
                if self.videoFrame is not None and self._videoWorkerThread != None:
                    # use self.videoFrame if available and up to date
                    frame = self.videoFrame
                else:
                    if not self.stream_on:
                        self.streamon()

                    frame = self.get_frame_read().frame

                # write to file
                cv2.imwrite(fileName, frame)

                self._logCommandResult(cmd, 'Saved' )
                return True
            except Exception as e:
                self._logException('Saving picture to %s' %fileName, e)
        return False

    def startOrStopStreamVideoAsync(self):
        """ streaming video in an open cv window """
        if not self.streamingVideo:
            if cv2Ok:
                self._logCommand('Start video streaming')
                self.streamingVideo = True
                self._startVideoWorkerAsync()
        else:
            self.streamingVideo = False
            self._stopVideoWorker()
            self._logCommand('Stopped video streaming')

    def startOrStopSaveVideoAsync(self, fileName):
        if not self.recordingVideo:
            if cv2Ok:
                self.videoFileName = fileName
                self._logCommand('Start video recording to file %s' %(fileName))
                self.recordingVideo = True
                self._startVideoWorkerAsync()
        else:
            self.recordingVideo = False
            self._stopVideoWorker()
            self._logCommand('Stopped video recording')

    def startOrStopFaceTrackingAsync(self):
        """ start/stop Face Tracking with streaming video in an open cv window """
        if not self.faceTracking:
            if cv2Ok:
                if self.faceTracker == None:
                    self.faceTracker = FaceTracker(cv2.CascadeClassifier(self.faceClassifierFile), debug=False)
                self._logCommand('Start face tracking')
                self.faceTracking = True
                self._startVideoWorkerAsync()
        else:
            self.faceTracking = False
            self._stopVideoWorker()
            self._logCommand('Stopped face tracking')

    def _logCommand(self, msg):
        Log.info(msg)
        if self.commandCallback is not None:
            self.commandCallback(msg)

    def _logCommandResult(self, cmd, result):
        Log.info('%s => %s' %(cmd, result))
        if self.postCmdCallback is not None:
            self.postCmdCallback(cmd, result)

    def _logException(self, cmd, err):
        Log.error('Error %s: %s' %(cmd, str(err)))
        if self.commandCallback is not None:
            self.commandCallback('Error: %s' %cmd)

    def _startVideoWorkerAsync(self):
        if self._videoWorkerThread is not None:
            return
        if cv2Ok:
            self._videoWorkerThread = startThread(context='Video Processing', target=self._videoWorker, front=True)

    def _stopVideoWorker(self):
        if self._videoWorkerThread is None or self.streamingVideo or self.recordingVideo or self.faceTracking:
            return

        self._videoWorkerThread.join()
        self._videoWorkerThread = None

    def _videoWorker(self):
        if not self.stream_on:
            self.streamon()

        self._logCommand('Start video processing')
        frameOk = True      # whether there is error in handling video frame
        videoWriter = None  # for recording video to file
        frame_read = self.get_frame_read()

        while self.streamingVideo or self.recordingVideo or self.faceTracking:
            try:
                frame = frame_read.frame
                # resize the image frame if necessary
                width = self.videoWidth
                height = self.videoHeight
                height0, width0, _ = frame.shape
                if height != height0 or width != width0:
                    frame = cv2.resize(frame, (width, height))

                if self.faceTracking:
                    frame = self.faceTracker.detectOrTrack(frame)

                if self.recordingVideo:
                    if videoWriter is None:
                        videoWriter = cv2.VideoWriter(self.videoFileName, cv2.VideoWriter_fourcc(*'XVID'), 30, (width, height))
                    videoWriter.write(frame)
                elif videoWriter is not None:
                    videoWriter.release()
                    videoWriter = None

                if self.streamingVideo:
                    cv2.imshow('Tello Stream', frame)

                frameOk = True
            except Exception as err:
                if frameOk:
                    # only issue warning when the video frame was ok before
                    Log.warning('Exception processing video frame : %s' %str(err))
                    frameOk = False

            # keep the current frame so takePicture() can use it
            self.videoFrame = frame
            # wait for ~1/30 second (~30 milliseconds)
            cv2.waitKey(30)

        # exit _videoWorker
        self.streamoff()
        self._logCommand('Stopped video processing')

    def runCommandFromFile(self, fileName):
        ''' load tello commands from file parse and send to tello '''
        Log.info('Loading command file: %s' %fileName)
        with open(fileName, 'r') as file:
            self._logCommand('Run ' + fileName)
            for line in file:
                line = line.strip()
                if len(line) == 0:
                    pass
                elif '#' == line[0]:
                    pass
                else:
                    self.executeCommand(line)
            self._logCommand('End of ' + fileName)

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
                self.startOrStopSaveVideoAsync(fileName)
            elif 's' == msg or 'stream' == msg:
                self.startOrStopStreamVideoAsync()
            elif '?' == msg[-1]:
                # send read command
                val = self.send_read_command(msg)
            elif 'sleep' in msg:
                self._logCommand(msg)
                value = float(self._getValue(cmdstr, 1.0))
                Log.info('Sleeping %f seconds ...' %value)
                time.sleep(value)
            elif 'run' in msg or 'load' in msg:
                fileName = self._getValue(cmdstr, 'telloCommands.txt')
                self.runCommandFromFile(fileName)
            else:
                # send control command
                ok = self.send_control_command(msg)
            return ok
        except Exception as e:
            self._logException(cmdstr, e)
            return False

    def _getValue(self, cmdstr, default):
        ''' get the command value from the str '''
        try:
            cmd, value = cmdstr.split(' ')
            return value
        except:
            return default

