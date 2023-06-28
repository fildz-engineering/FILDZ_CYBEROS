# The MIT License (MIT)
# Copyright (c) 2023 Edgaras Janušauskas and Inovatorius MB (www.fildz.com)

################################################################################
# FILDZ CYBEROS SETTINGS
#
# Cyberos settings and subscribed cyberwares management.

import errno
import os
import ujson as json
import ubinascii
import uasyncio as asyncio
from uasyncio import Event
import fildz_cyberos as cyberos


# import os
# os.remove('fildz/cyberos.json')
# os.remove('fildz/cyberwares.json')
# os.rmdir('fildz')
# os.listdir()
# os.remove('lib/FILDZ_CYBEROS/__init__.py')
# os.remove('lib/FILDZ_Button/__init__.py')


class Settings:
    _SETTINGS_FILE = '/cyberos.json'
    _PAIRED_FILE = '/cyberwares.json'
    _CONFIG_DIR = 'fildz'

    def __init__(self):
        self._on_save_settings = Event()
        asyncio.create_task(self._event_save_settings())
        self._on_save_cyberwares = Event()
        asyncio.create_task(self._event_save_cyberwares())
        self._load_settings()
        self._load_cyberwares()

    ################################################################################
    # Helpers
    #
    def _dir_exists(self, dirname):
        try:
            return (os.stat(dirname)[0] & 0x4000) != 0
        except OSError:
            return False

    def _file_exists(self, filename):
        try:
            return (os.stat(filename)[0] & 0x4000) == 0
        except OSError:
            return False

    ################################################################################
    # Events
    #
    @property
    def on_save_settings(self):
        return self._on_save_settings

    @property
    def on_save_cyberwares(self):
        return self._on_save_cyberwares

    ################################################################################
    # Tasks
    #
    def _load_settings(self):
        while True:
            if self._dir_exists(self._CONFIG_DIR):
                if self._file_exists(self._CONFIG_DIR + self._SETTINGS_FILE):
                    try:
                        with open(self._CONFIG_DIR + self._SETTINGS_FILE, "r") as config_file:
                            config_str = config_file.read()
                            cyberos.preferences = json.loads(config_str)
                            break
                    except ValueError:
                        break
                else:
                    with open(self._CONFIG_DIR + self._SETTINGS_FILE, 'w'):
                        break
            else:
                os.mkdir(self._CONFIG_DIR)

    def _load_cyberwares(self):
        while True:
            if self._dir_exists(self._CONFIG_DIR):
                if self._file_exists(self._CONFIG_DIR + self._PAIRED_FILE):
                    try:
                        with open(self._CONFIG_DIR + self._PAIRED_FILE, "r") as cyberwares_file:
                            cyberwares_str = cyberwares_file.read()
                            cyberos.cyberwares['subscribed'] = json.loads(cyberwares_str)
                            for cyberware in cyberos.cyberwares['subscribed']:
                                # Convert '00:00:00:00:00:00' ('mac_str') to b'\x00\x00\x00\x00\x00\x00' ('mac').
                                mac_str = cyberos.cyberwares['subscribed'][cyberware]['mac_str']
                                mac_str = mac_str.replace(':', '')
                                mac = ubinascii.unhexlify(mac_str)
                                cyberos.cyberwares['subscribed'][cyberware].update({'mac': mac, 'events': {}})
                            break
                    except ValueError:
                        # print('CYBEROS > Error loading cyberwares')
                        cyberos.cyberwares['subscribed'] = {}
                        break
                else:
                    cyberos.cyberwares['subscribed'] = {}
                    with open(self._CONFIG_DIR + self._PAIRED_FILE, 'w'):
                        break
            else:
                os.mkdir(self._CONFIG_DIR)

    async def _event_save_cyberwares(self):
        while True:
            await self._on_save_cyberwares.wait()
            _paired = {}
            for cyberware in cyberos.cyberwares['subscribed']:
                if 'mac_str' in cyberos.cyberwares['subscribed'][cyberware]:
                    _paired.update({cyberware: {'mac_str': cyberos.cyberwares['subscribed'][cyberware]['mac_str']}})
            while True:
                try:
                    with open(self._CONFIG_DIR + self._PAIRED_FILE, 'w') as config_file:
                        json.dump(_paired, config_file)
                    self._on_save_cyberwares.clear()
                    break
                except OSError as exc:
                    if exc.errno == errno.ENOENT:
                        # Config dir does not exists.
                        os.mkdir(self._CONFIG_DIR)

    async def _event_save_settings(self):
        while True:
            await self._on_save_settings.wait()
            while True:
                try:
                    with open(self._CONFIG_DIR + self._SETTINGS_FILE, 'w') as config_file:
                        json.dump(cyberos.preferences, config_file)
                    self._on_save_settings.clear()
                    break
                except OSError as exc:
                    if exc.errno == errno.ENOENT:
                        # Config dir does not exists.
                        os.mkdir(self._CONFIG_DIR)
