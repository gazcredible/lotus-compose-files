import local_environment_settings
import os

import unexeaqua3s.brokerdefinition
import unexeaqua3s.kibanablelog
import unexefiware.fiwarewrapper
from unexeaqua3s import support


def testbed():
    quitApp = False

    logger = unexeaqua3s.kibanablelog.KibanableLog('3D_Visualisation')

    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    fiware_wrapper.init(logger=logger)
    fiware_service = os.environ['PILOTS']

    device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    alert_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['ALERT_BROKER'], historic_url=os.environ['ALERT_HISTORIC_BROKER'])
    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)

    while quitApp is False:
        while quitApp is False:
            print()
            print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])
            print('ALERT_BROKER:  ' + os.environ['ALERT_BROKER'])
            print('WORKHOUSE_BROKER:  ' + os.environ['WORKHOUSE_BROKER'])

            deviceInfo.run()
            support.print_devices(deviceInfo)

            print()
            print('1..Process Data + Kick Visualise')
            print('X..Quit')
            print()

            key = input('>')

            if key == '1':
                support.do_all_processing(fiware_service)
                support.on_normaldevice_update(fiware_service)
                support.do_charting(fiware_service)

            if key == 'x':
                quitApp = True

if __name__ == '__main__':
    testbed()


