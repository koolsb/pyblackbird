## Status
[![Tests](https://github.com/koolsb/pyblackbird/actions/workflows/test.yml/badge.svg)](https://github.com/koolsb/pyblackbird/actions/workflows/test.yml)
# pyblackbird
Python3 interface implementation for Monoprice Blackbird HDMI matrix switches

## Notes
This is for use with [Home-Assistant](http://home-assistant.io)

Tested with models [21819](https://www.monoprice.com/product?p_id=21819)
(4K 8x8 HDBaseT) and [24180](https://www.monoprice.com/product?p_id=24180).

Models without IR routing, such as the 24180, use a different command to
select a source and report a shorter zone status. Pass `ir_control=False`
for those; the default suits the 21819.

## Usage
```python
from pyblackbird import get_blackbird

# Connect via serial port
blackbird = get_blackbird('/dev/ttyUSB0')

# Connect via IP
blackbird = get_blackbird('192.168.1.50', use_serial=False)

# Connect to a model without IR control, i.e. the 24180
blackbird = get_blackbird('/dev/ttyUSB0', ir_control=False)
blackbird = get_blackbird('192.168.1.50', use_serial=False, ir_control=False)

# Print system lock status
print('System Lock is {}'.format('On' if blackbird.lock_status() else 'Off'))

# Valid zones are 1-8
zone_status = blackbird.zone_status(1)

# Print zone status
print('Zone Number = {}'.format(zone_status.zone))
print('Zone Power is {}'.format('On' if zone_status.power else 'Off'))
print('AV Source = {}'.format(zone_status.av))
print('IR Source = {}'.format(zone_status.ir))  # None without IR control

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
