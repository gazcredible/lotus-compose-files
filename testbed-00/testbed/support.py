import unexeaqua3s.deviceinfo
import unexefiware.fiwarewrapper
import unexefiware.time
import json
import datetime
import inspect
import os
import requests

device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])

logger = unexefiware.base_logger.BaseLogger()

device_wrapper.init(logger=logger)


def print_device_info2(deviceInfo, device_id,service):
    text = ''

    text += (device_id + ' ' + deviceInfo.device_name(device_id)) .ljust(87, ' ')

    text += deviceInfo.property_prettyprint(device_id).ljust(16, ' ')
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
        scenario_data = json.loads(fiware_simulation_settings['status']['value'])[device_id]

        text += ' Sim:'
        text += (' E:' + scenario_data['enabled']).ljust(10, ' ')
        text += ' '
        text += (' Prop State:' + scenario_data['prop_state']).ljust(35, ' ')
    else:
        text += ' '.ljust(51,' ')


    #anomaly
    if deviceInfo._get_value_entry(device_id, unexeaqua3s.deviceinfo.anomalyStatus_label, 'triggered'):
        text += ('C:'  + str(deviceInfo._get_value_entry(device_id, unexeaqua3s.deviceinfo.anomalyStatus_label, 'count'))).ljust(4, ' ')
        text += ' '
        text += (str(deviceInfo._get_value_entry(device_id, unexeaqua3s.deviceinfo.anomalyStatus_label, 'triggered')[0])).ljust(1, ' ')
        text += ' '
        text += (str(deviceInfo._get_value_entry(device_id, unexeaqua3s.deviceinfo.anomalyStatus_label, 'reason'))).ljust(38, ' ')
    else:
        text += str('No Data').ljust(44,' ')

    text += ' '

    #alert
    if deviceInfo._get_value_entry(device_id, unexeaqua3s.deviceinfo.alertStatus_label, 'triggered'):
        text += (str(deviceInfo._get_value_entry(device_id, unexeaqua3s.deviceinfo.alertStatus_label, 'triggered')[0])).ljust(1, ' ')
        text += ' '
        text += str(deviceInfo.alertstatus_reason_prettyprint(device_id)).ljust(30, ' ')
    else:
        text += ' No Data'

    return text


def print_devices(deviceInfo):
    key_list = list(deviceInfo.deviceInfoList.keys())
    key_list = sorted(key_list)

    print(str('Device').ljust(87,' ')
        + str('Current Data').ljust(54,' ' )
        + str('Sim Settings').ljust(50,' ' )
        + str('Anomaly Status').ljust(46,' ' )
        + str('Alert Status').ljust(60,' ' )
        )

    for device_id in key_list:
        print(print_device_info2(deviceInfo, device_id, deviceInfo.service))
    print('')

def generate_new_device_data(current_service = 'AAA'):

    global device_wrapper
    global logger

    fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.utcnow())
    logger.log(inspect.currentframe(), 'Creating new data at: ' + fiware_time)

    simDeviceInfo = unexeaqua3s.simdeviceinfo.SimDeviceInfo(current_service, device_wrapper=device_wrapper)
    simDeviceInfo.run()
    simDeviceInfo.patch_all_devices(current_service, fiware_time)

def process_alerts(current_service = 'AAA'):
    global device_wrapper

    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(current_service, device_wrapper=device_wrapper)
    deviceInfo.run()

    alertService = unexeaqua3s.service_alert.AlertService()
    alertService.update(deviceInfo)

def process_anomalies(current_service = 'AAA'):
    global device_wrapper

    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(current_service, device_wrapper=device_wrapper)
    deviceInfo.run()

    serviceProcessor = unexeaqua3s.service_anomaly.AnomalyService()
    serviceProcessor.update(deviceInfo)


def delete_type_from_broker(broker_url, service, types):
    session = requests.session()
    link = '<https://smartdatamodels.org/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'


    for label in types:
        result = unexefiware.ngsildv1.get_type(session, broker_url, label, link=link, fiware_service=service)

        if result[0] == 200:
            for entity in result[1]:
                print('Deleting: ' + entity['id'])
                unexefiware.ngsildv1.delete_instance(session, broker_url, entity['id'], link, fiware_service=service)


def print_resources(broker_url:str, service:str, smart_models:list):
    session = requests.Session()
    link = 'https://schema.lab.fiware.org/ld/context'

    for model_type in smart_models:
        result = unexefiware.ngsildv1.get_type_count_orionld(session, broker_url, model_type, link=link, fiware_service=service)

        if result[0] == 200:

            item_count = result[1]['entityCount']

            if item_count > 0:
                print(model_type)

                for i in range(0, item_count):
                    try:
                        # get first entry in the list, rather than ith one as it will move :S
                        result = unexefiware.ngsildv1.get_type_by_index_orionld(session, broker_url, model_type, i, link, service)
                        if result[0] == 200:
                            print('\t'+ result[1][0]['id'])

                    except Exception as e:
                        print('Vague failure: ' + str(e))

                print()
    print()

def delete_resources(broker_url, service, smart_models:list):

    session = requests.Session()
    link = 'https://schema.lab.fiware.org/ld/context'

    for model_type in smart_models:
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

