# The MIT License (MIT)
# Copyright (c) 2023 Edgaras Janušauskas and Inovatorius MB (www.fildz.com)

################################################################################
# FILDZ CYBEROS NETWORK UTILITIES
#
# Variety of generators that depend on WLAN.

import fildz_cyberos as cyberos
import uasyncio as asyncio


# Generate AP name and color code.
async def _ap_color_code_update():
    import random
    c1 = cyberos.cyberware.pixel.COLORS[random.getrandbits(3)]
    c2 = cyberos.cyberware.pixel.COLORS[random.getrandbits(3)]
    c3 = cyberos.cyberware.pixel.COLORS[random.getrandbits(3)]
    cyberos.network.ap_color = (c1[1], c2[1], c3[1])
    cyberos.network.ap_color_code = '%s%s%s' % (c1[0], c2[0], c3[0])
    if cyberos.network.ap_ssid is None or cyberos.network.ap_ssid[:-4] == cyberos.cyberware.name:
        cyberos.network.ap_ssid = '%s-%s' % (cyberos.cyberware.name, cyberos.network.ap_color_code)


# Enable AP on double click and hold.
async def _event_ap_power_button():
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
            if cyberos.network.on_ap_active.is_set():
                cyberos.network.on_ap_down.set()
                cyberos.network.on_ap_pixel.clear()
                await asyncio.sleep(0)  # Fix for first tones play far too long.
                await cyberos.cyberware.buzzer.play(index=1)
            else:
                cyberos.network.on_ap_up.set()
                cyberos.network.on_ap_pixel.set()
                await asyncio.sleep(0)  # Fix for first tones play far too long.
                await cyberos.cyberware.buzzer.play(index=0)
            if cyberos.cyberware.power_button.on_hold.is_set():
                await cyberos.cyberware.power_button.on_up.wait()


# Enable built-in LED RGB to show color code once AP is enabled via power button.
async def _event_ap_pixel():
    while True:
        await cyberos.network.on_ap_pixel.wait()
        for color in [cyberos.network.ap_color[0], cyberos.network.ap_color[1], cyberos.network.ap_color[2]]:
            await cyberos.cyberware.pixel.set_color(color=color)
            await asyncio.sleep_ms(500)
            await cyberos.cyberware.pixel.set_color(color=cyberos.cyberware.pixel.C_BLANK)
            await asyncio.sleep_ms(500)
        await asyncio.sleep_ms(1000)
        if not cyberos.network.on_ap_pixel.is_set():
            await cyberos.cyberware.pixel.set_color(color=cyberos.cyberware.pixel.C_GREEN)
