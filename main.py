import _thread
import machine
import pycom
import utime
import gc
import sys

from lib import tools, tsl2561, wifi
from lib.smartthings_handler import Smartthings


def read_lux(smartthings_handler):
    previous_lux = -1000
    try:
        light_sensor = tsl2561.TSL2561()
    except Exception as e:
        tools.led_error()
        print("{} - main.read_lux - Enable to load TSL2561 Module, Exception: '{}'".format(tools.datetime_to_iso(utime.localtime()), e))
        sys.print_exception(e)
        sys.exit(1)

    while True:
        try:
            lux = light_sensor.get_lux()
        except Exception as e:
            print("{} - main.read_lux - Failed to get luminosity. Exception: '{}'".format(tools.datetime_to_iso(utime.localtime()), e))
            sys.print_exception(e)
            tools.led_error(0xFFFF00)
        else:
            if lux <= 80:
                if abs(lux - previous_lux) > 15:
                    body = {'lux': lux}
                    smartthings_handler.notify(body)
                    previous_lux = lux
                elif lux == 0 and lux != previous_lux:
                    body = {'lux': lux}
                    smartthings_handler.notify(body)
                    previous_lux = lux
            elif 80 < lux <= 700:
                if abs(lux - previous_lux) > 10:
                    body = {'lux': lux}
                    smartthings_handler.notify(body)
                    previous_lux = lux
            elif 700 < lux <= 1000:
                # report if variance is more than 5%
                previous_lux = previous_lux if previous_lux else 0.01
                if 100*abs((lux - previous_lux)/previous_lux) > 5:
                    body = {'lux': lux}
                    smartthings_handler.notify(body)
                    previous_lux = lux
            elif 1000 < lux <= 1500:
                # report if variance is more than 20%
                previous_lux = previous_lux if previous_lux else 0.01
                if 100*abs((lux - previous_lux)/previous_lux) > 20:
                    body = {'lux': lux}
                    smartthings_handler.notify(body)
                    previous_lux = lux
            elif 1500 < lux:
                # report if variance is more than 25%
                previous_lux = previous_lux if previous_lux else 0.01
                if 100*abs((lux - previous_lux)/previous_lux) > 25:
                    body = {'lux': lux}
                    smartthings_handler.notify(body)
                    previous_lux = lux
        finally:
            gc.collect()
            utime.sleep(5)


def ping_st(smartthings_handler, check_interval=300):
    while True:
        initialize_rtc()
        body = {'check_in_at': tools.datetime_to_iso(utime.gmtime(), "Z")}
        smartthings_handler.notify(body)
        gc.collect()
        utime.sleep(check_interval)


def initialize_rtc():
    rtc = machine.RTC()
    rtc.ntp_sync("pool.ntp.org")
    utime.sleep(5)
    if (3, 1, 2, 0, 0) <= rtc.now() < (11, 1, 2, 0, 0):
        tz_offset = -4*3600
    else:
        tz_offset = -5*3600

    if utime.timezone() != tz_offset:
        utime.timezone(tz_offset)

    gc.collect()
    utime.sleep(1)


##### START MAIN APP
try:
    # pycom.heartbeat(False)

    #  CONNECTO TO WIFI
    while not wifi.wifi_connect():
        tools.led_error(0x190077)
        utime.sleep(3)
        #connected = wifi.wifi_connect()

    #  TURN OFF LED
    tools.led_error(0x0)

    #  INITIALIZE RTC
    initialize_rtc()
    print("DateTime(LocalTime): {}".format(tools.datetime_to_iso(utime.localtime())))

    #  START MAIN LOOPS
    print("Starting Main loops")
    _thread.start_new_thread(read_lux, (Smartthings(retry_num=5, retry_sec=1),))
    _thread.start_new_thread(ping_st, (Smartthings(retry_num=3, retry_sec=2),))

except Exception as e:
    print(e)
    sys.print_exception(e)
finally:
    gc.collect()
