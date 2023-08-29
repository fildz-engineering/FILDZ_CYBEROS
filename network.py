# The MIT License (MIT)
# Copyright (c) 2023 Edgaras Janušauskas and Inovatorius MB (www.fildz.com)

################################################################################
# FILDZ CYBEROS NETWORK
#
# Manages STA/AP interface settings and power features.

# TODO:
#  1. Cyberware channel management 'on_ch_change', 'ch_update' etc.
#  2. As "ap_name" used to config the AP, make sure user chosen name is valid to use (length, special characters, etc).
#  3. If "ap_name" changes, update cyberos.cyberwares dictionary and inform paired cyberwares.

import uasyncio as asyncio
from uasyncio import Event
import fildz_cyberos as cyberos
import network
from .network_utils import _event_ap_pixel, _event_ap_power_button, _ap_color_code_update


class Network:
    def __init__(self):
        self._sta_if = network.WLAN(network.STA_IF)
        self._ap_if = network.WLAN(network.AP_IF)

        self._sta_boot = cyberos.preferences['sta_boot']
        self._sta_ssid = cyberos.preferences['sta_ssid']
        self._sta_key = cyberos.preferences['sta_key']
        self._sta_reconnect = cyberos.preferences['sta_reconnect']
        self._sta_reconnects = cyberos.preferences['sta_reconnects']
        self._sta_ch = cyberos.preferences['sta_channel']
        self._sta_hostname = cyberos.preferences['sta_hostname']

        self._ap_boot = cyberos.preferences['ap_boot']
        self._ap_ssid = cyberos.preferences['ap_ssid']
        self._ap_key = cyberos.preferences['ap_key']
        self._ap_color = cyberos.preferences['ap_color']
        self._ap_color_code = cyberos.preferences['ap_color_code']
        self._ap_ch = cyberos.preferences['ap_channel']

        self._ch_reset = cyberos.preferences['channel_reset']
        self._ch_update = cyberos.preferences['channel_update']

        self._on_sta_up = Event()
        self._on_sta_down = Event()
        self._on_sta_active = Event()
        self._on_sta_connected = Event()
        self._on_sta_disconnected = Event()

        self._on_ap_up = Event()
        self._on_ap_down = Event()
        self._on_ap_active = Event()

        self._on_ch_change = Event()
        self._on_wlan_change = Event()

        self._on_ap_pixel = Event()

        # We must generate cyberware AP SSID and color code on first start.
        if self._ap_ssid is None:
            asyncio.create_task(_ap_color_code_update())

        if self._sta_hostname is None:
            self.sta_hostname = cyberos.cyberware.name

        if self._sta_boot:
            self._on_sta_up.set()
        else:
            self._on_sta_down.set()

        if self._ap_boot:
            self._on_ap_up.set()
        else:
            self._on_ap_up.set()  # To update the STA/AP channel.
            self._on_ap_down.set()

        self._on_sta_disconnected.set()

        asyncio.create_task(self._event_sta_up())
        asyncio.create_task(self._event_sta_down())
        asyncio.create_task(self._event_ap_up())
        asyncio.create_task(self._event_ap_down())
        asyncio.create_task(self._event_ch_change())
        asyncio.create_task(_event_ap_power_button())
        asyncio.create_task(_event_ap_pixel())

        # Events.
        cyberos.cyberwares[self._ap_ssid] = (
            {
                'events':
                    {
                        'on_ch_change': self._on_ch_change,
                    }
            })

    ################################################################################
    # Properties
    #
    # Wi-Fi access pont SSID.
    @property
    def sta_ssid(self):
        return self._sta_ssid

    @sta_ssid.setter
    def sta_ssid(self, value):
        self._sta_ssid = value
        cyberos.preferences['sta_ssid'] = value
        cyberos.settings.on_save_settings.set()

    # Wi-Fi access pont password.
    @property
    def sta_key(self):
        return self._sta_key

    @sta_key.setter
    def sta_key(self, value):
        self._sta_key = value
        cyberos.preferences['sta_key'] = value
        cyberos.settings.on_save_settings.set()

    # Reconnect to last saved Wi-Fi AP once STA_IF is active.
    @property
    def sta_reconnect(self):
        return self._sta_reconnect

    @sta_reconnect.setter
    def sta_reconnect(self, value):
        self._sta_reconnect = value
        cyberos.preferences['sta_reconnect'] = value
        cyberos.settings.on_save_settings.set()

    # Number of attempts to reconnect where "0" - disable and "-1" - reconnect forever.
    @property
    def sta_reconnects(self):
        return self._sta_reconnects

    @sta_reconnects.setter
    def sta_reconnects(self, value):
        self._sta_reconnects = value
        cyberos.preferences['sta_reconnects'] = value
        cyberos.settings.on_save_settings.set()

    @property
    def sta_hostname(self):
        return self._sta_hostname

    @sta_hostname.setter
    def sta_hostname(self, value):
        self._sta_hostname = '%s-%s' % (cyberos.cyberware.name, self._ap_color_code) if not len(value) else value
        cyberos.preferences['sta_hostname'] = value
        cyberos.settings.on_save_settings.set()

    # Cyberware AP SSID e.g., "BUTTON-02AD9A-YYG".
    @property
    def ap_ssid(self):
        return self._ap_ssid

    @ap_ssid.setter
    def ap_ssid(self, value):
        self._ap_ssid = '%s-%s' % (cyberos.cyberware.name, self._ap_color_code) if not len(value) else value
        cyberos.preferences['ap_ssid'] = value
        cyberos.settings.on_save_settings.set()

    # Cyberware AP password.
    @property
    def ap_key(self):
        return self._ap_key

    @ap_key.setter
    def ap_key(self, value):
        self._ap_key = value
        cyberos.preferences['ap_key'] = value
        cyberos.settings.on_save_settings.set()

    # Cyberware AP color e.g., ((255, 255, 0), (255, 255, 0), (0, 255, 0))
    @property
    def ap_color(self):
        return self._ap_color

    @ap_color.setter
    def ap_color(self, value):
        self._ap_color = value
        cyberos.preferences['ap_color'] = value
        cyberos.settings.on_save_settings.set()

    # Cyberware AP color code e.g., "YYG".
    @property
    def ap_color_code(self):
        return self._ap_color_code

    @ap_color_code.setter
    def ap_color_code(self, value):
        self._ap_color_code = value
        cyberos.preferences['ap_color_code'] = value
        cyberos.settings.on_save_settings.set()

    # Enable AP_IF on boot.
    @property
    def ap_boot(self):
        return self._ap_boot

    @ap_boot.setter
    def ap_boot(self, value):
        self._ap_boot = value
        cyberos.preferences['ap_boot'] = value
        cyberos.settings.on_save_settings.set()

    # STA_IF channel.
    @property
    def sta_ch(self):
        return self._sta_ch

    @sta_ch.setter
    def sta_ch(self, value):
        self._sta_ch = value
        cyberos.preferences['sta_channel'] = value
        cyberos.settings.on_save_settings.set()

    # Cyberware AP channel.
    @property
    def ap_ch(self):
        return self._ap_ch

    @ap_ch.setter
    def ap_ch(self, value):
        self._ap_ch = value
        cyberos.preferences['ap_channel'] = value
        cyberos.settings.on_save_settings.set()

    # Reset Cyberware AP channel once STA is disconnected from Wi-Fi AP.
    @property
    def ch_reset(self):
        return self._ch_reset

    @ch_reset.setter
    def ch_reset(self, value):
        self._ch_reset = value
        cyberos.preferences['channel_reset'] = value
        cyberos.settings.on_save_settings.set()

    # Update Cyberware AP channel automatically once requested.
    @property
    def ch_update(self):
        return self._ch_update

    @ch_update.setter
    def ch_update(self, value):
        self._ch_update = value
        cyberos.preferences['channel_update'] = value
        cyberos.settings.on_save_settings.set()

    ################################################################################
    # Events
    #
    @property
    def on_sta_active(self):
        return self._on_sta_active

    @property
    def on_sta_up(self):
        return self._on_sta_up

    @property
    def on_sta_down(self):
        return self._on_sta_down

    @property
    def on_sta_connected(self):
        return self._on_sta_connected

    @property
    def on_sta_disconnected(self):
        return self._on_sta_disconnected

    @property
    def on_ap_active(self):
        return self._on_ap_active

    @property
    def on_ap_up(self):
        return self._on_ap_up

    @property
    def on_ap_down(self):
        return self._on_ap_down

    @property
    def on_ch_change(self):
        return self._on_ch_change

    @property
    def on_wlan_change(self):
        return self._on_wlan_change

    @property
    def on_ap_pixel(self):
        return self._on_ap_pixel

    ################################################################################
    # Tasks
    #
    async def connect(self, ssid=None, key=None):
        if ssid is not None and len(ssid):
            print('CYBEROS > Connecting to', ssid)
            self._sta_if.connect(ssid, key)
        else:
            print('CYBEROS > CONNECTION TO AP FAILED')
            return

        _wlan_status = self._sta_if.status()
        while not self._sta_if.isconnected():
            _wlan_status = self._sta_if.status()
            if _wlan_status == 2:
                print('CYBEROS > WRONG PASSWORD FOR {} AP'.format(ssid))
                return
            if _wlan_status == 3:
                print('CYBEROS > {} AP NOT FOUND'.format(ssid))
                return
            if _wlan_status == 4:
                print('CYBEROS > CONNECTION TO {} AP FAILED'.format(ssid))
                return
            await asyncio.sleep(0)
        self._on_sta_disconnected.clear()
        self._on_sta_connected.set()
        self._on_wlan_change.set()

        # Disable the power-saving mode on the STA_IF interface for reliable ESP-NOW communication.
        self._sta_if.config(pm=network.WLAN.PM_NONE)

        # Save ssid, key and the channel if changed.
        if ssid is not None and ssid != self._sta_ssid:
            self.sta_ssid = ssid

        if key is not None and key != self._sta_key:
            self.sta_key = key

        self._sta_ch = self._sta_if.config('channel')
        if self._sta_ch != cyberos.preferences['sta_channel']:
            self.sta_ch = self._sta_ch
        print('CYBEROS > Connected to {} on channel {}'.format(self._sta_ssid, self._sta_ch))

    async def disconnect(self):
        self._sta_if.disconnect()
        while self._sta_if.isconnected():
            await asyncio.sleep(0)
        self._on_sta_connected.clear()
        self._on_sta_disconnected.set()

        self._sta_if.config(pm=network.WLAN.PM_PERFORMANCE)

        if self._ch_reset:
            if self._on_ap_active.is_set():
                self._on_ap_up.set()
            else:
                self._on_ap_up.set()
                self._on_ap_down.set()
        self._on_wlan_change.set()
        print('CYBEROS > Disconnected from', self._sta_ssid)

    async def _event_sta_up(self):
        while True:
            await self._on_sta_up.wait()
            self._sta_if.active(True)
            while not self._sta_if.active():
                await asyncio.sleep(0)
            self._sta_if.config(hostname=self._sta_hostname,
                                auto_connect=self._sta_reconnect,
                                reconnects=self._sta_reconnects,
                                pm=network.WLAN.PM_PERFORMANCE)
            self._on_sta_up.clear()
            self._on_sta_active.set()
            self._on_wlan_change.set()
            print('CYBEROS > STA up')

    async def _event_sta_down(self):
        while True:
            await self._on_sta_down.wait()
            self._sta_if.active(False)
            self._on_sta_down.clear()
            self._on_sta_active.clear()
            self._on_wlan_change.set()
            print('CYBEROS > STA down')

    async def _event_ap_up(self):
        while True:
            await self._on_ap_up.wait()
            self._ap_if.active(True)
            while not self._ap_if.active():
                await asyncio.sleep(0)
            self._ap_if.config(ssid=self._ap_ssid,
                               key=self._ap_key,
                               mac=cyberos.cyberware.mac_public,
                               channel=self._ap_ch)

            self._on_ap_up.clear()
            self._on_ap_active.set()
            self._on_wlan_change.set()
            print('CYBEROS > AP up')

    async def _event_ap_down(self):
        while True:
            await self._on_ap_down.wait()
            self._ap_if.active(False)
            self._on_ap_down.clear()
            self._on_ap_active.clear()
            self._on_wlan_change.set()
            print('CYBEROS > AP down')

    async def _event_ch_change(self):
        pass
