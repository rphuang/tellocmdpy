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

def doCommandFromFile(fileName):
    ''' load tello commands from file and send to tello '''
    timePrint('Loading command file: %s' %fileName)
    with open(fileName, 'r') as file:
        for line in file:
            line = line.strip()
            if len(line) == 0:
                pass
            elif '#' == line[0]:
                pass
            else:
                executeCommand(line)

def executeCommand(cmdstr):
    ''' execute the command str. returns False to quit '''
    msg = cmdstr.lower()
    if 'end' in msg or '2' == msg:
        timePrint ('bye ...')
        return False
    try:
        if '1' == msg or 'land' == msg:
            tello.land()
        elif '0' == msg or 'takeoff' == msg:
            tello.takeoff()
        elif 'p' == msg or 'photo' == msg:
            tello.takePicture('%s.png' %timestamp())
        elif 'v' == msg or 'video' == msg:
            tello.startOrStopVideo('%s.avi' %timestamp())
        elif '?' == msg or 'help' == msg:
            help()
        elif '?' == msg[-1]:
            # send read command
            tello.send_read_command(msg)
        elif 'sleep' in msg:
            value = float(getValue(cmdstr, 1.0))
            timePrint('Sleeping %f seconds ...' %value)
            time.sleep(value)
        elif 'run' in msg or 'load' in msg:
            doCommandFromFile(getValue(cmdstr, 'telloCommands.txt'))
        else:
            # send control command
            #msg = msg.encode(encoding="utf-8") 
            tello.send_control_command(msg)
        return True
    except Exception as e:
        timePrint ('Error: ' + str(e))

def getValue(cmdstr, default):
    ''' get the command value from the str '''
    try:
        cmd, value = cmdstr.split(' ')
        return value
    except:
        return default

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
