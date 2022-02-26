#!/usr/bin/python3
# File name   : config.py
# Description : persistent configuration management class

class Config(object):
    """ simple key=value persistent configuration management class """
    def __init__(self, filePath, autoSave=True):
        """ construct a Config by loading configuration "=" separated settings from file
        """
        self.filePath = filePath
        self.autoSave = autoSave
        self.dirty = False
        self.settings = {}
        self.addSettings(filePath)

    def addSettings(self, filePath):
        """ get config settings from a file """
        with open(filePath) as f:
            key = None
            for line in f.readlines():
                line = line.strip()  # strip possible trailing \n\r
                if line.startswith('#') or len(line) == 0:
                    pass
                else:
                    index = line.find('=')
                    if index > 1:
                        key = line[0:index]
                        value = line[index+1:]
                        self.settings[key] = value
                    elif key is None:
                        print('Invalid setting: ' + line)
                    else:
                        # append to previous key
                        self.settings[key] = self.settings[key] + line

    def get(self, key):
        """ get the setting by key """
        value = self.settings.get(key, None)
        return value

    def getOrAdd(self, key, defaultValue):
        """ get the setting by key, add a new key with defaultValue if no key """
        value = self.settings.get(key, None)
        if value != None:
            return value
        else:
            return self.set(key, defaultValue)

    def getOrAddBool(self, key, defaultValue):
        """ get the bool setting by key, add a new key with defaultValue if no key """
        value = self.settings.get(key, None)
        if value != None:
            val = value.lower()
            return val == '1' or val == 'true' or val == 'yes'
        else:
            return self.set(key, defaultValue)

    def getOrAddInt(self, key, defaultValue):
        """ get the integer setting by key, add a new key with defaultValue if no key """
        return int(self.getOrAdd(key, defaultValue))

    def getOrAddFloat(self, key, defaultValue):
        """ get the float setting by key, add a new key with defaultValue if no key """
        return float(self.getOrAdd(key, defaultValue))

    def set(self, key, value):
        """ update/add the setting value by key """
        self.settings[key] = value
        self.dirty = True
        if self.autoSave:
            self.save()
        return value

    def save(self, forceSave=False, filePath=None):
        """ save the config back to file """
        if self.dirty or forceSave:
            if filePath is None:
                filePath = self.filePath
            with open(filePath, "w") as f:
                for key in self.settings:
                    f.write(key + '=' + str(self.settings[key]) + '\n')
            self.dirty = False


