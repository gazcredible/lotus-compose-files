import unexeaqua3s.service_anomaly

import unexefiware.fiwarewrapper
import unexefiware.fiwarewrapper_debug
import unexefiware.base_logger
import unexefiware.time

import unexeaqua3s.deviceinfo

import os

from unexeaqua3s import support


def testbed(fiware_wrapper, fiware_service):

    quitApp = False

    device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    alert_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['ALERT_BROKER'], historic_url=os.environ['ALERT_HISTORIC_BROKER'])
    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)

    while quitApp is False:
        deviceInfo.run()

        print('aqua3s:' + '\n')
        support.print_devices(deviceInfo)
        print('')

        print()
        print('1..Run Anomaly Process')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            # do anomaly process
            anomaly_service = unexeaqua3s.service_anomaly.AnomalyService()
            anomaly_service.update(deviceInfo)

        if key == 'x':
            quitApp = True
