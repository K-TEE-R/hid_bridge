#!/usr/bin/python
#coding: utf-8
import device_config
import evdev
import keymap
import threading
import time
import signal
import sys

def monitor_device():
    event_handlers = {}
    processed_devices = []
    while True:
        time.sleep(1)
        device_list = evdev.list_devices()
        for pdev in processed_devices:
            if pdev in device_list:
                device_list.remove(pdev)
        print('device_list = {}'.format(device_list))
        if len(device_list) == 0:
            continue
        devices = [evdev.InputDevice(fn) for fn in device_list]
        if len(devices) == 0:
            print('No input devices are found. Waiting for next detection')
            time.sleep(1)
            continue
        for device in devices:
            print('Searching new device')
            if device.path in processed_devices:
                continue
            print('Found new device{}'.format(device))
            if device.name in device_config.ALLOWED_DEVICE_NAMES:
                print('HID device {} is found on {}.'.format(device.name, device.path))
                print('Device capabilities: {}'.format(device.capabilities(verbose=True)))
                target_device = evdev.InputDevice(device.fn)
                thread = threading.Thread(target=handle_input_event, args=(target_device,))
                event_handlers[device.path] = (device.name, thread)
                thread.start()
            processed_devices.append(device.path)

def handle_input_event(target_device):
    button = 0
    modkey = [0, 0, 0, 0, 0, 0, 0, 0]

    try:
        while True:
            for event in target_device.read_loop():
                print('{} got event: type={}, code={}, value={}'.format(target_device.name, event.type, event.code, event.value))
                if event.type == evdev.ecodes.EV_REL:
                    if event.code == evdev.ecodes.REL_X:
                        if event.value >= 0:
                            barray = bytearray([button, event.value, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                        else:
                            barray = bytearray([button, 0xff + event.value, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                    if event.code == evdev.ecodes.REL_Y:
                        if event.value >= 0:
                            barray = bytearray([button, 0, event.value, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                        else:
                            barray = bytearray([button, 0, 0xff + event.value, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                    if event.code == evdev.ecodes.REL_WHEEL:
                        if event.value >= 0:
                            barray = bytearray([button, 0, 0, event.value, 0, 0, 0, 0, 0, 0, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                        else:
                            barray = bytearray([button, 0, 0, 0xff + event.value, 0, 0, 0, 0, 0, 0, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                elif event.type == evdev.ecodes.EV_KEY:
                    if event.value != 2:
                        key = 0
                        if event.code == evdev.ecodes.BTN_LEFT:
                            if event.value == 1:
                                button = 1
                            else:
                                button = 0
                            barray = bytearray([button, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                        elif event.code == evdev.ecodes.BTN_RIGHT:
                            if event.value == 1:
                                button = 2
                            else:
                                button = 0
                            barray = bytearray([button, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                        elif event.code == evdev.ecodes.BTN_MIDDLE:
                            if event.value == 1:
                                button = 4
                            else:
                                button = 0
                            barray = bytearray([button, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                        elif event.code < 256:
                            key = event.code
                            evdev_code = evdev.ecodes.KEY[key]
                            modkey_element = keymap.modkey(evdev_code)

                            if modkey_element > 0:
                                if event.value == 1:
                                    modkey[modkey_element] = 1
                                else:
                                    modkey[modkey_element] = 0

                            bit_pattern = ''
                            for bit in modkey:
                                bit_pattern += str(bit)

                            modbyte = int(bit_pattern, 2)

                            if event.value == 0:
                               key = 0
                            else:
                               key = event.code

                            evdev_code = evdev.ecodes.KEY[key]
                            modkey_element = keymap.modkey(evdev_code)

                            if event.value == 0:
                                key = 0
                            else:
                                key = event.code

                            barray = bytearray([button, 0, 0, 0, modbyte, 0, keymap.keytable[evdev_code], 0, 0, 0, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
    except:
        print(type(e))
        if hidg_dev != None:
            hidg_dev.close()
        sys.exit(0)

#########################
## Main implementation ##
#########################
if __name__ == '__main__':
    # Wait for HID gadget driver initialization.
    try:
        while True:
            hidg_dev = open('/dev/hidg0', mode='wb')
            if hidg_dev != None:
                print('Found HID gadget device')
                break
            print('Waiting for HID gadget device')
            time.sleep(1)
        root_thread = threading.Thread(target=monitor_device)
        root_thread.start()
        root_thread.join()
    except Exception as e:
        print(type(e))
        if hidg_dev != None:
            hidg_dev.close()
        sys.exit(0)
