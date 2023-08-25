# The MIT License (MIT)
# Copyright (c) 2023 Edgaras Janušauskas and Inovatorius MB (www.fildz.com)

################################################################################
# FILDZ CYBEROS NETWORK
#
# Manages STA/AP interface settings and power features.

# TODO:
#  1. Cyberware channel management 'on_ch_change', 'ch_update' etc.
#  2. Fix connect() to stop connecting to Wi-Fi AP forever.
#  3. Check connect() with open Wi-Fi AP, without ssid and key.
#  4. As "ap_name" used to config the AP, make sure user chosen name is valid to use (length, special characters, etc).
#  5. If "ap_name" changes, update cyberos.cyberwares dictionary.
#  6. _event_ap_pixel() will keep the old pixel colors.
#  7. Test self._sta_if.config(auto_connect=cyberos.preferences['sta_reconnect'])

import uasyncio as asyncio
from uasyncio import Event
import fildz_cyberos as cyberos
import network


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

        # We must generate cyberware AP SSID on first start.
        if self._ap_ssid is None:
            asyncio.create_task(self._event_ap_color_code_update())

        if self._sta_boot:
            self._on_sta_up.set()
        else:
            self._on_sta_down.set()

        if self._ap_boot:
            self._on_ap_up.set()
        else:
            self._on_ap_up.set()  # To update the STA/AP channel.
            self._on_ap_down.set()

        if not self._sta_reconnect:
            self._on_sta_disconnected.set()

        asyncio.create_task(self._event_sta_up())
        asyncio.create_task(self._event_sta_down())
        asyncio.create_task(self._event_ap_up())
        asyncio.create_task(self._event_ap_down())
        asyncio.create_task(self._event_ch_change())
        asyncio.create_task(self._event_ap_activate())
        asyncio.create_task(self._event_ap_pixel())

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

    # Cyberware AP color code e.g., "YYG".
    @property
    def ap_color_code(self):
        return self._ap_color_code

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

    ################################################################################
    # Tasks
    #
    async def connect(self, ssid=None, key=None):
        if ssid is None and self._sta_ssid is not None:
            print('CYBEROS > Reconnecting to', self._sta_ssid)
            self._sta_if.connect()
        elif ssid is not None and key is not None:
            print('CYBEROS > Connecting to', ssid)
            self._sta_if.connect(ssid, key)
        else:
            return

        # Fix this because this can take forever?
        while not self._sta_if.isconnected():
            # Use self._sta_if.status()
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
            self._sta_if.config(auto_connect=cyberos.preferences['sta_reconnect'],
                                reconnects=cyberos.preferences['sta_reconnects'],
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

    # Generate AP name and color code.
    async def _event_ap_color_code_update(self):
        import random
        c1 = cyberos.cyberware.pixel.COLORS[random.getrandbits(3)]
        c2 = cyberos.cyberware.pixel.COLORS[random.getrandbits(3)]
        c3 = cyberos.cyberware.pixel.COLORS[random.getrandbits(3)]
        self._ap_color = (c1[1], c2[1], c3[1])
        cyberos.preferences['ap_color'] = self._ap_color
        self._ap_color_code = '%s%s%s' % (c1[0], c2[0], c3[0])
        cyberos.preferences['ap_color_code'] = self._ap_color_code
        self.ap_ssid = '%s-%s' % (cyberos.cyberware.name, self._ap_color_code) if self._ap_ssid is None else self._ap_ssid

    # Enable AP on double click and hold.
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
                if self._on_ap_active.is_set():
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

    # Enable built-in LED RGB to show color code once AP is enabled via power button.
    async def _event_ap_pixel(self):
        pass
        # while True:
        #     await self._on_ap_pixel.wait()
        #     for color in [cyberos.cyberware.pixel.C_BLANK, self._ap_color[0],
        #                   cyberos.cyberware.pixel.C_BLANK, self._ap_color[1],
        #                   cyberos.cyberware.pixel.C_BLANK, self._ap_color[2]]:
        #         await cyberos.cyberware.pixel.set_color(color=color)
        #         await asyncio.sleep(1)
        #         if not self._on_ap_pixel.is_set():
        #             await cyberos.cyberware.pixel.set_color(color=cyberos.cyberware.pixel.C_BLANK)
        #             await asyncio.sleep(1)
        #             await cyberos.cyberware.pixel.set_color(color=cyberos.cyberware.pixel.C_GREEN)
        #             break
