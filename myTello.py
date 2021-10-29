import time
import logging
import cv2
from djitellopy import Tello
from pyUtils import timePrint, startThread
from djitellopy.enforce_types import enforce_types

@enforce_types
class MyTello(Tello):
    ''' override Tello '''
    def __init__(self, host=Tello.TELLO_IP, retry_count=Tello.RETRY_COUNT, log_level=logging.INFO):
        Tello.LOGGER.setLevel(log_level)	# logging.DEBUG logging.WARNING logging.INFO
        super(MyTello, self).__init__(host, retry_count)
        self.recordingVideo = False

    def connect(self, wait_for_state=True):
        """ override connect (enter SDK mode) to log battery status """
        super(MyTello, self).connect(wait_for_state)
        # log battery, temperature, and speed
        if wait_for_state:
            battery = str(self.get_battery())
        else:
            battery = str(self.query_battery())
        timePrint('Connected to Tello - Battery: %s Speed: %s Temperature: %s' %(battery, str(self.query_speed()), str(self.query_temperature())))

    def send_control_command(self, command: str, timeout: int = Tello.RESPONSE_TIMEOUT) -> bool:
        ''' override to handle error conditions and print time of the command '''
        timePrint('Send command: %s' %command)
        #return super(MyTello, self).send_control_command(command, timeout)
        response = "max retries exceeded"
        for i in range(0, self.retry_count):
            response = self.send_command_with_return(command, timeout=timeout)
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

    def send_read_command(self, command: str) -> str:
        ''' override to print response of the command '''
        response = super(MyTello, self).send_read_command(command)
        timePrint('Read %s: %s' %(command, response))

    def query_speed(self):
        """ override query speed setting (cm/s) to return float """
        return self.send_read_command_float('speed?')

    def query_temperature(self):
        """ override Query temperature to return string """
        return self.send_read_command('temp?')

    def end(self):
        """ override end method to stop video recording if still running """
        self.stopVideo()
        super(MyTello, self).end()
        #timePrint('Stopped Tello ')

    def takePicture(self, fileName):
        ''' take a picture and save to a png file '''
        timePrint('Taking picture to %s' %fileName)
        if not self.stream_on:
            self.streamon()
        frame_read = self.get_frame_read()
        cv2.imwrite(fileName, frame_read.frame)
        timePrint('Saved picture to %s' %fileName)

    def startOrStopVideo(self, fileName):
        if not self.recordingVideo:
            self.startVideo(fileName)
        else:
            self.stopVideo()

    def startVideo(self, fileName):
        ''' start a video and save to a avi file '''
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
        frame_read = self.get_frame_read()
        height, width, _ = frame_read.frame.shape
        timePrint('Starting video recording (%ix%i) to file %s' %(width, height, fileName))
        video = cv2.VideoWriter(fileName, cv2.VideoWriter_fourcc(*'XVID'), 30, (width, height))

        while self.recordingVideo:
            video.write(frame_read.frame)
            time.sleep(1 / 30)

        video.release()
        timePrint('Stopped video recording')


