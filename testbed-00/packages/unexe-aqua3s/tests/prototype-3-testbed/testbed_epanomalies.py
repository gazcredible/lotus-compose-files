import datetime
import os
import unexeaqua3s.json
import inspect
import copy

import unexefiware.fiwarewrapper
import unexefiware.fiwarewrapper_debug
import unexefiware.base_logger
import unexefiware.time

import unexeaqua3s.deviceinfo
import unexeaqua3s.visualiser
import unexeaqua3s.service_anomaly
import unexeaqua3s.epanomalies

def testbed(fiware_service):
    quitApp = False

    device_id = 'urn:ngsi-ld:Device:UNEXE_TEST_2'

    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service)


    logger = unexefiware.base_logger.BaseLogger()

    epanomalies = unexeaqua3s.epanomalies.EPAnomalies(fiware_service)
    epanomalies.load_data()

    while quitApp is False:

        deviceInfo.run()

        print('\n')
        print('EPAnomaly devices')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])

        print('\n')
        print('1..Run process on device:' + device_id)
        print('2..Run process on pilot:' + fiware_service)

        print('11..Build anomaly data for epanet devices:' + fiware_service)

        print('99..Update Visualiser:' + fiware_service)


        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            epanomalies.process_device(fiware_service, deviceInfo.get_model_from_fiware(device_id))

        if key == '2':
            for label in deviceInfo.deviceInfoList:
                device = deviceInfo.deviceModelList[label]

                epanomalies.process_device(deviceInfo, device)

        if key == '11':
            #go through all the epanet devices and build anomaly data from the avg_values_DB
            epanomalies.build_anomaly_settings(fiware_service)

        if key == '99':
            unexeaqua3s.visualiser.pilot_device_update(fiware_service)

        if key == 'x':
            quitApp = True


if __name__ == '__main__':
    logger = unexefiware.base_logger.BaseLogger()
    fiware_service = 'AAA'

    testbed(fiware_service)
