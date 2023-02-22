import unexeaqua3s.deviceinfo
#import unexeaqua3s.simdeviceinfo
import unexefiware.fiwarewrapper
import unexefiware.time
import unexeaqua3s.json
import datetime
import inspect
import os
import requests
import time

import unexefiware.base_logger

import unexeaqua3s.service_anomaly
import unexeaqua3s.service_alert
import unexeaqua3s.service_chart
import unexeaqua3s.service
import unexeaqua3s.resourcebuilder

device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])

logger = unexefiware.base_logger.BaseLogger()

device_wrapper.init(logger=logger)


def print_device_info2(deviceInfo, device_id,service):
    text = ''

    text += (device_id + ' ' + deviceInfo.device_name(device_id)) .ljust(87, ' ')

    text += deviceInfo.property_prettyprint(device_id).ljust(20, ' ')
    text += ' '
    text += deviceInfo.property_value_prettyprint(device_id).rjust(8, ' ')
    text += ' '
    text += deviceInfo.property_observedAt(device_id)

    text += ' '
    text += deviceInfo.device_status(device_id).ljust(6, ' ')

    fiware_simulation_settings = []
    if False:
        fiware_simulation_settings = deviceInfo.brokers[unexeaqua3s.deviceinfo.device_label].get_entity('urn:ngsi-ld:DeviceSimulationSettings:1', deviceInfo.service)

    if fiware_simulation_settings != []:
        scenario_data = unexeaqua3s.json.loads(fiware_simulation_settings['status']['value'])[device_id]

        text += ' Sim:'
        text += (' E:' + scenario_data['enabled']).ljust(10, ' ')
        text += ' '
        text += (' Prop State:' + scenario_data['prop_state']).ljust(35, ' ')
    else:
        pass
        #text += ' '.ljust(51,' ')

    text += '   '

    #anomaly
    size  = 20
    if deviceInfo.anomaly_isTriggered(device_id):
        text +=  str(deviceInfo.anomaly_reason(device_id)).ljust(size,' ' )
    else:
        text += str('In range').ljust(size,' ')

    text += ' '

    #alert
    size = 33
    if deviceInfo.alert_isTriggered(device_id):
        text += str(deviceInfo.alertstatus_reason_prettyprint(device_id)).ljust(size, ' ')
    else:
        text += str(' In range').ljust(size,' ')

    if False:
        temp = deviceInfo.device_get(device_id)
        text += str(temp['location'])

    return text


def print_devices(deviceInfo:unexeaqua3s.deviceinfo.DeviceInfo2):
    key_list = list(deviceInfo.deviceInfoList.keys())
    key_list = sorted(key_list)

    print(str('Device').ljust(87,' ')
        + str('Current Data').ljust(60,' ' )
#        + str('Sim Settings').ljust(50,' ' )
        + str('Anomaly Status').ljust(22,' ' )
        + str('Alert Status').ljust(33,' ' )
        )

    for device_id in key_list:
        print(print_device_info2(deviceInfo, device_id, deviceInfo.fiware_service))
    print('')

def generate_new_device_data(current_service = 'AAA'):

    global device_wrapper
    global alert_wrapper
    global logger

    fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.utcnow())
    logger.log(inspect.currentframe(), 'Creating new data at: ' + fiware_time)

    simDeviceInfo = unexeaqua3s.simdeviceinfo.SimDeviceInfo(current_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
    simDeviceInfo.run()
    simDeviceInfo.patch_all_devices(current_service, fiware_time)

def process_alerts(current_service = 'AAA'):
    global device_wrapper
    global alert_wrapper

    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(current_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
    deviceInfo.run()

    alertService = unexeaqua3s.service_alert.AlertService()
    alertService.update(deviceInfo)

def process_anomalies(current_service = 'AAA'):
    global device_wrapper
    global alert_wrapper

    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(current_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
    deviceInfo.run()

    serviceProcessor = unexeaqua3s.service_anomaly.AnomalyService()
    serviceProcessor.update(deviceInfo)


def delete_type_from_broker(broker_url, service, types):
    session = requests.session()
    link = '<https://smartdatamodels.org/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'

    if not isinstance(types, list):
        types = [types]

    for label in types:
        result = unexefiware.ngsildv1.get_type(session, broker_url, label, link=link, fiware_service=service)

        if result[0] == 200:
            for entity in result[1]:
                print('Deleting: ' + entity['id'])
                unexefiware.ngsildv1.delete_instance(session, broker_url, entity['id'], link, fiware_service=service)


def delete_normal_devices(broker_url, fiware_service):
    session = requests.session()
    link = '<https://smartdatamodels.org/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'

    result = unexefiware.ngsildv1.get_type_count_orionld(session, broker_url, 'Device', link=link, fiware_service=fiware_service)

    if result[0] == 200:
        if 'entityCount' in result[1]:
            entityCount = int(result[1]['entityCount'])

            entities = []

            for i in range(0, entityCount):
                result = unexefiware.ngsildv1.get_type_by_index_orionld(session, broker_url, 'Device', i, link=link, fiware_service=fiware_service)

                if result[0] == 200:
                    device = result[1][0]

                    if 'epanet_reference' not in device:
                        entities.append(device['id'])

            if len(entities) > 0:
                for entity in entities:
                    print('Deleting: ' + entity)
                    unexefiware.ngsildv1.delete_instance(session, broker_url, entity, link, fiware_service=fiware_service)


def delete_epanet_devices(broker_url, fiware_service):
    session = requests.session()
    link = '<https://smartdatamodels.org/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'

    result = unexefiware.ngsildv1.get_type_count_orionld(session, broker_url, 'Device', link=link, fiware_service=fiware_service)

    if result[0] == 200:
        if 'entityCount' in result[1]:
            entityCount = int(result[1]['entityCount'])

            entities = []

            for i in range(0, entityCount):
                result = unexefiware.ngsildv1.get_type_by_index_orionld(session, broker_url, 'Device', i, link=link, fiware_service=fiware_service)

                if result[0] == 200:
                    device = result[1][0]

                    if 'epanet_reference' in device:
                        entities.append(device['id'])

            if len(entities) > 0:
                for entity in entities:
                    print('Deleting: ' + entity)
                    unexefiware.ngsildv1.delete_instance(session, broker_url, entity, link, fiware_service=fiware_service)




import unexeaqua3s.service_anomaly_epanet
def update_device_epanetanomaly_info(fiware_service):
    try:
        global device_wrapper
        global alert_wrapper

        deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
        deviceInfo.run()

        now = datetime.datetime.utcnow()
        now += datetime.timedelta(hours=24)
        fiware_time = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))

        historic_data = unexeaqua3s.service_anomaly_epanet.HistoricData()
        historic_data.collect_anomaly_webdavData(fiware_service)  # load up z value db
        historic_data.processEPAnetAnomalies(deviceInfo, fiware_time, fiware_service)
    except Exception as e:
        print(str(e))



def on_normaldevice_update(fiware_service):
    try:
        headers = {}
        headers['Content-Type'] = 'application/ld+json'
        headers['fiware-service']= fiware_service
        session = requests.session()

        path = os.environ['VISUALISER'] + '/pilot_device_update'
        payload = {'fiware-service': fiware_service}

        r = session.post(path, data=unexeaqua3s.json.dumps(payload), headers=headers, timeout=10)
        print(str(r))

    except Exception as e:
        print(str(e))

def do_charting(fiware_service, force_interday=False, logger=None):
    global device_wrapper
    global alert_wrapper

    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service)
    deviceInfo.run()

    chartingService = unexeaqua3s.service_chart.ChartService()

    if logger:
        chartingService.logger = logger

    chartingService.update(deviceInfo, write_to_broker=True, force_process=True, force_interday = force_interday)

def create_alert_settings_from_device_sim_settings(fiware_service):
    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
    deviceInfo.run()

    fiware_simulation_settings = deviceInfo.brokers[unexeaqua3s.deviceinfo.device_label].get_entity('urn:ngsi-ld:DeviceSimulationSettings:1', deviceInfo.service)

    sim_settings = unexeaqua3s.json.loads(fiware_simulation_settings['status']['value'])

    for entry in sim_settings:
        fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.utcnow())
        last_status = '1970-01-01T00:00:00Z'

        raw_device_data = deviceInfo.brokers[unexeaqua3s.deviceinfo.device_label].get_temporal_orion(deviceInfo.service, entry
                                                                                                     , last_status
                                                                                                     , fiware_time)

        if raw_device_data != []:
            fiware_time = raw_device_data[0]['observedAt']

            asettings = unexeaqua3s.service_alert.create_alert_settings(unexeaqua3s.service.device_id_to_name(entry), fiware_time = fiware_time, normal_min=sim_settings[entry]['min'], normal_max=sim_settings[entry]['max'])

            deviceInfo.brokers[unexeaqua3s.deviceinfo.alertSetting_label].delete_instance(asettings['id'], deviceInfo.service)
            deviceInfo.brokers[unexeaqua3s.deviceinfo.alertSetting_label].create_instance(asettings, deviceInfo.service)

            asettings = unexeaqua3s.service_anomaly_epanet.create_DubiousEPAnomaly_settings(unexeaqua3s.service.device_id_to_name(entry), fiware_time=fiware_time, normal_min=sim_settings[entry]['min'], normal_max=sim_settings[entry]['max'])

            deviceInfo.brokers[unexeaqua3s.deviceinfo.alertSetting_label].delete_instance(asettings['id'], deviceInfo.service)
            deviceInfo.brokers[unexeaqua3s.deviceinfo.alertSetting_label].create_instance(asettings, deviceInfo.service)



def delete_resources(broker_url, service):
    types = ['WaterNetwork', 'SimulationResult', 'UserLayer']

    session = requests.Session()
    link = 'https://schema.lab.fiware.org/ld/context'

    for model_type in types:
        result = unexefiware.ngsildv1.get_type_count_orionld(session, broker_url, model_type, link=link, fiware_service=service)

        if result[0] == 200:

            item_count = result[1]['entityCount']

            if item_count > 0:
                for i in range(0, item_count):
                    try:
                        # get first entry in the list, rather than ith one as it will move :S
                        result = unexefiware.ngsildv1.get_type_by_index_orionld(session, broker_url, model_type, 0, link, service)
                        if result[0] == 200:
                            result = unexefiware.ngsildv1.delete_instance(session, broker_url, result[1][0]['id'], link, service)

                            if result[0] != 200:
                                print('Deletion failed: ' + result[1])

                    except Exception as e:
                        print('Vague failure: ' + str(e))

def add_user_resources(url, pilot_list = None, create_fiware_resources = True, force_build_files = False):

    if 'WEBDAV_URL' not in os.environ:
        raise Exception('Webdav not defined')

    options = {
        'webdav_hostname':  os.environ['WEBDAV_URL'],
        'webdav_login': os.environ['WEBDAV_NAME'],
        'webdav_password': os.environ['WEBDAV_PASS']
    }

    resourcebuilder = unexeaqua3s.resourcebuilder.ResourceBuilder(options=options)
    resourcebuilder.convert_files = True
    resourcebuilder.perform_file_operations = True
    #gareth -   this is the same as the path in visualiser.resourceManager
    resourcebuilder.init(path_root = os.environ['FILE_PATH'] + os.sep + os.environ['FILE_VISUALISER_FOLDER'], clone_remote=True,pilot_list=pilot_list)

    resources = resourcebuilder.process_kmz_resources()
    resources += resourcebuilder.process_shapefile_resources(force_build_files)
    resources += resourcebuilder.process_waternetwork_resources()

    if create_fiware_resources:
        resourcebuilder.create_fiware_assets(url, resources)


import pytz

def get_fiware_time(fiware_service):
    timezone = pytz.timezone('CET')

    if fiware_service == 'AAA':
        timezone = pytz.timezone('Europe/Rome')

    if fiware_service == 'SOF':
        timezone = pytz.timezone('Europe/Sofia')

    if fiware_service == 'SVK':
        timezone = pytz.timezone('Europe/Sofia')

    dt = datetime.datetime.now(timezone)
    fiware_time = unexefiware.time.datetime_to_fiware(dt)

    return fiware_time
