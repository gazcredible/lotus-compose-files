import unexefiware.fiwarewrapper
import unexefiware.base_logger
import unexefiware.time
import unexefiware.workertask
import unexeaqua3s.deviceinfo

import unexeaqua3s.json
import datetime
import inspect


def name_to_fiware_type(name, type):
    return "urn:ngsi-ld:" + type + ':' + name

def device_id_to_name(name):
    return name[19:]


class ServiceBase(unexefiware.workertask.WorkerTask):
    def __init__(self):
        super().__init__()
        self.logger = unexefiware.base_logger.BaseLogger()

    def name_to_fiware_type(self, name, type):
        return "urn:ngsi-ld:" + type + ':' + name

    def device_id_to_name(self, name):
        return name[19:]

    def build_setting_data(self, deviceInfo, device_id, observedAt):
        raise Exception('build_setting_data not defined')

    def build_status_data(self,deviceInfo,device_id, data):
        raise Exception('build_status_data not defined')

    def build_from_deviceInfo(self,args):
        raise Exception('build_from_deviceInfo not defined')

    def status_label(self):
        raise Exception('status label not defined')

    def setting_label(self):
        raise Exception('setting label not defined')

    def build_from_deviceid(self, deviceInfo, device_id, fiware_time=None):
        raise Exception('build_from_deviceid not defined')

    def lumpyprocess_device(self, deviceInfo, device_id, fiware_time, raw_device_data=None, fiware_start_time='1970-01-01T00:00:00Z'):
        try:
            if raw_device_data == None:
                raw_device_data = deviceInfo.brokers[unexeaqua3s.deviceinfo.device_label].get_temporal_orion(deviceInfo.service, device_id
                                                                                                             , fiware_start_time
                                                                                                             , fiware_time)

            if False:
                device_test = {}
                for device_entry in raw_device_data:
                    if device_entry['observedAt'] not in device_test:
                        device_test[device_entry['observedAt']] = 0

                    device_test[device_entry['observedAt']]+=1

                for entry in device_test:
                    print(entry + ' ' + str(device_test[entry]))


            status_id = deviceInfo.deviceInfoList[device_id][self.status_label()]['id']

            raw_status_data = deviceInfo.brokers[self.status_label()].get_temporal_orion(deviceInfo.service, status_id
                                                                                         , fiware_start_time
                                                                                         , fiware_time)
            status_lookup = {}

            if True:
                for device_entry in raw_device_data:
                    if not unexefiware.time.is_fiware_valid(device_entry['observedAt']):
                        if self.logger:
                            self.logger.fail(inspect.currentframe(), 'Adding device entry Timestamp not valid:' + deviceInfo.service + ':' + device_id + ' ' + device_entry['observedAt'])
                    else:
                        status_lookup[device_entry['observedAt']] = {'patch_me': device_entry}

                for status_entry in raw_status_data:
                    if status_entry['status']['observedAt'] in status_lookup:
                        status_lookup[status_entry['status']['observedAt']] = status_entry
            else:
                for entry in raw_status_data:
                    status_lookup[entry['status']['observedAt']] = entry

                for device_entry in raw_device_data:
                    if device_entry['observedAt'] not in status_lookup:
                        status_lookup[device_entry['observedAt']] = {'patch_me': device_entry}


            patch_data = []

            status_lookup_keylist = sorted(list(status_lookup.keys()))

            previous_status = None
            for entry in status_lookup_keylist:

                #if entry is not valid!!!!
                if not unexefiware.time.is_fiware_valid(entry):
                    if self.logger:
                        self.logger.fail(inspect.currentframe(),'Timestamp not valid:' + deviceInfo.service + ':' + device_id + ' ' + entry)
                else:
                    if 'patch_me' in status_lookup[entry]:
                        current_value = float(status_lookup[entry]['patch_me']['value'])
                        result = self.process(deviceInfo, device_id, entry, setting_data=None, previous_status=previous_status, current_value=current_value)

                        if result['setting_data_created']:
                            # write setting data to broker
                            if unexefiware.time.is_fiware_valid(result['setting_data']['status']['observedAt']):
                                deviceInfo.brokers[self.setting_label()].create_instance(result['setting_data'], deviceInfo.service)
                                deviceInfo.deviceInfoList[device_id][self.setting_label()]['data'] = result['setting_data']

                                if self.logger:
                                    self.logger.log(inspect.currentframe(), result['diagnostic_text'] + ' ' +'Setting Data Created' +  result['setting_data']['status']['observedAt'])
                            else:
                                self.logger.fail(inspect.currentframe(), 'setting_data_created-Timestamp not valid:' + deviceInfo.service + ':' + device_id + ' ' + entry)

                        if result['status_data_created']:
                            # write the data

                            if unexefiware.time.is_fiware_valid(result['setting_data']['status']['observedAt']):
                                if self.logger:
                                    self.logger.log(inspect.currentframe(), deviceInfo.service+':' + result['diagnostic_text'] + ' ' +'Status Data Created' +  result['status_data']['status']['observedAt'])

                                    deviceInfo.brokers[self.status_label()].create_instance(result['status_data'], deviceInfo.service)
                                    deviceInfo.deviceInfoList[device_id][self.status_label()]['data'] = result['status_data']
                                else:
                                    self.logger.fail(inspect.currentframe(), 'status_data_created-Timestamp not valid:' + deviceInfo.service + ':' + device_id + ' ' + entry)
                        else:
                            if unexefiware.time.is_fiware_valid(result['setting_data']['status']['observedAt']):
                                #if self.logger:
                                #    self.logger.log(inspect.currentframe(), deviceInfo.service + ':' + result['diagnostic_text'] + ' ' +'Status Data Patch:' +  result['status_data']['status']['observedAt'])

                                patch_data.append({'status': result['status_data']['status']})
                            else:
                                self.logger.fail(inspect.currentframe(), 'status_data_patch-Timestamp not valid:' + deviceInfo.service + ':' + device_id + ' ' + entry)

                        previous_status = result['status_data']

            if len(patch_data):
                if self.logger:
                    self.logger.log(inspect.currentframe(), deviceInfo.service + ':' + device_id +' Patching data:' + str(len(patch_data))+' entries')

                deviceInfo.brokers[self.status_label()].patch_entity(status_id, patch_data, service=deviceInfo.service)

        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e )

    def lumpyprocess(self, deviceInfo, fiware_time):
        # gareth -   for a device, get all the historic sensor data and compare with historic alert status data
        try:
            for device_id in deviceInfo.key_list:
                if True:
                    self.lumpyprocess_device(deviceInfo,device_id, fiware_time)
                else:
                    raw_device_data = deviceInfo.brokers[unexeaqua3s.deviceinfo.device_label].get_temporal_orion(deviceInfo.service, device_id
                                                                                                                 , '1970-01-01T00:00:00Z'
                                                                                                                 , fiware_time)

                    status_id = deviceInfo.deviceInfoList[device_id][self.status_label()]['id']

                    print(status_id)

                    raw_status_data = deviceInfo.brokers[self.status_label()].get_temporal_orion(deviceInfo.service, status_id
                                                                                                 , '1970-01-01T00:00:00Z'
                                                                                                 , fiware_time)
                    status_lookup = {}

                    for entry in raw_status_data:
                        status_lookup[entry['status']['observedAt']] = entry

                    for device_entry in raw_device_data:
                        if device_entry['observedAt'] not in status_lookup:
                            status_lookup[device_entry['observedAt']] = {'patch_me': device_entry}

                    patch_data = []

                    status_lookup_keylist = sorted(list(status_lookup.keys()))

                    previous_status = None
                    for entry in status_lookup_keylist:

                        if 'patch_me' in status_lookup[entry]:
                            current_value = float(status_lookup[entry]['patch_me']['value'])
                            result = self.process(deviceInfo, device_id, entry, setting_data=None, previous_status = previous_status, current_value=current_value)

                            if result['setting_data_created']:
                                #write setting data to broker
                                deviceInfo.brokers[self.setting_label()].create_instance(result['setting_data'], deviceInfo.service)
                                deviceInfo.deviceInfoList[device_id][self.setting_label()]['data'] = result['setting_data']

                            if result['status_data_created']:
                                #write the data
                                deviceInfo.brokers[self.status_label()].create_instance(result['status_data'], deviceInfo.service)
                                deviceInfo.deviceInfoList[device_id][self.status_label()]['data'] = result['status_data']
                            else:
                                patch_data.append({'status': result['status_data']['status']})

                            previous_status = result['status_data']
                        else:
                            pass #do something with the status data

                    if len(patch_data):
                        deviceInfo.brokers[self.status_label()].patch_entity(status_id, patch_data, service=deviceInfo.service)

        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e )

    def process(self, deviceInfo, device_id, observedAt, setting_data, previous_status, current_value):
        result = {'status_data': None,
                  'diagnostic_text': '',
                  'setting_data': setting_data,
                  'setting_data_created': False,
                  'status_data_created': False
                  }

        result['diagnostic_text'] = device_id
        result['diagnostic_text'] += ' '

        if deviceInfo.deviceInfoList[device_id][self.status_label()]['data'] == None:
            result['status_data_created'] = True

        if result['setting_data'] == None:
            result['setting_data'] = deviceInfo.deviceInfoList[device_id][self.setting_label()]['data']

        if result['setting_data'] == None:
            if self.logger:
                result['diagnostic_text'] += self.name() + 'No Setting Record .. building'

            result['setting_data'] = self.build_setting_data(deviceInfo, device_id, observedAt)
            result['setting_data_created'] = True

        return result

    def createOrGetData(self, deviceInfo, device_id, label, observedAt):
        if deviceInfo.hasData(device_id, label) == False:
            self.build_from_deviceid(deviceInfo, device_id, observedAt)


import time

class MultiprocessorBase:
    def __init__(self):
        self.alert_processor = unexeaqua3s.service_alert.AlertService()
        self.anomaly_processor = unexeaqua3s.service_anomaly.AnomalyService()
        self.chart_processor = unexeaqua3s.service_chart.ChartService()

    def step(self, deviceInfo):
        now = datetime.datetime.utcnow()
        now += datetime.timedelta(hours=24)
        fiware_time = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))

        t0 = time.perf_counter()

        key_list = list(deviceInfo.deviceInfoList.keys())
        key_list = sorted(key_list)

        for device_id in key_list:
            raw_device_data = deviceInfo.brokers[unexeaqua3s.deviceinfo.device_label].get_temporal_orion(deviceInfo.service, device_id
                                                                                                         , '1970-01-01T00:00:00Z'
                                                                                                         , fiware_time)
            if len(raw_device_data) > 10:

                # if no alertSetting -> create alert setting
                if deviceInfo.deviceInfoList[device_id][unexeaqua3s.deviceinfo.alertSetting_label]['data'] == []:
                    self.alert_processor.create_setting_from_historic_data(deviceInfo, device_id, raw_device_data)

                # if no anomalySetting -> create anomaly setting
                if deviceInfo.deviceInfoList[device_id][unexeaqua3s.deviceinfo.anomalySetting_label]['data'] == []:
                    self.anomaly_processor.create_setting_from_historic_data(deviceInfo, device_id, raw_device_data)

                # if alertSetting -> get device data & alert setting data -> process to fill in gaps
                if deviceInfo.deviceInfoList[device_id][unexeaqua3s.deviceinfo.alertSetting_label]['data'] != []:
                    self.alert_processor.lumpyprocess_device(deviceInfo, device_id, fiware_time, raw_device_data)

                # if anomalySetting -> get device data & anomaly setting data -> process to fill in gaps
                if deviceInfo.deviceInfoList[device_id][unexeaqua3s.deviceinfo.anomalySetting_label]['data'] != []:
                    self.anomaly_processor.lumpyprocess_device(deviceInfo, device_id, fiware_time, raw_device_data)

        self.chart_processor.update(deviceInfo)