from pyblackbird import get_blackbird

blackbird = get_blackbird('/home/localadmin/dev/ttyV0')
# Valid zones are 11-16 for main monoprice amplifier
zone_status = blackbird.zone_status(1)
system_power_status = blackbird.system_power_status()
#blackbird.set_system_power(4)
#blackbird.set_source(2,2)
#blackbird.set_zone_power(1,1)

# Print system power status
print('System Power = {}'.format(system_power_status))

# Print zone status
print('Zone Number = {}'.format(zone_status.zone))
print('AV Source = {}'.format(zone_status.av))
print('IR Source = {}'.format(zone_status.ir))
print('Zone Power is {}'.format('On' if zone_status.power else 'Off'))
#print('Mute is {}'.format('On' if zone_status.mute else 'Off'))
#print('Public Anouncement Mode is {}'.format('On' if zone_status.pa else 'Off'))
#print('Do Not Disturb Mode is {}'.format('On' if zone_status.do_not_disturb else 'Off'))
#print('Volume = {}'.format(zone_status.volume))
#print('Treble = {}'.format(zone_status.treble))
#print('Bass = {}'.format(zone_status.bass))
#print('Balance = {}'.format(zone_status.balance))
#print('Source = {}'.format(zone_status.source))
#print('Keypad is {}'.format('connected' if zone_status.keypad else 'disconnected'))

# Turn off zone #11
#monoprice.set_power(11, False)

# Mute zone #12
#monoprice.set_mute(12, True)

# Set volume for zone #13
#monoprice.set_volume(13, 15)

# Set source 1 for zone #14 
#monoprice.set_source(14, 1)

# Set treble for zone #15
#monoprice.set_treble(15, 10)

# Set bass for zone #16
#monoprice.set_bass(16, 7)

# Set balance for zone #11
#monoprice.set_balance(11, 3)

# Restore zone #11 to it's original state
#monoprice.restore_zone(zone_status)
