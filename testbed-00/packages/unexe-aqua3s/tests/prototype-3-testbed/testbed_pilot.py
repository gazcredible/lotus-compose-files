import os
import unexefiware.ngsildv1
import requests

import unexeaqua3s.deviceinfo
import unexeaqua3s.workhorse_backend

def eya_testbed(fiware_service='EYA'):
    quitApp = False

    logger = unexefiware.base_logger.BaseLogger()

    while quitApp is False:
        print('\n')
        print('Testbed devices')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])

        print('\n')
        print('1..View Devices')
        print('2..Setup alerts')
        print('3..Setup anomalies')
        print('4..Setup epanomalies')
        print('5..Setup charting')


        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':

            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service=fiware_service)
            deviceInfo.run()

            for device_id in deviceInfo.deviceInfoList:
                device = deviceInfo.get_smart_model(device_id)

                print(device_id)

        if key == '2':

            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service=fiware_service)
            deviceInfo.run()

            for device_id in deviceInfo.deviceInfoList:
                device = deviceInfo.get_smart_model(device_id)

                device.alertsetting_initialise(fiware_service)
                device.alertstatus_initialise(fiware_service)

        if key == '3':

            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service=fiware_service)
            deviceInfo.run()

            for device_id in deviceInfo.deviceInfoList:
                device = deviceInfo.get_smart_model(device_id)

                device.anomalysetting_initialise(fiware_service)
                device.anomalystatus_initialise(fiware_service)


        if key == '4':

            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service=fiware_service)
            deviceInfo.run()

            for device_id in deviceInfo.deviceInfoList:
                device = deviceInfo.get_smart_model(device_id)

                device.model['epanet_reference']['value'] = str(-1)

                device._patch(fiware_service,'epanet_reference')

        if key == '5':
            pilot_processor = unexeaqua3s.workhorse_backend.PilotProcessor(debug=True, do_automatic_updates=False)
            pilot_processor.init(fiware_service=fiware_service)

            pilot_processor.update_charting(data = {'force_interday':'true'})

        if key == 'x':
            quitApp = True
