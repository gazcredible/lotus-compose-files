import copy
import datetime
import inspect
import unexeaqua3s.json

import local_environment_settings
import os

import unexefiware.fiwarewrapper
import unexefiware.fiwarewrapper_debug
import unexefiware.base_logger
import unexefiware.time

import unexeaqua3s.deviceinfo

def clone_broker(src:str, dest:str):
    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2('AAA')
    deviceInfo.run()

    logger = unexefiware.base_logger.BaseLogger()

    fiware_service = 'AAA'

    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=dest, historic_url=dest)
    fiware_wrapper.init(logger=logger)


    for label in deviceInfo.deviceModelList:
        print(label)

        device = deviceInfo.device_get(label)

        fiware_wrapper.delete_instance(device['id'], service=fiware_service, link=device['@context'])
        fiware_wrapper.create_instance(entity_json=device, service=fiware_service, link=device['@context'])


import requests
class unexe_wrapper(unexefiware.fiwarewrapper.fiwareWrapper):

    def version(self):

        headers = {}
        headers['Content-Type'] = 'application/ld+json'

        session = requests.session()

        path = self.url + '/unexe-broker/v1/version'

        try:
            r = session.get(path, data=unexeaqua3s.json.dumps([]), headers=headers, timeout=10)
            return unexefiware.ngsildv1.return_response(r)

        except Exception as e:
            return [-1, str(e)]

    def is_model_temporal(self, service: str, model: str) -> dict:
        instance = self.get_entity(model, service)

        results = {'temporal': False, 'attribs': []}

        for key in instance:
            if isinstance(instance[key], dict):
                if 'observedAt' in instance[key]:
                    results['attribs'].append(key)
                    results['temporal'] = True

        return results

import pickle
import base64
import zipfile

def dump_orion_broker(current_broker:str, historic_broker:str) -> bool:
    dump_object = {}

    logger = unexefiware.base_logger.BaseLogger()

    fiware_wrapper = unexe_wrapper(url=current_broker, historic_url=historic_broker)
    fiware_wrapper.init(logger=logger)

    entities = ['Device', 'ChartStatus','UserLayer']

    for fiware_service in os.environ['PILOTS'].split(','):
        dump_object[fiware_service] = {}

        for entity_type in entities:

            dump_object[fiware_service][entity_type] = []
            result = fiware_wrapper.get_entities(entity_type,fiware_service)
            if result[0] == 200:
                models = result[1]
                for model in models:
                    print(str(model['id']))

                    model_data = {}
                    model_data['model'] = model
                    model_data['temporal_data'] = {}

                    for key in model_data['model']:
                        if 'observedAt' in model_data['model'][key]:
                            temporal_result = fiware_wrapper.get_temporal_orion(fiware_service,model_data['model']['id'], '1980-01-01T00:00:00Z', model_data['model'][key]['observedAt'])

                            if len(temporal_result) > 0:
                                model_data['temporal_data'][key] = temporal_result

                    dump_object[fiware_service][entity_type].append(model_data)
    #
    file_root = 'a3s_broker_' + fiware_service + '_'+ str(datetime.datetime.now().replace(microsecond=0))

    with open(file_root + '.dump', 'wb') as f:
        pickle.dump(dump_object, f)

    with open(file_root + '.json', 'w') as f:
        f.write(unexeaqua3s.json.dumps(dump_object))

    with zipfile.ZipFile(file_root + '.unexeaqua3s.json.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as f:
        # add files
        f.write(file_root + '.json')

    with open(file_root + '.unexeaqua3s.json.zip', 'rb') as fin, open(file_root + '.unexeaqua3s.json.zip.b64', 'wb') as fout:
        base64.encode(fin, fout)

    return True

def dump_broker(current_broker:str, historic_broker:str=None) -> bool:

    logger = unexefiware.base_logger.BaseLogger()

    fiware_wrapper = unexe_wrapper(url=current_broker, historic_url=historic_broker)
    fiware_wrapper.init(logger=logger)

    result = fiware_wrapper.version()

    fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.now() + datetime.timedelta(days=1))

    dump_object = {}

    if result[0] == 200:
        data = result[1]

        for service in data:
            dump_object[service] = {}
            for model_type in data[service]:
                dump_object[service][model_type] = []
                for model in data[service][model_type]:

                    print('AR: ' + model)
                    instance = fiware_wrapper.get_entity(model, service)

                    if isinstance(instance, dict):
                        model_data = {}
                        model_data['model'] = instance

                        temporal_data = fiware_wrapper.get_temporal_orion(service, model, '1980-01-01T00:00:00Z',fiware_time)

                        if len(temporal_data) and 'observedAt' in temporal_data[0]:
                            model_data['temporal_data'] = temporal_data

                        dump_object[service][model_type].append(model_data)

        file_root ='broker_' + str(datetime.datetime.now().replace(microsecond=0))

        with open(file_root + '.dump','wb') as f:
            pickle.dump(dump_object,f)

        with open(file_root + '.json','w') as f:
            f.write(unexeaqua3s.json.dumps(dump_object))

        with zipfile.ZipFile(file_root+'.unexeaqua3s.json.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as f:
            #add files
            f.write(file_root+'.json')


        with open(file_root+'.unexeaqua3s.json.zip', 'rb') as fin, open('file_root+.unexeaqua3s.json.zip.b64', 'wb') as fout:
            base64.encode(fin, fout)


def restore_broker(current_broker:str, historic_broker:str, dump_file:str):

    logger = unexefiware.base_logger.BaseLogger()

    with open(dump_file, 'r') as f:
        try:
            ar = unexeaqua3s.json.load(f)

            fiware_wrapper = unexe_wrapper(url=current_broker, historic_url=historic_broker)
            fiware_wrapper.init(logger=logger)

            for fiware_service in ar:
                for entity_type in ar[fiware_service]:
                        for record in ar[fiware_service][entity_type]:
                            text = fiware_service + ' ' + entity_type + ' ' + record['model']['id']

                            if 'temporal_data' in record:
                                text += ' temporal:' + str(len(record['temporal_data']))

                            print(text)
                            fiware_wrapper.delete_instance(record['model']['id'],fiware_service)
                            fiware_wrapper.create_instance(record['model'],fiware_service)

                            if 'temporal_data' in record:

                                for key in record['temporal_data']:
                                    patch_list = []
                                    for data in record['temporal_data'][key]:
                                        patch_list.append({'value': data})

                                    fiware_wrapper.patch_entity(record['model']['id'], patch_list, fiware_service)
        except Exception as e:
            logger.exception(inspect.currentframe(),e)



def testbed(fiware_wrapper, fiware_service):
    quitApp = False

    fiware_service = 'EYA'

    logger = unexefiware.base_logger.BaseLogger()

    orion = 'https://platform.aqua3s.eu/orion'
    cygnus = 'https://platform.aqua3s.eu/api_cygnus'
    my_broker = 'http://52.50.143.202:8101'
    
    ar_to_load = 'a3s_broker_EYA_2022-09-16 10:08:14.json'
    ar_to_load = 'a3s_broker_VVQ_2022-11-02 15:50:56.json'

    while quitApp is False:
        print('\n')
        print('Testbed devices')
        print('DEVICE_BROKER: ' + orion +' ALERTS:'+my_broker )

        print('\n')
        print('1..Clone broker:' + fiware_service)
        print('2..Backup My broker:' + os.environ['DEVICE_BROKER'] +' Historic:' + os.environ['DEVICE_HISTORIC_BROKER'])
        print('3..Restore broker:' + os.environ['DEVICE_BROKER'] + ' Historic:' + os.environ['DEVICE_HISTORIC_BROKER'] +' ' +ar_to_load)

        print('4..Backup Orion/Cygnus brokers:' + os.environ['DEVICE_BROKER'] + ' Historic:' + os.environ['DEVICE_HISTORIC_BROKER'])
        print('5..Back-up from 31101')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            clone_broker(src= 'http://0.0.0.0:9101', dest = 'http://46.101.61.143:18101')
            #dump_broker(src = 'http://0.0.0.0:18101')
            if False: #dump from platform.aqua3s
                #dump devices, alert & anomalies
                device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=orion,historic_url=cygnus)
                alert_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=my_broker)
                deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)

                deviceInfo.run()

                for label in deviceInfo.deviceInfoList:

                    try:
                        entry = deviceInfo.deviceInfoList[label]
                        print(label)

                        device_record = copy.deepcopy(entry[unexeaqua3s.deviceinfo.device_label]['data'])

                        if entry[unexeaqua3s.deviceinfo.alertSetting_label]['data']:
                            device_record['alert_setting'] = {'type': 'Property', 'value': entry[unexeaqua3s.deviceinfo.alertSetting_label]['data']['status']['value']}
                        else:
                            device_record['alert_setting'] = {'type': 'Property', 'value': '{"min": "-9999", "max": "9999", "step": "1", "current_min": "-9999", "current_max": "9999", "active": "True"}'}

                        if entry[unexeaqua3s.deviceinfo.alertStatus_label]['data']:
                            device_record['alert_status'] = {'type': 'Property', 'value': entry[unexeaqua3s.deviceinfo.alertStatus_label]['data']['status']['value']}
                        else:
                            device_record['alert_status'] = {'type': 'Property', 'value': '{"triggered": "False", "reason": "Alert Settings Not Set"}'}

                        device_record['anomaly_setting'] = {'type': 'Property', 'value': entry[unexeaqua3s.deviceinfo.anomalySetting_label]['data']['status']['value']}

                        anomaly_setting = {}
                        anomaly_setting['ranges'] = unexeaqua3s.json.loads(device_record['anomaly_setting']['value'])
                        anomaly_setting['timelog'] = '60'

                        device_record['anomaly_setting']['value'] = unexeaqua3s.json.dumps(anomaly_setting)

                        device_record['anomaly_status'] = {'type': 'Property', 'value': entry[unexeaqua3s.deviceinfo.anomalyStatus_label]['data']['status']['value']}

                        device_record['epanomaly_setting'] = {'type': 'Property', 'value': ''}
                        device_record['epanomaly_status'] = {'type': 'Property', 'value': ''}

                        if 'https://uri.fiware.org/ns/data-models#deviceState' in device_record:
                            deviceState = copy.deepcopy(device_record['https://uri.fiware.org/ns/data-models#deviceState'])

                            if 'deviceState' not in device_record:
                                device_record['deviceState'] = deviceState

                        fiware_wrapper.delete_instance(device_record['id'], service=fiware_service, link=device_record['@context'])
                        fiware_wrapper.create_instance(entity_json=device_record, service=fiware_service, link=device_record['@context'])


                    except Exception as e:
                        logger.exception(inspect.currentframe(), e)
                    #delete from new broker
                    #add to new broker

        if key == '2':
            dump_broker(current_broker = os.environ['DEVICE_BROKER'], historic_broker = os.environ['DEVICE_HISTORIC_BROKER'])

        if key == '3':
            #restore_broker(current_broker = os.environ['DEVICE_BROKER'], historic_broker = os.environ['DEVICE_HISTORIC_BROKER'], dump_file = 'broker_2022-08-14 12:34:53.json')
            restore_broker(current_broker=os.environ['DEVICE_BROKER'], historic_broker=os.environ['DEVICE_HISTORIC_BROKER'], dump_file= ar_to_load)

        if key == '4':
            dump_orion_broker(current_broker = os.environ['DEVICE_BROKER'], historic_broker = os.environ['DEVICE_HISTORIC_BROKER'])

        if key == '5':
            dump_broker('http://0.0.0.0:31101')

        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    testbed()
