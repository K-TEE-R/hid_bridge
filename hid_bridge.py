#!/usr/bin/python
#coding: utf-8
import device_config
import evdev
import keymap
import threading
import time
import traceback
import signal
import sys

VERBOSE = False
MOUSE_REPORT_ID = 1
KEYBOARD_REPORT_ID = 2
USBHID_GADGET_PATH = '/dev/hidg0'

def monitor_device(hidg_dev):
    event_handlers = {}
    processed_devices = []
    while True:
        time.sleep(1)
        device_list = evdev.list_devices()
        for pdev in processed_devices:
            if pdev in device_list:
                device_list.remove(pdev)
        if len(device_list) > 0:
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
            if device.name in device_config.ALLOWED_MOUSE_DEVS:
                print('Mouse device: {} is found on {}.'.format(device.name, device.path))
                print('Device capabilities: {}'.format(device.capabilities(verbose=True)))
                target_device = evdev.InputDevice(device.fn)
                thread = threading.Thread(target=handle_mouse_event, args=(hidg_dev, target_device,))
                event_handlers[device.path] = (device.name, thread, 'mouse')
                thread.start()
            elif device.name in device_config.ALLOWED_KEYBOARD_DEVS:
                print('Keyboard device: {} is found on {}.'.format(device.name, device.path))
                print('Device capabilities: {}'.format(device.capabilities(verbose=True)))
                target_device = evdev.InputDevice(device.fn)
                thread = threading.Thread(target=handle_keyboard_event, args=(hidg_dev, target_device,))
                event_handlers[device.path] = (device.name, thread, 'keyboard')
                thread.start()
            processed_devices.append(device.path)

def handle_mouse_event(hidg_dev, input_ev_dev):
    button = 0
    while True:
        try:
            for event in input_ev_dev.read_loop():
                if VERBOSE:
                    print('{} got event: type={}, code={}, value={}'.format(input_ev_dev.name, event.type, event.code, event.value))
                if event.type == evdev.ecodes.EV_REL:
                    if event.code == evdev.ecodes.REL_X:
                        if event.value >= 0:
                            barray = bytearray([MOUSE_REPORT_ID, button, event.value, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                        else:
                            barray = bytearray([MOUSE_REPORT_ID, button, 0xff + event.value, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                    if event.code == evdev.ecodes.REL_Y:
                        if event.value >= 0:
                            barray = bytearray([MOUSE_REPORT_ID, button, 0, event.value, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                        else:
                            barray = bytearray([MOUSE_REPORT_ID, button, 0, 0xff + event.value, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                    if event.code == evdev.ecodes.REL_WHEEL:
                        if event.value >= 0:
                            barray = bytearray([MOUSE_REPORT_ID, button, 0, 0, event.value])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                        else:
                            barray = bytearray([MOUSE_REPORT_ID, button, 0, 0, 0xff + event.value])
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
                            barray = bytearray([MOUSE_REPORT_ID, button, 0, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                        elif event.code == evdev.ecodes.BTN_RIGHT:
                            if event.value == 1:
                                button = 2
                            else:
                                button = 0
                            barray = bytearray([MOUSE_REPORT_ID, button, 0, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
                        elif event.code == evdev.ecodes.BTN_MIDDLE:
                            if event.value == 1:
                                button = 4
                            else:
                                button = 0
                            barray = bytearray([MOUSE_REPORT_ID, button, 0, 0, 0])
                            hidg_dev.write(barray)
                            hidg_dev.flush()
        except Exception as e:
            print(traceback.format_exc())
            time.sleep(5)

def handle_keyboard_event(hidg_dev, input_ev_dev):
    modkey = [0, 0, 0, 0, 0, 0, 0, 0]
    while True:
        try:
            for event in input_ev_dev.read_loop():
                if VERBOSE:
                    print('{} got event: type={}, code={}, value={}'.format(input_ev_dev.name, event.type, event.code, event.value))
                if event.type == evdev.ecodes.EV_KEY:
                    if event.value != 2:
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

                        barray = bytearray([KEYBOARD_REPORT_ID, modbyte, 0, keymap.keytable[evdev_code], 0, 0, 0, 0, 0])
                        hidg_dev.write(barray)
                        hidg_dev.flush()
        except Exception as e:
            print(traceback.format_exc())
            time.sleep(5)

#########################
## Main implementation ##
#########################
if __name__ == '__main__':
    try:
        while True:
            hidg_dev = open(USBHID_GADGET_PATH, mode='wb')
            if hidg_dev != None:
                print('Found {}'.format(USBHID_GADGET_PATH))
                break
            print('Waiting for {}'.format(USBHID_GADGET_PATH))

        root_thread = threading.Thread(target=monitor_device, args=(hidg_dev,))
        root_thread.start()
        root_thread.join()
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        if hidg_dev != None:
            hidg_dev.close()
            hidg_dev = None
        sys.exit(0)
