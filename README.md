## Status

# pyblackbird
Python3 interface implementation for Monoprice Blackbird 4k 8x8 HDBaseT Matrix

## Notes
This is for use with [Home-Assistant](http://home-assistant.io)

## Usage
```python
from pyblackbird import get_blackbird

blackbird = get_blackbird('/dev/ttyUSB0')

# Print system power status
print('System Power is {}'.format(system_power_status))

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
blackbird.set_source(1, 5)
```
