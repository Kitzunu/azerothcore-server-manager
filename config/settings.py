import configparser
import os

SETTINGS_FILE = "settings.ini"

class SettingsManager:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.load()

    def load(self):
        if not os.path.exists(SETTINGS_FILE):
            self._create_default()
        self.config.read(SETTINGS_FILE)

    def _create_default(self):
        self.config['Paths'] = {
            'worldserver': r'D:\build\bin\RelWithDebInfo\worldserver.exe',
            'authserver': r'D:\build\bin\RelWithDebInfo\authserver.exe',
            'world_log_file': r'D:\build\bin\RelWithDebInfo\Server.log',
            'auth_log_file': r'D:\build\bin\RelWithDebInfo\Auth.log',
        }
        self.config['General'] = {
            'restart_worldserver_on_crash': '1',
        }
        self.config['Database'] = {
            'database_host': '127.0.0.1',
            'database_port': '3306',
            'database_user': 'acore',
            'database_password': 'acore',
            'database_world': 'acore_world',
            'database_characters': 'acore_characters',
            'database_auth': 'acore_auth',
        }
        with open(SETTINGS_FILE, 'w') as configfile:
            self.config.write(configfile)

    def save(self):
        with open(SETTINGS_FILE, 'w') as configfile:
            self.config.write(configfile)

    def get(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)

    def getboolean(self, section, key, fallback=False):
        return self.config.getboolean(section, key, fallback=fallback)

    def set(self, section, key, value):
        self.config.set(section, key, str(value))
