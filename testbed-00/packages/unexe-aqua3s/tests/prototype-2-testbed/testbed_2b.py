import local_environment_settings
import os
import testbed_devices
import time

import unexeaqua3s.brokerdefinition
import unexeaqua3s.kibanablelog
import unexefiware.fiwarewrapper
import testbed_userlayer

special_pilot = 'AAA'

pilot_definition = [
        {'pilot': 'P2B', 'sensor_name': 'TGO0P12AGOP1_1_K_VLP_VLPA001_MFPRE01', 'name': 'P12', 'property': 'pressure', 'source': 'WELL', 'unitcode': 'N23', 'location': [45.84470284, 13.45316127], 'limit': {'normal_min': 50, 'normal_max': 70}},
        {'pilot': 'P2B', 'sensor_name': 'TGO0P12AGOP1_1_K_LIV_FALD001_MFCON01', 'name': 'P12', 'property': 'conductibility', 'source': 'WELL', 'unitcode': 'H61', 'location': [45.84470284, 13.45316127], 'limit': {'normal_min': 200, 'normal_max': 220}},
        {'pilot': 'P2B', 'sensor_name': 'TGO0P12AGOP1_1_K_LIV_FALD001_MFLIV01', 'name': 'P12', 'property': 'level', 'source': 'WELL', 'unitcode': 'MTR', 'location': [45.84470284, 13.45316127], 'limit': {'normal_min': 3, 'normal_max': 5}},
        {'pilot': 'P2B', 'sensor_name': 'TGO0P12AGOP1_1_K_VLP_VLPA001_MFPOR01', 'name': 'P12', 'property': 'level', 'source': 'WELL', 'unitcode': 'm3/h', 'location': [45.84470284, 13.45316127], 'limit': {'normal_min': 3, 'normal_max': 5}},

        {'pilot': 'P2B', 'sensor_name': 'TTS0RANATSN9_3_K_STC_VASC001_MFLIV06', 'name': 'SARDOS', 'property': 'level', 'source': 'CHANNEL', 'unitcode': 'MTR', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 3, 'normal_max': 5}},
        {'pilot': 'P2B', 'sensor_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR05', 'name': 'SARDOS', 'property': 'ph', 'source': 'SPRING', 'unitcode': 'Q30', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 6.95, 'normal_max': 7.2}},
        {'pilot': 'P2B', 'sensor_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR03', 'name': 'SARDOS', 'property': 'turbidity', 'source': 'SPRING', 'unitcode': 'NTU', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 1, 'normal_max': 3}},
        {'pilot': 'P2B', 'sensor_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR04', 'name': 'SARDOS', 'property': 'conductibility', 'source': 'SPRING', 'unitcode': 'H61', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 200, 'normal_max': 220}},
        {'pilot': 'P2B', 'sensor_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR06', 'name': 'SARDOS', 'property': 'uv', 'source': 'SPRING', 'unitcode': 'UV', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 0, 'normal_max': 0.1}},
        {'pilot': 'P2B', 'sensor_name': 'TTS0RANATSN9_3_K_GEN_IMPI001_MFPOR01', 'name': 'SARDOS', 'property': 'discharge', 'source': 'SPRING', 'unitcode': 'm3/h', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 0, 'normal_max': 2}},

        {'pilot': 'P2B', 'sensor_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR03', 'name': 'CAPTAZIONE TIMAVO - RAMO 1', 'property': 'pH', 'source': 'SPRING', 'unitcode': 'Q30', 'location': [45.787659, 13.590759], 'limit': {'normal_min': 6.95, 'normal_max': 7.2}},
        {'pilot': 'P2B', 'sensor_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR04', 'name': 'CAPTAZIONE TIMAVO - RAMO 1', 'property': 'UV', 'source': 'SPRING', 'unitcode': 'UV', 'location': [45.787659, 13.590759], 'limit': {'normal_min': 0, 'normal_max': 0.1}},
        {'pilot': 'P2B', 'sensor_name': 'TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV01', 'name': 'CAPTAZIONE TIMAVO - RAMO 1', 'property': 'level', 'source': 'SPRING', 'unitcode': 'MTR', 'location': [45.787659, 13.590759], 'limit': {'normal_min': 3, 'normal_max': 5}},

        {'pilot': 'P2B', 'sensor_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR02', 'name': 'CAPTAZIONE TIMAVO - RAMO 2', 'property': 'turbidity', 'source': 'SPRING', 'unitcode': 'NTU', 'location': [45.78673, 13.59128], 'limit': {'normal_min': 1, 'normal_max': 3}},
        {'pilot': 'P2B', 'sensor_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR01', 'name': 'CAPTAZIONE TIMAVO - RAMO 2', 'property': 'conductibility', 'source': 'SPRING', 'unitcode': 'H61', 'location': [45.78673, 13.59128], 'limit': {'normal_min': 200, 'normal_max': 220}},
        {'pilot': 'P2B', 'sensor_name': 'TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV02', 'name': 'CAPTAZIONE TIMAVO - RAMO 2', 'property': 'level', 'source': 'SPRING', 'unitcode': 'MTR', 'location': [45.78673, 13.59128], 'limit': {'normal_min': 3, 'normal_max': 5}},

        #{'pilot': 'P2B', 'sensor_name': 'TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV03', 'name': 'CAPTAZIONE TIMAVO - RAMO 3', 'property': 'level', 'source': 'SPRING', 'unitcode': 'MTR', 'location': [45.78673, 13.59128], 'limit': {'normal_min': 3, 'normal_max': 5}},
        {'pilot': 'P2B', 'sensor_name': 'TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV03', 'name': 'CAPTAZIONE TIMAVO - RAMO 3', 'property': 'level', 'source': 'SPRING', 'unitcode': 'MTR', 'location': [45.78773, 13.59228], 'limit': {'normal_min': 3, 'normal_max': 5}},

        {'pilot': 'SVK', 'sensor_name': 'CDGEastpressuredevice', 'name': 'CDGEastpressuredevice', 'location': [42.9025605, 23.8058583], 'property': 'pressure', 'unitcode': 'N23', 'limit': {'normal_min': 50, 'normal_max': 70}},
        {'pilot': 'SOF', 'sensor_name': 'RI1_PRESSURE', 'name': 'RI1', 'location': [42.603111, 23.178722], 'property': 'pressure', 'unitcode': 'N23', 'limit': {'normal_min': 50, 'normal_max': 70}},
        {'pilot': 'EYA', 'sensor_name': 'TH1_PRESSURE', 'name': 'TH1', 'location': [40.628, 22.95], 'property': 'pressure', 'unitcode': 'N23', 'limit': {'normal_min': 50, 'normal_max': 70}},
        {'pilot': 'WBL', 'sensor_name': 'WBL1_PRESSURE', 'name': 'WBL1', 'location': [50.89, 4.34], 'property': 'pressure', 'unitcode': 'N23', 'limit': {'normal_min': 50, 'normal_max': 70}},

        {'pilot': 'GT', 'sensor_name': 'GT1_PRESSURE', 'name': 'GT1', 'location': [50.954, -4.137], 'property': 'pressure', 'unitcode': 'N23', 'limit': {'normal_min': 50, 'normal_max': 70}},

        {'pilot': 'WIS', 'sensor_name': 'WIS1_PRESSURE', 'name': 'WIS1', 'location': [50.814, -4.257], 'property': 'pressure', 'unitcode': 'N23', 'limit': {'normal_min': 50, 'normal_max': 70}},
        {'pilot': 'WIS', 'sensor_name': 'GT1_PRESSURE', 'name': 'GT1', 'location': [50.954, -4.137], 'property': 'pressure', 'unitcode': 'N23', 'limit': {'normal_min': 50, 'normal_max': 70}},
    ]

import backlogbuilder
from unexeaqua3s import support


def testbed():
    quitApp = False

    logger = unexeaqua3s.kibanablelog.KibanableLog('3D_Visualisation')

    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    fiware_wrapper.init(logger=logger)
    fiware_service = os.environ['PILOTS']

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])
        print('ALERT_BROKER:  ' + os.environ['ALERT_BROKER'])

        print('\n')
        print('0..Delete broker')
        print('01..Delete Alerts')
        print('\n')
        print('1..Create normal devices')
        print('1a..Create normal devices with backlog')
        print('1b..PATCH normal devices')
        print()

        print('2..Create epanet devices')
        print('2a..Create epanet devices with backlog')
        print('2b..PATCH epanet devices')
        print('2c..DELETE epanet devices')
        print('2d..Create Userlayers')
        print()

        print('3..ALERT all devices')
        print('3a..ALERT delete settings')
        print()

        print('4..ANOMALY normal devices')
        print('5..ANOMALY epanet devices')
        print('5a..ANOMALY delete epanet devices')
        print()

        print('6..CHART all devices')
        print()

        print('7..PATCH devices + do all processing')
        print('71..just do all processing')

        print('91..Notify visualiser of device update')


        print('X..Back')
        print('\n')

        key = input('>')

        if key == '0':
            support.delete_type_from_broker(os.environ['DEVICE_BROKER'], fiware_service
                                            , ['AlertSetting'
                                                ,'AlertStatus'
                                                , 'AnomalySetting'
                                                , 'AnomalyStatus'
                                                , 'AnomalyStatusEPAnet'
                                                , 'Device'
                                                , 'DeviceSimulationSettings'
                                                , 'ChartStatus'])

        if key == '01':
            support.delete_type_from_broker(os.environ['DEVICE_BROKER'], fiware_service
                                            , ['AlertSetting'
                                              ,'AlertStatus'
                                              ])


        if key == '1':
            support.delete_normal_devices(os.environ['DEVICE_BROKER'], fiware_service)
            backlogbuilder.build_backlog(fiware_wrapper,days=0, timestep=15,all_pilots=False)
            support.on_normaldevice_update(fiware_service)

        if key == '1a':
            support.delete_normal_devices(os.environ['DEVICE_BROKER'], fiware_service)
            backlogbuilder.build_backlog(fiware_wrapper,days=7, timestep=15,all_pilots=False)
            support.on_normaldevice_update(fiware_service)

        if key == '1b':
            support.generate_new_device_data(fiware_service)
            support.on_normaldevice_update(fiware_service)

        if key == '2':
            support.delete_epanet_devices(os.environ['DEVICE_BROKER'], fiware_service)
            pass #create epanet devices

        if key == '2a':
            support.delete_epanet_devices(os.environ['DEVICE_BROKER'], fiware_service)
            testbed_devices.build_pilot_from_epanet(fiware_wrapper,fiware_service)

        if key == '2b':
            pass #PATCH epanet devices

        if key == '2c':
            support.delete_epanet_devices(os.environ['DEVICE_BROKER'], fiware_service)

        if key == '2d':
            testbed_userlayer.testbed(fiware_wrapper, fiware_service)



        if key == '3':
            #print('3..ALERT all devices')
            support.update_device_alert_info(fiware_service)

        if key == '3a':
            support.delete_type_from_broker(os.environ['DEVICE_BROKER'], fiware_service, 'AlertSetting')
            support.delete_type_from_broker(os.environ['DEVICE_BROKER'], fiware_service, 'AlertStatus')

        if key == '4':
            #print('4..ANOMALY normal devices')
            support.update_device_anomaly_info(fiware_service)
            support.on_normaldevice_update(fiware_service)

        if key == '5':
            support.update_device_epanetanomaly_info(fiware_service)

        if key == '5a':
            support.delete_type_from_broker(os.environ['DEVICE_BROKER'], fiware_service, 'AnomalyStatusEPAnet')

        if key =='6':
            support.do_charting(fiware_service)

        if key == '7':
            t0 = time.perf_counter()
            print('Create new device data')
            #support.generate_new_device_data(fiware_service)
            #send that to workhouse ->
            print('Process Alerts')
            support.update_device_alert_info(fiware_service)
            support.on_normaldevice_update(fiware_service)

            print('Process EPANET anomalies')
            support.update_device_epanetanomaly_info(fiware_service)
            support.on_normaldevice_update(fiware_service)

            print('Process normal anomalies')
            support.update_device_anomaly_info(fiware_service)
            support.on_normaldevice_update(fiware_service)

            print('Do charting')
            support.do_charting(fiware_service)

            print(str(time.perf_counter() - t0))

        if key == '71':
            t0 = time.perf_counter()
            print('Process Alerts')
            support.update_device_alert_info(fiware_service)
            support.on_normaldevice_update(fiware_service)

            print('Process EPANET anomalies')
            support.update_device_epanetanomaly_info(fiware_service)
            support.on_normaldevice_update(fiware_service)

            print('Process normal anomalies')
            support.update_device_anomaly_info(fiware_service)
            support.on_normaldevice_update(fiware_service)

            print('Do charting')
            support.do_charting(fiware_service)

            print(str(time.perf_counter() - t0))

        if key == '72':
            t0 = time.perf_counter()
            support.do_all_processing(fiware_service)
            print(str(time.perf_counter() - t0))


        if key == '91':
            support.on_normaldevice_update(fiware_service)

        if key == 'x':
                quitApp = True

if __name__ == '__main__':
    testbed()
