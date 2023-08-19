# The MIT License (MIT)
# Copyright (c) 2023 Edgaras Janušauskas and Inovatorius MB (www.fildz.com)

################################################################################
# FILDZ CYBEROS PAIRING
#
# Pairing of two (or more) cyberwares goes like this:
# 1. enter pairing mode by holding power button for 3 s.;
# 2. cyberware then disconnects from Wi-Fi AP (if connected);
# 3. cyberware enables AP interface;
# 4. cyberware sends pairing request to "public" MAC address for 3 seconds (1 request per second);
# 5. if no one responds, we stop and wait for the event to repeat this task;
# 6. if we do receive a response, we save the data and pairing continue paring (if 3 seconds has not passed yet).

# TODO:
#  1. Pairing mechanism is unreliable due to if one cyberware sends last pairing request while second cyberware sends
#  pairing request after it, first cyberware will receive the request while the other one will not.

import uasyncio as asyncio
from uasyncio import Event
import ubinascii
import fildz_cyberos as cyberos


class Pairing:
    def __init__(self):
        self._on_pair = Event()
        asyncio.create_task(self._event_pair())
        self._on_pairing = Event()
        asyncio.create_task(self._event_pairing())
        self._on_paired = Event()
        asyncio.create_task(self._event_pairing_mode())
        cyberos.cyberwares[cyberos.cyberware.ap_name]['events'].update(
            {
                'on_pairing': self._on_pairing,
            })

    ################################################################################
    # Events
    #
    @property
    def on_pair(self):
        return self._on_pair

    @property
    def on_pairing(self):
        return self._on_pairing

    @property
    def on_paired(self):
        return self._on_paired

    ################################################################################
    # Tasks
    #
    # Pairing mode.
    async def _event_pairing_mode(self):
        _sta_reconnect = False
        _ap_disable = False
        while True:
            await cyberos.cyberware.power_button.on_click.wait()
            try:
                await asyncio.wait_for_ms(cyberos.cyberware.power_button.on_down.wait(),
                                          cyberos.cyberware.power_button._double_click_ms)
            except asyncio.TimeoutError:
                continue
            try:
                await asyncio.wait_for(cyberos.cyberware.power_button.on_up.wait(), 3)
            except asyncio.TimeoutError:
                # print('CYBEROS > Pairing mode started')
                if cyberos.network.on_sta_connected.is_set():
                    _sta_reconnect = True
                    await cyberos.network.disconnect()
                else:
                    _sta_reconnect = False
                if cyberos.network.on_ap_active.is_set():
                    _ap_disable = False
                else:
                    _ap_disable = True
                    cyberos.network.on_ap_up.set()
                self._on_pair.set()
                await asyncio.sleep(3)
                self._on_pair.clear()
                # print('CYBEROS > Pairing mode timeout')
                if _sta_reconnect:
                    await cyberos.network.connect()
                if _ap_disable:
                    cyberos.network.on_ap_down.set()
                if cyberos.cyberware.power_button.on_hold.is_set():
                    await cyberos.cyberware.power_button.on_up.wait()

    # Send pairing request.
    async def _event_pair(self):
        while True:
            await self._on_pair.wait()
            event = await cyberos.event.encode('on_pairing',
                                               (cyberos.cyberware.mac_private,
                                                cyberos.network.ap_ch.to_bytes(1, 'little')))
            # Send pairing request every second.
            while self._on_pair.is_set():
                # print('CYBEROS > Pairing mode')
                await cyberos.espnow.asend(cyberos.cyberware.mac_public, event, sync=True)
                await asyncio.sleep(1)

    # Received a new pairing request.
    async def _event_pairing(self):
        while True:
            await self._on_pairing.wait()
            # Pairing mode is active?
            if self._on_pair.is_set():
                # Are we paired with the cyberware?
                if cyberos.event.sender in cyberos.cyberwares['subscribed']:
                    if 'mac' in cyberos.cyberwares['subscribed'][cyberos.event.sender]:
                        self._on_pairing.clear()
                        continue
                    else:
                        # We are not paired, but subscribed to cyberware events.
                        cyberos.cyberwares['subscribed'][cyberos.event.sender].update({
                            'mac': cyberos.event.args[0],
                            'mac_str': ubinascii.hexlify(cyberos.event.args[0], ':').decode().upper(),
                            'channel': int.from_bytes(cyberos.event.args[1], 'little')})
                else:
                    cyberos.cyberwares['subscribed'][cyberos.event.sender] = {
                        'mac': cyberos.event.args[0],
                        'mac_str': ubinascii.hexlify(cyberos.event.args[0], ':').decode().upper(),
                        'channel': int.from_bytes(cyberos.event.args[1], 'little'),
                        'events': {}}
                # print('CYBEROS > Paired with', cyberos.event.sender)
                self._on_paired.set()
                cyberos.settings.on_save_cyberwares.set()
                self._on_pairing.clear()
                self._on_paired.clear()
                await cyberos.cyberware.buzzer.play(2)
            else:
                self._on_pairing.clear()
