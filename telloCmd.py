import time
import logging
from djitellopy import Tello
from pyUtils import timePrint, timestamp
from myTello import MyTello

def help():
    print ('Control Tello drone with command line or text file contains commands. Available commands:')
    print ('  0 - takeoff')
    print ('  1 - land')
    print ('  2 - end and exit')
    print ('  p[hoto]     - take a picture and save to file (yyyy-mmdd-hhmmss.png)')
    print ('  v[ideo]     - start/stop video recording and save to file (yyyy-mmdd-hhmmss.avi)')
    print ('  run <file>  - load and execute commands from file (default: telloCommands.txt)')
    print ('  sleep <sec> - sleep in seconds (default: 1.0)')
    print ('  help        - print this help menu')
    print ('  or just enter a valid Tello commands like "up 20", "left 50", "cw 90", "flip l"')

def executeCommand(cmdstr):
    ''' execute the command str. returns False to quit '''
    msg = cmdstr.lower()
    if 'end' in msg or '2' == msg:
        timePrint ('bye ...')
        return False
    try:
        if '?' == msg or 'help' == msg:
            help()
            return True
        else:
            if '1' == msg:
                msg = 'land'
            elif '0' == msg:
                msg = 'takeoff'

            # send control command
            return tello.executeCommand(msg)

    except Exception as e:
        timePrint ('Error: ' + str(e))
        return False

tello = MyTello(log_level=logging.WARNING)	# logging.DEBUG logging.WARNING logging.INFO
tello.connect(wait_for_state=True)
while True:
    try:
        msg0 = input("0-takeoff, 1-land, 2-end, run, photo, video, sleep, or just type tello commands? ");
        if not msg0:
            timePrint ('bye ...')
            break
        if not executeCommand(msg0):
            break
    except KeyboardInterrupt:
        timePrint ('KeyboardInterrupt  . . .\n')
        break

try:
    timePrint('Stopping Tello with battery: %s' %(str(tello.query_battery())))
except:
    pass
