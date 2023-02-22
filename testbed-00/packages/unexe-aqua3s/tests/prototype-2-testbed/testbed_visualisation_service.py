import threading
import unexeaqua3s.siteinfo
import unexeaqua3s.service_alert
import unexeaqua3s.service_anomaly
import unexeaqua3s.service_chart
import unexefiware.ngsildv1
import unexefiware.fiwarewrapper
import requests
import os
import datetime
import unexeaqua3s.json

import backlogbuilder
from unexeaqua3s import support

_siteInfo = None
mutex = threading.Lock()

def get_siteInfo(loc, update=False):
    global mutex
    mutex.acquire()

    global _siteInfo

    if _siteInfo == None:
        device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
        alert_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['ALERT_BROKER'], historic_url=os.environ['ALERT_HISTORIC_BROKER'])

        _siteInfo = unexeaqua3s.deviceinfo.DeviceInfo(loc, device_wrapper = device_wrapper, other_wrapper=alert_wrapper)
        update = True

    if update:
        _siteInfo.run()

    mutex.release()

    return _siteInfo


def on_startup(rebuild_alert_anomaly_data = False):

    siteInfo = get_siteInfo('AAA')


    print_device_info()

def on_siteinfo_process():
    get_siteInfo('AAA', update=True)


def clear_anomaly_alert_data():
    session = requests.session()
    service = 'AAA'
    link = '<https://smartdatamodels.org/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
    url = os.environ['ALERT_BROKER']

    for label in [unexeaqua3s.deviceinfo.alertStatus_label,
                  unexeaqua3s.deviceinfo.alertSetting_label,
                  unexeaqua3s.deviceinfo.anomalyStatus_label,
                  unexeaqua3s.deviceinfo.anomalySetting_label,
                  unexeaqua3s.deviceinfo.chartStatus_label]:
        result = unexefiware.ngsildv1.get_type(session, url, label, link=link, fiware_service=service)

        if result[0] == 200:
            for entity in result[1]:
                unexefiware.ngsildv1.delete_instance(session, url, entity['id'], link, fiware_service=service)

def print_device_info():
    deviceInfo = get_siteInfo('AAA')

    for device_id in deviceInfo.deviceInfoList:
        print(str(device_id))
        print('\t'+deviceInfo.deviceInfoList[device_id][unexeaqua3s.deviceinfo.alertStatus_label]['id'] + ' ' + str(deviceInfo.deviceInfoList[device_id][unexeaqua3s.deviceinfo.alertStatus_label]['data']))
        print('\t'+deviceInfo.deviceInfoList[device_id][unexeaqua3s.deviceinfo.anomalyStatus_label]['id'] + ' ' + str(deviceInfo.deviceInfoList[device_id][unexeaqua3s.deviceinfo.anomalyStatus_label]['data']))

def testbed():
    quitApp = False

    while quitApp is False:
        print('\n')
        print('0..Delete all the anomaly and alert data')
        print('1..Do Start-up')
        print('1a..Do Start-up & rebuild anomaly & alert data')
        print('2..Do SiteInfo Process')
        print('3..Print DeviceInfo')
        print('4..Charting Service')
        print('5..Build anomaly settings')
        print('66..Build Demo')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '0':
            clear_anomaly_alert_data()


        if key == '1':
            on_startup()

        if key == '1a':
            clear_anomaly_alert_data()
            on_startup(rebuild_alert_anomaly_data=True)

        if key == '2':
            on_siteinfo_process()

        if key == '3':
            print_device_info()

        if key == '4':
            chart_service = unexeaqua3s.service_chart.ChartService()
            chart_service.update(get_siteInfo('AAA'))

        if key == '5':
            anomaly_service = unexeaqua3s.service_anomaly.AnomalyService()
            anomaly_service.build_from_deviceInfo(get_siteInfo('AAA'))

        if key == '66':
            #make a backlog
            backlogbuilder.build_backlog(support.device_wrapper, days=400, timestep=15, all_pilots=True)

            #add userlayers
            backlogbuilder.add_user_resources(os.environ['ALERT_BROKER'])

            device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            alert_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['ALERT_BROKER'], historic_url=os.environ['ALERT_HISTORIC_BROKER'])

            print('PILOTS:' + os.environ['PILOTS'])
            pilots = os.environ['PILOTS'].split(',')

            now = datetime.datetime.utcnow()
            fiware_time = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))

            alert_processor = unexeaqua3s.service_alert.AlertService()
            anomaly_processor = unexeaqua3s.service_anomaly.AnomalyService()

            for fiware_service in pilots:
                deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
                deviceInfo.run()

                #do charting for service
                chartingService = unexeaqua3s.service_chart.ChartService()
                chartingService.update(deviceInfo)


                #do alert settings from DeviceSimulationSettings
                pilot_sim_settings = alert_wrapper.get_entity('urn:ngsi-ld:DeviceSimulationSettings:1', fiware_service)

                if pilot_sim_settings != []:
                    simulation_settings = unexeaqua3s.json.loads(pilot_sim_settings['status']['value'])

                    for device_id in simulation_settings:
                        sensor_name = alert_processor.device_id_to_name(device_id)
                        settings = alert_processor.create_alert_settings(name=sensor_name,
                                                                   fiware_time='1970-01-01T00:00:00Z',
                                                                   normal_min= float(simulation_settings[device_id]['min']),
                                                                   normal_max= float(simulation_settings[device_id]['max']))

                        alert_wrapper.create_instance(settings, deviceInfo.service)

                # do alert & anomaly status backlogs
                alert_processor.lumpyprocess(deviceInfo, fiware_time)
                anomaly_processor.lumpyprocess(deviceInfo, fiware_time)

                support.generate_new_device_data(fiware_service)
                support.process_alerts(fiware_service)
                support.process_anomalies(fiware_service)

        if key == 'x':
            quitApp = True


if __name__ == '__main__':
    testbed()