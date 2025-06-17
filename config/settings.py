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

    def load_settings(self):      
        self.WORLD_PATH = self.get('Paths', 'worldserver')
        self.AUTH_PATH = self.get('Paths', 'authserver')
        self.WORLD_LOG_FILE = self.get('Paths', 'world_log_file')
        self.AUTH_LOG_FILE = self.get('Paths', 'auth_log_file')
        self.RESTART_WORLDSERVER_ON_CRASH = self.getboolean('General', 'restart_worldserver_on_crash')
        self.DATABASE_HOST = self.get('Database', 'database_host')
        self.DATABASE_PORT = self.get('Database', 'database_port')
        self.DATABASE_USER = self.get('Database', 'database_user')
        self.DATABASE_PASSWORD = self.get('Database', 'database_password')
        self.DATABASE_WORLD = self.get('Database', 'database_world')
        self.DATABASE_CHARACTERS = self.get('Database', 'database_characters')
        self.DATABASE_AUTH = self.get('Database', 'database_auth')

    def save_settings(self):
        self.set('Paths', 'worldserver', self.WORLD_PATH)
        self.set('Paths', 'authserver', self.AUTH_PATH)
        self.set('Paths', 'world_log_file', self.WORLD_LOG_FILE)
        self.set('Paths', 'auth_log_file', self.AUTH_LOG_FILE)
        self.set('General', 'restart_worldserver_on_crash', self.RESTART_WORLDSERVER_ON_CRASH)
        self.set('Database', 'database_host', self.DATABASE_HOST)
        self.set('Database', 'database_port', self.DATABASE_PORT)
        self.set('Database', 'database_user', self.DATABASE_USER)
        self.set('Database', 'database_password', self.DATABASE_PASSWORD)
        self.set('Database', 'database_world', self.DATABASE_WORLD)
        self.set('Database', 'database_characters', self.DATABASE_CHARACTERS)
        self.set('Database', 'database_auth', self.DATABASE_AUTH)

        self.save()
