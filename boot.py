# boot.py -- run on boot-up
import os
import machine
import pycom
from wifi import WIFI
import time
import tools

if machine.reset_cause() != machine.SOFT_RESET:
    WIFI()
    #initialize DateTime
    rtc = machine.RTC()
    rtc.ntp_sync("pool.ntp.org")
    pycom.heartbeat(False)
    time.sleep(5)
    print("DateTime(UTC): {}".format(tools.datetime_toIso(rtc.now())))
