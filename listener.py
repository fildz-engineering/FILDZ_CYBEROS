# The MIT License (MIT)
# Copyright (c) 2023 Edgaras Janušauskas and Inovatorius MB (www.fildz.com)

################################################################################
# FILDZ CYBEROS EVENT LISTENER
#
# ESP-NOW event listener and firing of events or generators.

import uasyncio as asyncio
from uasyncio import Event
import fildz_cyberos as cyberos
import ustruct as struct


class Listener:
    def __init__(self):
        self._on_event = Event()
        asyncio.create_task(self._event())
        self._sender_mac = None  # Event sender MAC address (e.g., b'\x9e\x9c\x1f\x00\x00\x00')
        self._name = None  # Event name (e.g., on_pair, on_ping)
        self._args = list()  # Event arguments (e.g., (0, 0, 'Hello World!'))
        self._sender = None  # Event sender name (e.g., BUTTON-02AD9A-WAY)
        self._receiver = None  # Event receiver name (e.g., DISPLAY-0F889A-ABW)

    ################################################################################
    # Properties
    #
    @property
    def sender_mac(self):
        return self._sender_mac

    @property
    def sender(self):
        return self._sender

    @property
    def receiver(self):
        return self._receiver

    @property
    def name(self):
        return self._name

    @property
    def args(self):
        return self._args

    ################################################################################
    # Events
    #
    @property
    def on_event(self):
        return self._on_event

    ################################################################################
    # Tasks
    #
    # New event received.
    async def _event(self):
        async for sender, event in cyberos.espnow:
            self._sender_mac = sender
            try:
                self._sender, self._receiver, self._name, self._args = self.decode(event)
            except:
                continue

            # print('\nFROM:', self._sender)
            # print('TO:', self._receiver)
            # print('EVENT:', self._name)
            # print('ARGS:', self._args)

            self._on_event.set()  # We have a new event, inform tasks.

            # To whom event was sent?
            if self._receiver is '':
                # Event was sent to all cyberwares, so it is a public event.
                # Public events are sent to AP MAC address on default channel.
                if self._name in cyberos.cyberwares[cyberos.cyberware.ap_name]['events']:
                    if not cyberos.cyberwares[cyberos.cyberware.ap_name]['events'][self._name].is_set():
                        # print('\nPUBLIC {} EVENT'.format(self._name))
                        cyberos.cyberwares[cyberos.cyberware.ap_name]['events'][self._name].set()
            elif self._receiver == cyberos.cyberware.ap_name:
                # Event was sent to our cyberware, so it is a private event.
                # Private events are sent to STA MAC address on random channel (channel depends on cyberware config).
                # The event we received can be from unpaired, in-pairing, or paired cyberware.
                # Is the event received is from the paired or unpaired cyberware?
                if self._sender in cyberos.cyberwares['subscribed']:
                    # Received an event from either paired-subscribed or unpaired-subscribed cyberware.
                    # If we have a mac address of the event sender, then we are paired with it.
                    if 'mac' in cyberos.cyberwares['subscribed'][self._sender]:
                        # We are paired with the event sender, but are we subscribed to its events?
                        if self._name in cyberos.cyberwares['subscribed'][self._sender]['events']:
                            # print('\nPAIRED {} {} SUBSCRIBED EVENT'.format(self._sender, self._name))
                            # Indeed we are subscribed to paired cyberware events.
                            # Now should we set the event or run a function?
                            if cyberos.cyberwares['subscribed'][self._sender] \
                                    ['events'][self._name].__class__.__name__ is 'Event':
                                if not cyberos.cyberwares['subscribed'][self._sender]['events'][self._name].is_set():
                                    cyberos.cyberwares['subscribed'][self._sender]['events'][self._name].set()
                            elif cyberos.cyberwares['subscribed'][self._sender]['events'][
                                self._name].__class__.__name__ is 'generator':
                                await cyberos.cyberwares['subscribed'][self._sender]['events'][self._name]()
                        # else:
                        # We do not listen to paired cyberware events.
                        # print('\nPAIRED {} {} UNSUBSCRIBED EVENT'.format(self._sender, self._name))
                    # else:
                    # Event from unpaired device, but we are subscribed to its events.
                    # We do not execute any events from unpaired cyberware except for public events.
                    # print('\nUNPAIRED {} {} SUBSCRIBED EVENT'.format(self._sender, self._name))
                else:
                    # Received an event from 'unpaired' or 'in-pairing' cyberware.
                    # We do not execute any events from 'unpaired' cyberware except if it is a public event
                    # like 'on_pairing' that is only available in 'in-pairing' cyberware.
                    # 'in-pairing' cyberware is a cyberware that is answering our pairing (on_pairing event) request.
                    if self._name in cyberos.cyberwares[cyberos.cyberware.ap_name]['events']:
                        if not cyberos.cyberwares[cyberos.cyberware.ap_name]['events'][self._name].is_set():
                            # print('\nCYBEROS {} EVENT'.format(self._name))
                            cyberos.cyberwares[cyberos.cyberware.ap_name]['events'][self._name].set()
                    # else:
                    # print('\nUNPAIRED {} {} UNSUBSCRIBED EVENT'.format(self._sender, self._name))
            # Event was sent to some other cyberware, resend it to all.
            # else:
            # print('\nRetransmitting...')
            self._on_event.clear()

    async def encode(self, event_name, args, cyberware=''):
        a_len = len(cyberos.cyberware.ap_name)
        c_len = len(cyberware)
        e_len = len(event_name)

        n = len(args)
        for arg in args:
            n += len(arg)
        offset = 1 + a_len + 1 + c_len + 1 + e_len
        n += offset
        data = bytearray(n)
        buffer = memoryview(data)
        struct.pack_into('b%isb%isb%is' % (a_len, c_len, e_len), buffer, 0,
                         a_len, cyberos.cyberware.ap_name,
                         c_len, cyberware,
                         e_len, event_name)
        for arg in args:
            arg_len = len(arg)
            struct.pack_into('b%is' % arg_len, buffer, offset, arg_len, arg)
            offset += 1 + arg_len
        return buffer

    async def decode(self, event):
        size = len(event)
        event = memoryview(event)
        offset = 0
        args = list()

        # Event sender, receiver, name.
        for x in range(3):
            arg_size = event[offset:offset + 1][0]
            arg = event[offset + 1:offset + 1 + arg_size]
            arg = str(arg, 'utf8')
            offset += 1 + len(arg)
            yield arg

        # Event args.
        while True:
            arg_size = event[offset:offset + 1][0]
            arg = event[offset + 1:offset + 1 + arg_size]
            arg = str(arg, 'utf8')
            offset += 1 + len(arg)
            args.append(arg)
            if offset >= size:
                yield args
                break

    async def send(self, event_name, *args, cyberware='', sync=True):
        if cyberware is '':
            for cyberware in cyberos.cyberwares['subscribed']:
                _event = await self.encode(event_name, '' if not len(args) else args, cyberware=cyberware)
                await cyberos.espnow.asend(cyberos.cyberwares['subscribed'][cyberware]['mac'], _event, sync=sync)
        else:
            _event = await self.encode(event_name, '' if not len(args) else args, cyberware=cyberware)
            await cyberos.espnow.asend(cyberos.cyberwares['subscribed'][cyberware]['mac'], _event, sync=sync)

    async def push(self, cyberware_name, event_name, event):
        if cyberware_name in cyberos.cyberwares['subscribed']:
            cyberos.cyberwares['subscribed'][cyberware_name]['events'].update({event_name: event})
        else:
            cyberos.cyberwares['subscribed'].update({cyberware_name: {'events': {event_name: event}}})

    async def pull(self, cyberware_name, event_name=''):
        if event_name is '':
            cyberos.cyberwares['subscribed'][cyberware_name]['events'].clear()
        else:
            cyberos.cyberwares['subscribed'][cyberware_name]['events'].pop(event_name)
