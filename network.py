# The MIT License (MIT)
# Copyright (c) 2023 Edgaras Janušauskas and Inovatorius MB (www.fildz.com)

################################################################################
# FILDZ CYBEROS NETWORK
#
# Manages STA/AP interface settings and power features.

# TODO:
#  1. Cyberware channel management 'on_ch_change', 'ch_update' etc.
#  2. Fix connect() to stop connecting to Wi-Fi AP forever.
#  3. Check connect() with open Wi-Fi AP.

import uasyncio as asyncio
from uasyncio import Event
import fildz_cyberos as cyberos
import network


class Network:
    def __init__(self):
        self._ssid = cyberos.preferences['ssid']
        self._key = cyberos.preferences['key']

        self._sta_active = False
        self._sta_reconnect = cyberos.preferences['sta_reconnect']
        self._sta_reconnects = cyberos.preferences['sta_reconnects']

        self._on_sta_up = Event()
        asyncio.create_task(self._event_sta_up())
        self._on_sta_active = Event()
        self._on_sta_up.set()  # STA interface is always active and should not be disabled.
        self._on_sta_down = Event()
        asyncio.create_task(self._event_sta_down())
        self._on_sta_connected = Event()
        self._on_sta_disconnected = Event()
        asyncio.create_task(self._event_sta_disconnect())

        self._sta_ch = cyberos.preferences['sta_channel']
        self._ap_ch = cyberos.preferences['ap_channel']
        self._ch_reset = cyberos.preferences['channel_reset']
        self._ch_update = cyberos.preferences['channel_update']
        self._on_ch_change = Event()
        asyncio.create_task(self._event_ch_change())
        cyberos.cyberwares[cyberos.cyberware.ap_name]['events'].update(
            {
                'on_ch_change': self._on_ch_change,
            })

        self._ap_active = False
        self._ap_boot = cyberos.preferences['ap_boot']

        self._on_ap_up = Event()
        asyncio.create_task(self._event_ap_up())
        self._on_ap_active = Event()
        self._on_ap_down = Event()
        asyncio.create_task(self._event_ap_down())
        if self._ap_boot:
            self._on_ap_up.set()
        else:
            self._on_ap_up.set()  # To update the STA and AP channel.
            self._on_ap_down.set()
        asyncio.create_task(self._event_ap_activate())
        self._on_ap_pixel = Event()
        asyncio.create_task(self._event_ap_pixel())

    ################################################################################
    # Properties
    #
    @property
    def ssid(self):
        return self._ssid

    @ssid.setter
    def ssid(self, value):
        self._ssid = value
        cyberos.preferences['ssid'] = value
        cyberos.settings.on_save_settings.set()

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value
        cyberos.preferences['key'] = value
        cyberos.settings.on_save_settings.set()

    @property
    def sta_active(self):
        return self._sta_active

    @property
    def sta_reconnect(self):
        return self._sta_reconnect

    @sta_reconnect.setter
    def sta_reconnect(self, value):
        self._sta_reconnect = value
        cyberos.preferences['sta_reconnect'] = value
        cyberos.settings.on_save_settings.set()

    @property
    def sta_reconnects(self):
        return self._sta_reconnects

    @sta_reconnects.setter
    def sta_reconnects(self, value):
        self._sta_reconnects = value
        cyberos.preferences['sta_reconnects'] = value
        cyberos.settings.on_save_settings.set()

    @property
    def ap_active(self):
        return self._ap_active

    @property
    def ap_boot(self):
        return self._ap_boot

    @ap_boot.setter
    def ap_boot(self, value):
        self._ap_boot = value
        cyberos.preferences['ap_boot'] = value
        cyberos.settings.on_save_settings.set()

    @property
    def sta_ch(self):
        return self._sta_ch

    @sta_ch.setter
    def sta_ch(self, value):
        self._sta_ch = value
        cyberos.preferences['sta_channel'] = value
        cyberos.settings.on_save_settings.set()

    @property
    def ap_ch(self):
        return self._ap_ch

    @ap_ch.setter
    def ap_ch(self, value):
        self._ap_ch = value
        cyberos.preferences['ap_channel'] = value
        cyberos.settings.on_save_settings.set()

    @property
    def ch_reset(self):
        return self._ch_reset

    @ch_reset.setter
    def ch_reset(self, value):
        self._ch_reset = value
        cyberos.preferences['channel_reset'] = value
        cyberos.settings.on_save_settings.set()

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
    def on_ap_up(self):
        return self._on_ap_up

    @property
    def on_ap_down(self):
        return self._on_ap_down

    @property
    def on_ch_change(self):
        return self._on_ch_change

    ################################################################################
    # Tasks
    #
    async def connect(self, ssid=None, key=None):
        if ssid is None and self._ssid is not None:
            print('CYBEROS > Reconnecting to', self._ssid)
            network.WLAN(network.STA_IF).connect()
        elif ssid is not None and key is not None:
            print('CYBEROS > Connecting to', ssid)
            network.WLAN(network.STA_IF).connect(ssid, key)
        else:
            return

        # Fix this because this can take forever?
        while not network.WLAN(network.STA_IF).isconnected():
            await asyncio.sleep(0)
        self._on_sta_connected.set()

        # Disable the power-saving mode on the STA_IF interface for reliable ESP-NOW communication.
        network.WLAN(network.STA_IF).config(pm=network.WLAN.PM_NONE)

        # Save ssid, key and the channel if changed.
        if ssid is not None and ssid != self._ssid:
            self._ssid = ssid
            cyberos.preferences['ssid'] = ssid
            if not cyberos.settings.on_save_settings.is_set():
                cyberos.settings.on_save_settings.set()

        if key is not None and key != self._key:
            self._key = key
            cyberos.preferences['key'] = key
            if not cyberos.settings.on_save_settings.is_set():
                cyberos.settings.on_save_settings.set()

        self._sta_ch = network.WLAN(network.STA_IF).config('channel')
        if self._sta_ch != cyberos.preferences['sta_channel']:
            cyberos.preferences['sta_channel'] = self._sta_ch
            if not cyberos.settings.on_save_settings.is_set():
                cyberos.settings.on_save_settings.set()

        print('CYBEROS > Connected to {} on channel {}'.format(self._ssid, self._sta_ch))

    async def disconnect(self):
        print('CYBEROS > Disconnecting from', self._ssid)
        self._on_sta_connected.clear()
        self._on_sta_disconnected.set()

    async def _event_ch_change(self):
        pass

    async def _event_sta_up(self):
        while True:
            await self._on_sta_up.wait()
            network.WLAN(network.STA_IF).active(True)
            network.WLAN(network.STA_IF).config(auto_connect=cyberos.preferences['sta_reconnect'])
            network.WLAN(network.STA_IF).config(reconnects=cyberos.preferences['sta_reconnects'])
            network.WLAN(network.STA_IF).config(pm=network.WLAN.PM_PERFORMANCE)
            self._sta_active = True
            self._on_sta_up.clear()
            if not self._on_sta_active.is_set():
                self._on_sta_active.set()
            print('CYBEROS > STA up')

    async def _event_sta_down(self):
        while True:
            await self._on_sta_down.wait()
            network.WLAN(network.STA_IF).active(False)
            self._sta_active = False
            self._on_sta_down.clear()
            self._on_sta_active.clear()
            print('CYBEROS > STA down')

    async def _event_sta_disconnect(self):
        while True:
            await self._on_sta_disconnected.wait()
            network.WLAN(network.STA_IF).disconnect()
            while network.WLAN(network.STA_IF).isconnected():
                await asyncio.sleep(0)
            network.WLAN(network.STA_IF).config(pm=network.WLAN.PM_PERFORMANCE)
            self._on_sta_disconnected.clear()

            if self._ch_reset:
                if self._ap_active:
                    self._on_ap_up.set()
                else:
                    self._on_ap_up.set()
                    self._on_ap_down.set()

            print('CYBEROS > Disconnected from', self._ssid)

    async def _event_ap_activate(self):
        while True:
            await cyberos.cyberware.power_button.on_double_click.wait()
            try:
                await asyncio.wait_for_ms(cyberos.cyberware.power_button.on_down.wait(),
                                          cyberos.cyberware.power_button._double_click_ms)
            except asyncio.TimeoutError:
                continue
            try:
                await asyncio.wait_for(cyberos.cyberware.power_button.on_up.wait(), 3)
            except asyncio.TimeoutError:
                if self._ap_active:
                    self._on_ap_down.set()
                    self._on_ap_pixel.clear()
                    await asyncio.sleep(0)  # Fix for first tones play far too long.
                    await cyberos.cyberware.buzzer.play(index=1)
                else:
                    self._on_ap_up.set()
                    self._on_ap_pixel.set()
                    await asyncio.sleep(0)  # Fix for first tones play far too long.
                    await cyberos.cyberware.buzzer.play(index=0)
                if cyberos.cyberware.power_button.on_hold.is_set():
                    await cyberos.cyberware.power_button.on_up.wait()

    async def _event_ap_up(self):
        while True:
            await self._on_ap_up.wait()
            network.WLAN(network.AP_IF).active(True)
            network.WLAN(network.AP_IF).config(ssid=cyberos.cyberware.ap_name,
                                               mac=cyberos.cyberware.mac_public,
                                               channel=self._ap_ch)

            self._ap_active = True
            self._on_ap_up.clear()
            if not self._on_ap_active.is_set():
                self._on_ap_active.set()
            print('CYBEROS > AP up')

    async def _event_ap_down(self):
        while True:
            await self._on_ap_down.wait()
            network.WLAN(network.AP_IF).active(False)
            self._ap_active = False
            self._on_ap_down.clear()
            self._on_ap_active.clear()
            print('CYBEROS > AP down')

    async def _event_ap_pixel(self):
        while True:
            await self._on_ap_pixel.wait()
            await cyberos.cyberware.pixel.set_color(cyberos.cyberware.pixel.C_BLANK)
            await asyncio.sleep(2)
            await cyberos.cyberware.pixel.set_color(cyberos.cyberware.ap_color[0])
            await asyncio.sleep(1)
            await cyberos.cyberware.pixel.set_color(cyberos.cyberware.pixel.C_BLANK)
            await asyncio.sleep(1)
            await cyberos.cyberware.pixel.set_color(cyberos.cyberware.ap_color[1])
            await asyncio.sleep(1)
            await cyberos.cyberware.pixel.set_color(cyberos.cyberware.pixel.C_BLANK)
            await asyncio.sleep(1)
            await cyberos.cyberware.pixel.set_color(cyberos.cyberware.ap_color[2])
            await asyncio.sleep(1)
            if not self._on_ap_pixel.is_set():
                await cyberos.cyberware.pixel.set_color(cyberos.cyberware.pixel.C_BLANK)
                await asyncio.sleep(1)
                await cyberos.cyberware.pixel.set_color(cyberos.cyberware.pixel.C_GREEN)
