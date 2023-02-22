import unexefiware.base_logger

import local_environment_settings
import os

import requests
import unexeaqua3s.json
import unexeaqua3s.workhorse_backend
import unexefiware.fiwarewrapper

def testbed(fiware_service):
    quitApp = False

    #trieste_processor = unexeaqua3s.trieste_demo.TriesteDemo()
    #trieste_processor.init()

    workhouse = unexeaqua3s.workhouse_backend.WorkhorseBackend()
    workhouse.init(debug = True)

    while quitApp is False:
        print('\nWorkhouse Testbed')

        #SOF?
        test_device = 'urn:ngsi-ld:Device:UNEXE_TEST_LG-001'

        #AAA
        test_device = 'urn:ngsi-ld:Device:UNEXE_TEST_MIR'

        #SVK
        test_device = 'urn:ngsi-ld:Device:UNEXE_TEST_CCS51D-AA11AD+NC'

        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])
        print('ALERT_BROKER:  ' + os.environ['ALERT_BROKER'])
        print('WORKHOUSE:  ' + os.environ['WORKHOUSE_BROKER'])

        print('\n')
        print('1..pilot_update_device' + ' ' + fiware_service)
        print('2..Vis Server: pilot_update_device' + ' ' + fiware_service)
        print('3..mproc Server: pilot_update_device' + ' ' + fiware_service)
        print()
        print('4..LOCAL processing - device_update' + ' ' + fiware_service)
        print('5..LOCAL processing - build_sensors' + ' ' + fiware_service)
        print('6..LOCAL processing - update demo sensors (make new data)' + ' ' + fiware_service)
        print('7..device normal:'+ test_device)
        print('8..device offline:'+ test_device)
        print('9..device alert:'+ test_device)

        print('10..Update Visualisation:' + fiware_service)

        print('20..UNEXE Vis On:' + fiware_service)
        print('21..UNEXE Vis Off:' + fiware_service)

        print('31..Clone devices from Orion:' + fiware_service)
        print('32..Build anomaly settings:' + fiware_service)
        print('33..Test anomaly processing:' + fiware_service)
        print('34..device anomaly:' + test_device)

        print('35..Build alert settings:' + fiware_service)


        print('41..Build userlayer references from resources:' + fiware_service)
        print('42..Visualiser - reaload userlayers:' + fiware_service)

        print('51..Download Broker Data:' + 'http://52.50.143.202:8101' )

        # To do
        # 1. do unexeaqua3s.workhouse_backend.command_device_update (firware_service)
        # 1x. what about no alert_settings?
        # 1a.do unexeaqua3s.workhouse_backend.command_rebuild_anomaly_settings (firware_service)
        # 1b.do unexeaqua3s.workhouse_backend.command_build_userlayer_references (firware_service)
        # 1c.do unexeaqua3s.workhouse_backend.command_visualiser_update_userlayers (firware_service)

        # 2. get all the sites working
        # 3. make workhouse requests work, work out what we need and add them
        # 4. make a UI for doing stuff
        # 5.
        # 6.
        # 7.revisit Brett epanomalies (get from AAA data)
        # 8.see why broker is nuking on start-up
        # 9.profit

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            try:
                headers = {}
                headers['Content-Type'] = 'application/ld+json'
                headers['fiware-service'] = fiware_service
                session = requests.session()

                path = os.environ['WORKHOUSE_BROKER'] + '/pilot_device_update'
                payload = {}

                r = session.post(path, data=unexeaqua3s.json.dumps(payload), headers=headers, timeout=10)
                print(str(r))

            except Exception as e:
                print(str(e))

        if key == '2':
            try:
                headers = {}
                headers['Content-Type'] = 'application/ld+json'
                session = requests.session()

                path = 'http://0.0.0.0:8100' + '/pilot_device_update'
                payload = {'fiware_service': 'AAA'}

                r = session.post(path, data=unexeaqua3s.json.dumps(payload), headers=headers, timeout=10)
                print(str(r))

            except Exception as e:
                print(str(e))

        if key == '3':
            try:
                headers = {}
                headers['Content-Type'] = 'application/ld+json'
                session = requests.session()

                path = 'http://0.0.0.0:8103' + '/pilot_device_update'
                payload = {'fiware_service': 'AAA'}

                r = session.post(path, data=unexeaqua3s.json.dumps(payload), headers=headers, timeout=10)
                print(str(r))

            except Exception as e:
                print(str(e))

        if key == '4':
            workhouse.add_command(fiware_service,unexeaqua3s.workhouse_backend.command_device_update)

        if key == '5':
            workhouse.add_command(fiware_service,unexeaqua3s.workhouse_backend.command_create_demo_sensors)

        if key == '6':
            workhouse.add_command(fiware_service,unexeaqua3s.workhouse_backend.command_update_demo_sensors)

        if key == '7':
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_set_demo_sensor_status, {'device':test_device, 'status':unexeaqua3s.workhouse_backend.device_state_normal} )
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_update_demo_sensors)

        if key == '8':
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_set_demo_sensor_status, {'device':test_device, 'status':unexeaqua3s.workhouse_backend.device_state_offline} )
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_update_demo_sensors)

        if key == '9':
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_set_demo_sensor_status, {'device':test_device, 'status':unexeaqua3s.workhouse_backend.device_state_alert} )
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_update_demo_sensors)

        if key == '10':
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_update_visualisation)

        if key == '20':
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_unexevis_on)

        if key == '21':
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_unexevis_off)

        if key == '31':
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_clone_devices_from_orion)

        if key == '32':
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_rebuild_anomaly_settings)

        if key == '33':
            device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            alert_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['ALERT_BROKER'], historic_url=os.environ['ALERT_HISTORIC_BROKER'])

            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
            deviceInfo.logger = unexefiware.base_logger.BaseLogger()
            deviceInfo.run()

            key_list = list(deviceInfo.deviceInfoList.keys())

            for key in key_list:
                print(key +':' +str(deviceInfo.anomaly_isTriggered(key)) )

        if key == '34':
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_set_demo_sensor_status, {'device':test_device, 'status':unexeaqua3s.workhouse_backend.device_state_anomaly} )
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_update_demo_sensors)

        if key == '35':
            unexeaqua3s.workhouse_site.build_alertsettings_from_orion(fiware_service)

        if key == '41':
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_build_userlayer_references)

        if key == '42':
            workhouse.add_command(fiware_service, unexeaqua3s.workhouse_backend.command_visualiser_update_userlayers)

        if key == '51':
            pilots = os.environ['PILOTS'].split(',')

            for fiware_service in pilots:
                unexeaqua3s.workhouse_site.dump_demo_sensors_from_orion(fiware_service)

        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    testbed('SOF')

