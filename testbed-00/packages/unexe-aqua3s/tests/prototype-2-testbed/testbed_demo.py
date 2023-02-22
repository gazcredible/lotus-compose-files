import os

import unexeaqua3s.brokerdefinition
import unexeaqua3s.kibanablelog
import unexefiware.fiwarewrapper
from unexeaqua3s import support
import backlogbuilder


def testbed():
    quitApp = False

    logger = unexeaqua3s.kibanablelog.KibanableLog('3D_Visualisation')

    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    fiware_wrapper.init(logger=logger)
    fiware_service = os.environ['PILOTS']

    device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    alert_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['ALERT_BROKER'], historic_url=os.environ['ALERT_HISTORIC_BROKER'])
    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
    deviceInfo.run()

    support.print_devices(deviceInfo)

    epa_anomaly_list = ['urn:ngsi-ld:Device:UNEXE_TEST_97','urn:ngsi-ld:Device:UNEXE_TEST_28','urn:ngsi-ld:Device:UNEXE_TEST_76']

    while quitApp is False:
        while quitApp is False:
            print()
            print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])
            print('ALERT_BROKER:  ' + os.environ['ALERT_BROKER'])

            print()
            print('0..Reset Broker + Create initial backlog')
            print('1..Create patch data')

            print()
            print('2..TGO0P12AGOP1.Pressure - State Toggle')

            print()
            print('4..EPANET anomaly - Active + localisable')
            print('5..EPANET anomaly - Disabled')

            print()
            print('6..RI temp - Coliform ACTIVE')
            print('7..RI temp - Coliform NORMAL')

            print()
            print('8..All normal')

            print('X..Quit')
            print()

            key = input('>')

            if key == '0':
                types = ['AlertSetting' , 'AlertStatus', 'AnomalySetting', 'AnomalyStatus', 'AnomalyStatusEPAnet', 'Device', 'DeviceSimulationSettings', 'ChartStatus']
                support.delete_type_from_broker(os.environ['DEVICE_BROKER'], fiware_service, types = types)
                backlogbuilder.build_backlog(fiware_wrapper, days=28, timestep=15, all_pilots=False)

                support.create_alert_settings_from_device_sim_settings(fiware_service)

                support.do_all_processing(fiware_service)
                support.on_normaldevice_update(fiware_service)
                support.do_charting(fiware_service)

            if key == '1':
                support.generate_new_device_data(fiware_service)
                support.do_all_processing(fiware_service)
                support.on_normaldevice_update(fiware_service)
                support.do_charting(fiware_service)

            if key == '2':
                simDeviceInfo = unexeaqua3s.simdeviceinfo.SimDeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
                simDeviceInfo.run()

                simDeviceInfo.enabled_toggle('urn:ngsi-ld:Device:TGO0P12AGOP1_1_K_VLP_VLPA001_MFPRE01', fiware_service)

                support.on_normaldevice_update(fiware_service)

            if key == '4':
                simDeviceInfo = unexeaqua3s.simdeviceinfo.SimDeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
                simDeviceInfo.run()

                for entity in epa_anomaly_list:
                    simDeviceInfo.propstate_set(entity, fiware_service,unexeaqua3s.sim_pilot.controlled_by_scenario_in_epanomaly)

                support.do_all_processing(fiware_service)
                support.on_normaldevice_update(fiware_service)

            if key == '5':
                simDeviceInfo = unexeaqua3s.simdeviceinfo.SimDeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
                simDeviceInfo.run()

                for entity in epa_anomaly_list:
                    simDeviceInfo.propstate_set(entity, fiware_service,unexeaqua3s.sim_pilot.controlled_by_scenario)

                support.do_all_processing(fiware_service)
                support.on_normaldevice_update(fiware_service)



            if key == '6':
                simDeviceInfo = unexeaqua3s.simdeviceinfo.SimDeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
                simDeviceInfo.run()

                simDeviceInfo.propstate_set('urn:ngsi-ld:Device:Sensor_RI', fiware_service,unexeaqua3s.sim_pilot.controlled_by_scenario_out_of_range_high)

                support.do_all_processing(fiware_service)
                support.on_normaldevice_update(fiware_service)


            if key == '7':
                simDeviceInfo = unexeaqua3s.simdeviceinfo.SimDeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
                simDeviceInfo.run()

                simDeviceInfo.propstate_set('urn:ngsi-ld:Device:Sensor_RI', fiware_service,unexeaqua3s.sim_pilot.controlled_by_scenario)

                support.do_all_processing(fiware_service)
                support.on_normaldevice_update(fiware_service)



            if key == 'x':
                quitApp = True

if __name__ == '__main__':
    testbed()


