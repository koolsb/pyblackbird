## Status
[![Build Status](https://travis-ci.org/koolsb/pyblackbird.svg?branch=master)](https://travis-ci.org/koolsb/pyblackbird)[![Coverage Status](https://coveralls.io/repos/github/koolsb/pyblackbird/badge.svg)](https://coveralls.io/github/koolsb/pyblackbird)
# pyblackbird
Python3 interface implementation for Monoprice Blackbird HDMI Matrix Switches

## Notes
This is for use with [Home-Assistant](http://home-assistant.io)
Has been tested with models 21819 and 24180

## Usage
```python
from pyblackbird import get_blackbird

# Connect via serial port
blackbird = get_blackbird('/dev/ttyUSB0')

# Connect via serial port with a device that doesn't support IR control
blackbird = get_blackbird('/dev/ttyUSB0', use_serial=True, ir_control=false)

# Connect via IP
blackbird = get_blackbird('192.168.1.50', use_serial=False)

# Connect via IP with a device that doesn't support IR control
blackbird = get_blackbird('192.168.1.50', use_serial=False, ir_control=false)

# Print system lock status
print('System Lock is {}'.format('On' if blackbird.lock_status() else 'Off'))

# Valid zones are 1-8
zone_status = blackbird.zone_status(1)

# Print zone status
print('Zone Number = {}'.format(zone_status.zone))
print('Zone Power is {}'.format('On' if zone_status.power else 'Off'))
print('AV Source = {}'.format(zone_status.av))
print('IR Source = {}'.format(zone_status.ir))

# Turn off zone #1
blackbird.set_power(1, False)

# Set source 5 for zone #1
blackbird.set_zone_source(1, 5)

# Set all zones to source 2
blackbird.set_all_zone_source(2)

# Lock system buttons
blackbird.lock_front_buttons()

# Unlock system buttons
blackbird.unlock_front_buttons()

```
