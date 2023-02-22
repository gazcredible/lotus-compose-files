import datetime

import local_environment_settings
import os
import unexeaqua3s.json
import inspect

import unexefiware.fiwarewrapper
import unexefiware.fiwarewrapper_debug
import unexefiware.base_logger
import unexefiware.time

import unexeaqua3s.deviceinfo
import unexeaqua3s.visualiser
import unexeaqua3s.device_simulation
import unexeaqua3s.pilot_timezone
import testbed_pilot


import requests
import testbed_epanomalies

def testbed_devices(fiware_service):
    quitApp = False

    logger = unexefiware.base_logger.BaseLogger()

    epanomalies = unexeaqua3s.epanomalies.EPAnomalies(fiware_service)
    epanomalies.load_data()

    entity_id = 'urn:ngsi-ld:Device:UNEXE_TEST_2'
    device_id = 'urn:ngsi-ld:Device:UNEXE_TEST_32'

    while quitApp is False:
        print('\n')
        print('Devices')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])

        print('\n')
        print('1..View Devices')
        print('2..Create Devices')
        print('3..Update Devices')
        print('4..Lerp anomaly values')
        print('5..epanomaly: ' +device_id)
        print('6..rebuild anomaly settings')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            #read all the devices ...
            result = unexefiware.ngsildv1.get_all_orion(requests.session(), os.environ['DEVICE_BROKER'], 'Device', link='https://smartdatamodels.org/context.jsonld', fiware_service=fiware_service)

            if result[0] == 200:
                for entry in result[1]:
                    try:
                        if 'controlledProperty' in entry:
                            value = entry['controlledProperty']['value']
                            if isinstance(value, list):
                                for prop in value:
                                    print(entry['id'] + ' ' + prop + ' ' + entry[prop]['observedAt'] + ' ' + str(entry['location']))
                            else:
                                print(entry['id'] + ' ' + entry[value]['observedAt'] + ' ' + str(entry['location']))
                        else:
                            print(entry['id'] + ' ' + entry['value']['observedAt'] + ' ' + str(entry['location']))
                    except Exception as e:
                        logger.exception(inspect.currentframe(),e)
            else:
                print(result)

        if key == '2':
            pass

        if key == '3':
            fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.now(unexeaqua3s.pilot_timezone.get(fiware_service)))

            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service=fiware_service)
            deviceInfo.logger = logger
            deviceInfo.run()

            for device_id in deviceInfo.deviceModelList:
                device = deviceInfo.deviceModelList[device_id]

                state = 'normal'

                #if device_id == 'urn:ngsi-ld:Device:UNEXE_TEST_103':
                #    state = 'Anomaly'

                #if device_id == 'urn:ngsi-ld:Device:UNEXE_TEST_2':
                #    print()

                unexeaqua3s.device_simulation.create_device_data(fiware_service, device, state, fiware_time, epanomalies)

            unexeaqua3s.workhorse_backend.pilot_update(fiware_service, logger)
            unexeaqua3s.visualiser.pilot_device_update(fiware_service)


        if key == '4':

            fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])

            result = fiware_wrapper.get_entity(entity_id=entity_id, service=fiware_service)

            if type(result) is dict:
                model = unexeaqua3s.deviceinfo.DeviceSmartModel(result)
                date = datetime.datetime(year=2017, month=1, day=1, hour=0, minute=0)

                for hour in range(0,14*24*6):
                    fiware_time = unexefiware.time.datetime_to_fiware(date)
                    result = model.get_anomaly_raw_values(fiware_time, lerp = True)

                    date += datetime.timedelta(minutes=10)

        if key == '5':
            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service=fiware_service)
            deviceInfo.logger = logger
            deviceInfo.run()

            state = 'epanomaly'
            device = deviceInfo.get_smart_model(device_id)
            fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.now(unexeaqua3s.pilot_timezone.get(fiware_service)))

            unexeaqua3s.device_simulation.create_device_data(fiware_service, device, state, fiware_time, epanomalies)

            unexeaqua3s.workhorse_backend.pilot_update(fiware_service, logger)
            unexeaqua3s.visualiser.pilot_device_update(fiware_service)

        if key =='6':
            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service=fiware_service)
            deviceInfo.logger = logger
            deviceInfo.run()

            for device_id in deviceInfo.deviceModelList:
                device = deviceInfo.deviceModelList[device_id]

                print(device.get_id().ljust(45,' ') + ' ' + str(device._observedAt_prettyprint()) )

                device.anomalysetting_initialise(fiware_service, do_patch=True)


        if key == 'x':
            quitApp = True


def testbed(fiware_service):
    quitApp = False

    logger = unexefiware.base_logger.BaseLogger()

    while quitApp is False:
        print('\n')
        print('Testbed devices')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])

        print('\n')
        print('1..Devices')
        print('2..EPAnomalies')
        print('3..EYA Testbed')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            testbed_devices(fiware_service)

        if key == '2':
            testbed_epanomalies.testbed(fiware_service)

        if key == '3':
            testbed_pilot.eya_testbed(fiware_service='EYA')

        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    logger = unexefiware.base_logger.BaseLogger()

    fiware_service = 'AAA'

    testbed(fiware_service)
