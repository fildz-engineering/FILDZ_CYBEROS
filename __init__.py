# The MIT License (MIT)
# Copyright (c) 2023 Edgaras Janušauskas and Inovatorius MB (www.fildz.com)

################################################################################
# FILDZ CYBEROS
#
# Cyberos and its modules are initialized here.

import uasyncio as asyncio
from fildz_cyberware import CYBERWARE as cyberware
from .settings import Settings as settings
from .network import Network as network
from .listener import Listener as event
from .pairing import Pairing as pairing
from .heartbeat import Heartbeat as heartbeat
import aioespnow as espnow
from .httpserver import HTTPServer as server


async def init():
    # Paired cyberware, their mac addresses and events are stored in dictionary.
    global cyberwares
    cyberwares = dict()

    # Various user preferences stored in a dictionary.
    global preferences
    preferences = dict(ap_boot=False, ap_ssid=None, ap_key='inovator', ap_color=None, ap_color_code=None, ap_channel=13,
                       sta_boot=True, sta_reconnect=False, sta_reconnects=-1, sta_channel=13,
                       sta_ssid=None, sta_key=None,
                       channel_update=False, channel_reset=True,)

    global settings
    settings = settings()

    global cyberware
    cyberware = cyberware()

    global network
    network = network()

    global event
    event = event()

    global pairing
    pairing = pairing()

    global heartbeat
    heartbeat = heartbeat()

    global espnow
    espnow = espnow.AIOESPNow()
    espnow.active(True)

    global server
    server = server()

    # Notify the user that the cyberos is ready.
    await cyberware.pixel.set_color(color=cyberware.pixel.C_GREEN)
    await asyncio.sleep(0)  # Fix for first tones play far too long.
    await cyberware.buzzer.play(index=0)


async def run_forever():
    asyncio.get_event_loop().run_forever()
