from pyblackbird import get_blackbird
#from pyblackbird.devices import SerialBlackbird

#serial = SerialBlackbird('/home/localadmin/dev/ttyV0')
host = '172.30.1.7'

blackbird = get_blackbird(host)

zone_status = blackbird.zone_status(1)


print('Zone Number = {}'.format(zone_status.zone))
print('AV Source = {}'.format(zone_status.av))
print('IR Source = {}'.format(zone_status.ir))
print('Zone Power is {}'.format('On' if zone_status.power else 'Off'))