# FILDZ CYBEROS

IoT messaging framework built on MicroPython and ESP-NOW for ESP8266/ESP8285 devices.

CYBEROS was developed for [CYBERCORE X1](https://www.indiegogo.com/projects/cybercore-x1-a-tiny-wi-fi-module#/) that was kickstarted on Indiegogo. The module is used to develop pocket-sized computers with a variety of sensors on board for quick programming and prototyping. These compact computers are called [CYBERWARE](https://www.indiegogo.com/projects/cyberware-next-gen-wireless-prototyping-platform/coming_soon).

## Features

* Completely asynchronous.
* Bluetooth like pairing between ESP devices.
* Paired ESP devices are saved in `fildz/cyberwares.json`.
* Events are send and received via ESP-NOW.
* Listen for the events from all or specific ESP devices.
* APIs allow to extend the events ESP can subscribe to (see [fildz_button](https://github.com/fildz-engineering/FILDZ_CYBEROS_Button) and [fildz_button_api](https://github.com/fildz-engineering/FILDZ_CYBEROS_Button_API)).
* Network and power features management.
* User preferences are saved in `fildz/cyberos.json`.

## Setup

1. Download and extract .zip file contents to fildz_cyberos folder.
2. Upload fildz_cyberos folder to your MicroPython powered device.

## Requirements

1. FILDZ custom build of [MicroPython](https://github.com/fildz-engineering/FILDZ_CYBEROS_FIRMWARE).
2. [CYBERWARE API](https://github.com/fildz-engineering/FILDZ_CYBERWARE).
3. Libraries [fildz_button](https://github.com/fildz-engineering/FILDZ_CYBEROS_Button), [fildz_buzzer](https://github.com/fildz-engineering/FILDZ_CYBEROS_Buzzer) and [fildz_neopixel](https://github.com/fildz-engineering/FILDZ_CYBEROS_NeoPixel).
4. (Optional) APIs [fildz_button_api](https://github.com/fildz-engineering/FILDZ_CYBEROS_Button_API).

## Usage

### main.py:

```Python
import uasyncio as asyncio
import fildz_cyberos as cyberos


async def main():
    await cyberos.init()
    # Your code here.
    await cyberos.run_forever()

asyncio.run(main())
```

### Subscribe to button click events:

```Python
from fildz_button_api import ButtonAPI


async def btn_clicked():
    print('Button clicked')

async def main():
    await cyberos.init()
    btn = ButtonAPI('BUTTON-0F889A-ABW')  # Listen for events from this cyberware. 
    btn.on_click = btn_clicked  # Once "on_click" event received, run btn_clicked() coroutine.
    await cyberos.run_forever()

asyncio.run(main())
```

## Documentation

[CYBEROS WIKI](https://github.com/fildz-engineering/FILDZ_CYBEROS/wiki)

## Contributing

FILDZ CYBEROS is an open-source project that thrives on community contributions. We welcome developers to contribute to the project by following the MIT license guidelines. Feel free to submit pull requests, report issues, or suggest enhancements to help us improve the project further.

## Acknowledgment 

We are immensely thankful to the [MicroPython](https://github.com/micropython/micropython) community for developing and maintaining this incredible open-source project. Their dedication and hard work have provided us with a powerful and versatile platform to build upon.
