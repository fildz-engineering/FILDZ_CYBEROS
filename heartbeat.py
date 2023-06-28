# The MIT License (MIT)
# Copyright (c) 2023 Edgaras Janušauskas and Inovatorius MB (www.fildz.com)

################################################################################
# FILDZ CYBEROS HEARTBEAT
#
# Send periodic ping to paired cyberware.

# TODO:
#  1. Create task to send pings.
#  2. Once pong received, update the web interface.

import uasyncio as asyncio
from uasyncio import Event
import fildz_cyberos as cyberos


class Heartbeat:
    def __init__(self):
        self._on_ping = Event()
        asyncio.create_task(self._event_ping())
        self._on_pong = Event()
        asyncio.create_task(self._event_pong())
        cyberos.cyberwares[cyberos.cyberware.ap_name]['events'].update(
            {
                'on_ping': self._on_ping,
                'on_pong': self._on_pong
            })

    ################################################################################
    # Events
    #
    @property
    def on_ping(self):
        return self._on_ping

    @property
    def on_pong(self):
        return self._on_pong

    ################################################################################
    # Tasks
    #
    # Received a ping.
    async def _event_ping(self):
        while True:
            await self._on_ping.wait()
            self._on_ping.clear()
            # print('Ping from', cyberos.event.sender)

    # Received a pong.
    async def _event_pong(self):
        while True:
            await self._on_pong.wait()
            self._on_pong.clear()
            # print('Pong from', cyberos.event.sender)
