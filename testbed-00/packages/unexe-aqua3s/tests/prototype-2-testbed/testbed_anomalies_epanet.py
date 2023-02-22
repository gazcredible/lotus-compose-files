import unexeaqua3s.service_alert
import unexeaqua3s.deviceinfo
import unexeaqua3s.service
import os
import unexefiware.base_logger
import unexefiware.time
from unexeaqua3s import support
import datetime
import unexefiware.workertask
import time

import unexeaqua3s.service_chart
import unexeaqua3s.service_anomaly
import unexeaqua3s.service_anomaly_epanet

import unexeaqua3s.resourcebuilder


def testbed(fiware_service):
    quitApp = False

    alertService = unexeaqua3s.service_alert.AlertService()
    logger = unexefiware.base_logger.BaseLogger()

    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    fiware_wrapper.init(logger=logger)

    my_broker = unexeaqua3s.brokerdefinition.BrokerDefinition()
    my_broker.init(fiware_wrapper)

    alert_init_data = {'orion_broker': fiware_wrapper.url, 'drop_tables': 'True', 'fiware_service': fiware_service}

    while quitApp is False:
        print('\nEPANET Anomaly Testbed')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])
        print('ALERT_BROKER:  ' + os.environ['ALERT_BROKER'])

        print('\n')
        print('0..Delete broker data (devices, alerts, anomalies')
        print('3..Run Anomaly Epanet process')
        print('4..IoTAgent generation')
        print('5..View Stuff')
        print('6..View History')
        print('9..New Stuff')
        print('9a..New Stuff - Do multiprocess')


        print('X..Back')
        print('\n')

        key = input('>')

        if key == '0':
            pilots = os.environ['PILOTS'].split(',')

            for fiware_service in pilots:
                other_types = [unexeaqua3s.deviceinfo.alertStatus_label,
                      unexeaqua3s.deviceinfo.alertSetting_label,
                      unexeaqua3s.deviceinfo.anomalyStatus_label,
                      unexeaqua3s.deviceinfo.anomalySetting_label,
                      unexeaqua3s.deviceinfo.chartStatus_label]

                support.delete_type_from_broker(os.environ['ALERT_BROKER'], fiware_service, other_types)


        if key == '3':

            now = datetime.datetime.utcnow()
            fiware_time = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))
            pilots = os.environ['PILOTS'].split(',')

            for fiware_service in pilots:

                print(fiware_service)
                deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=support.device_wrapper, other_wrapper=support.alert_wrapper)
                deviceInfo.run()
                historic_data = unexeaqua3s.service_anomaly_epanet.HistoricData()
                historic_data.collect_anomaly_webdavData(fiware_service) #load up z value db
                historic_data.processEPAnetAnomalies(deviceInfo, fiware_time, fiware_service)

        if key == '4':
            if False:
                pilots = os.environ['PILOTS'].split(',')

                for fiware_service in pilots:
                    support.generate_new_device_data(fiware_service)

        if key == '5':
            pilots = os.environ['PILOTS'].split(',')

            for fiware_service in pilots:
                print(fiware_service)
                deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=support.device_wrapper, other_wrapper=support.alert_wrapper)
                deviceInfo.run()

                support.print_devices(deviceInfo)
                print()

        if key == '6':
            pilots = os.environ['PILOTS'].split(',')

            now = datetime.datetime.utcnow()
            fiware_time = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))

            for fiware_service in pilots:
                print(fiware_service)
                deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=support.device_wrapper, other_wrapper=support.alert_wrapper)
                deviceInfo.run()

                historic_data = HistoricData()
                historic_data.collectData(deviceInfo,fiware_time)

                for entry in historic_data.collect_data_results:
                    print(entry)

                print()

        if key =='9':
            pilot_lookup = os.environ['PILOTS'].split(',')

            for pilot in pilot_lookup:
                deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(pilot, device_wrapper=support.device_wrapper, other_wrapper=support.alert_wrapper)
                deviceInfo.run()

                now = datetime.datetime.utcnow()
                now += datetime.timedelta(hours=24)
                fiware_time = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))

                t0 = time.perf_counter()

                key_list = list(deviceInfo.deviceInfoList.keys())
                key_list = sorted(key_list)

                start_time = '1980-01-01T00:00:00Z'
                start_time = '2022-02-17T10:00:00Z'

                fiware_time = '2022-02-18T13:00:00Z'

                now = datetime.datetime.utcnow()
                now += datetime.timedelta(hours=24)
                fiware_time = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))

                key_list = ['urn:ngsi-ld:Device:0121UV254']

                for device_id in key_list:
                    raw_device_data = deviceInfo.brokers[unexeaqua3s.deviceinfo.device_label].get_temporal_orion(deviceInfo.service, device_id
                                                                                                                 , start_time
                                                                                                                 , fiware_time)

                    alert_processor = unexeaqua3s.service_alert.AlertService()
                    alert_processor.lumpyprocess_device(deviceInfo, device_id, fiware_time, raw_device_data,fiware_start_time=start_time)

        if key == '9a':
            pass
            """
            mprocessor = unexeaqua3s.mprocessor.MultiprocessorBase()

            pilot_lookup = os.environ['PILOTS'].split(',')

            for pilot in pilot_lookup:
                deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(pilot, device_wrapper=support.device_wrapper, other_wrapper=support.alert_wrapper)
                deviceInfo.run()

                print('Doing: ' + pilot)
                mprocessor.step(deviceInfo)
                print()
                print()
            """

        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    testbed()

