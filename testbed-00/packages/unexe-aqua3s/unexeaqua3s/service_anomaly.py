import unexeaqua3s.service
import unexefiware.fiwarewrapper
import unexefiware.base_logger
import unexeaqua3s.deviceinfo
import unexeaqua3s.json
import datetime
import unexefiware.time
import inspect
import time
import copy


class Bucketiser:
    def __init__(self):
        self.buckets = []

        for i in range(0, 21):
            entry = {}
            entry['results'] = []
            self.buckets.append(entry)

    def timestamp_to_bucket(self, fiware_datetime):
        # return (day of week *3) + (hour/8)
        try:
            date = unexefiware.time.fiware_to_datetime(fiware_datetime)

            index = int(date.strftime('%w')) * 3
            index += int((date.hour) / 8)

            return self.buckets[index]
        except Exception as e:
            logger = unexefiware.base_logger.BaseLogger()
            logger.exception(inspect.currentframe(), e)

    def add(self, value, observedAt):
        self.timestamp_to_bucket(observedAt)['results'].append(value)

    def generate_results(self):
        results = []

        try:
            for bucket in self.buckets:
                record = {}
                record['min'] = 0
                record['max'] = 0
                record['average'] = 0

                if bucket['results']:
                    record['min'] = min(bucket['results'])
                    record['max'] = max(bucket['results'])
                    record['average'] = round(sum(bucket['results']) / len(bucket['results']), 3)

                results.append(record)
        except Exception as e:
            logger = unexefiware.base_logger.BaseLogger()
            logger.exception(inspect.currentframe(), e)

        return results


def create_anomaly_settings(name, fiware_time, data=None):
    fiware_data = {}
    fiware_data['@context'] = 'https://schema.lab.fiware.org/ld/context'
    fiware_data['type'] = unexeaqua3s.deviceinfo.anomalySetting_label
    fiware_data['id'] = unexeaqua3s.service.name_to_fiware_type(name, fiware_data['type'])

    if data == None:
        fiware_data['status'] = {'observedAt': fiware_time, 'type': 'Property', 'value': unexeaqua3s.json.dumps([])}
    else:
        fiware_data['status'] = {'observedAt': fiware_time, 'type': 'Property', 'value': unexeaqua3s.json.dumps(data)}

    return fiware_data

def build_limit(deviceInfo, device_id, fiware_time):

    start_time = '2022-04-01T00:00:00Z'
    end_time = fiware_time

    data = deviceInfo.brokers[unexeaqua3s.deviceinfo.device_label].get_temporal_orion(deviceInfo.service, device_id, start_time, end_time)

    bucketiser = Bucketiser()

    if len(data)> 0 and data[0] != -1:
        for entry in data:
            try:
                if 'value' in entry:
                    bucketiser.add(float(entry['value']), entry['observedAt'])
                else:
                    # gareth - this is for oldie stylee data
                    prop = entry['controlledProperty']['value']
                    bucketiser.add(float(entry[prop]['value']), entry[prop]['observedAt'])
            except Exception as e:
                print(str(inspect.currentframe()) + ' ' + str(e))

    return bucketiser.generate_results()

def is_anomaly(observedAt, setting_value, current_value):

    try:
        date = unexefiware.time.fiware_to_datetime(observedAt)
        index = int(date.strftime('%w')) * 3
        index += int(date.hour / 8)

        return (current_value > setting_value[index]['max']) or (current_value < setting_value[index]['min'])
    except Exception as e:
        pass

    return False

def get_anomaly_range(observedAt, setting_value):
    try:
        date = unexefiware.time.fiware_to_datetime(observedAt)
        index = int(date.strftime('%w')) * 3
        index += int(date.hour / 8)

        return setting_value[index]
    except Exception as e:
        pass

    return []



def get_anomaly_value(fiware_time, setting_value, high_value = True):

    try:
        date = unexefiware.time.fiware_to_datetime(fiware_time)
        index = int(date.strftime('%w')) * 3
        index += int(date.hour / 8)

        if high_value:
            return setting_value[index]['max'] + 0.1
        else:
            return setting_value[index]['min'] -0.1

    except Exception as e:
        pass

    return 0.0



class AnomalyService(unexeaqua3s.service.ServiceBase):
    def __init__(self):
        super().__init__()

    def name(self):
        return 'AnomalyService'

    def status_label(self):
        return unexeaqua3s.deviceinfo.anomalyStatus_label

    def setting_label(self):
        return unexeaqua3s.deviceinfo.anomalySetting_label

    def build_setting_data(self, deviceInfo, device_id, observedAt):

        sensor_name = self.device_id_to_name(device_id)
        fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.utcnow())

        return self.create_anomaly_settings(sensor_name, observedAt, self.build_limit(deviceInfo, device_id, fiware_time))

    def build_from_deviceid(self, deviceInfo, device_id, fiware_time=None):

        if fiware_time == None:
            fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.utcnow())

        try:
            sensor_name = self.device_id_to_name(device_id)

            settings_model = self.create_anomaly_settings(sensor_name, fiware_time, self.build_limit(deviceInfo, device_id, fiware_time))
            status_model = self.create_anomaly_status(sensor_name, fiware_time)

            deviceInfo.brokers[unexeaqua3s.deviceinfo.anomalyStatus_label].delete_instance(status_model['id'], deviceInfo.service)
            deviceInfo.brokers[unexeaqua3s.deviceinfo.anomalySetting_label].delete_instance(settings_model['id'], deviceInfo.service)

            deviceInfo.brokers[unexeaqua3s.deviceinfo.anomalyStatus_label].create_instance(status_model, deviceInfo.service)
            deviceInfo.brokers[unexeaqua3s.deviceinfo.anomalySetting_label].create_instance(settings_model, deviceInfo.service)

            deviceInfo.deviceInfoList[device_id][self.status_label()]['data'] = status_model
            deviceInfo.deviceInfoList[device_id][self.setting_label()]['data'] = settings_model

        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e)

    def build_from_deviceInfo(self, deviceInfo):
        try:
            print('Start Anomaly building')
            t0 = time.perf_counter()

            for device_id in deviceInfo.deviceInfoList:
                args = {'device_id': device_id, 'deviceInfo': deviceInfo}
                self.doWork(self._init_anomaly_model, arguments=args)

            self.wait_to_finish()

            t0 = time.perf_counter() - t0

            print('build_from_deviceInfo() Took: ' + str(t0))

        except Exception as e:
            print(str(inspect.currentframe()) + ' ' + str(e))

        print('Anomaly building done')

    def _init_anomaly_model(self, args):
        try:
            device_id = args['device_id']
            deviceInfo = args['deviceInfo']

            print('_init_anomaly_model()' + ' ' + device_id)

            sensor_name = self.device_id_to_name(device_id)

            fiware_time = deviceInfo.property_observedAt(device_id)

            settings_model = self.create_anomaly_settings(sensor_name, fiware_time, self.build_limit(deviceInfo, device_id, fiware_time))
            status_model = self.create_anomaly_status(sensor_name, fiware_time)

            result = deviceInfo.brokers[unexeaqua3s.deviceinfo.anomalyStatus_label].delete_instance(status_model['id'], deviceInfo.service)

            if result[0] != 200 and result[0] != 404:
                print(str(inspect.currentframe()) + ' ' + str(result[1]))

            result = deviceInfo.brokers[unexeaqua3s.deviceinfo.anomalySetting_label].delete_instance(settings_model['id'], deviceInfo.service)

            if result[0] != 200 and result[0] != 404:
                print(str(inspect.currentframe()) + ' ' + str(result[1]))

            result = deviceInfo.brokers[unexeaqua3s.deviceinfo.anomalyStatus_label].create_instance(status_model, deviceInfo.service)

            if result[0] != 201:
                print(str(inspect.currentframe()) + ' ' + str(result[1]))

            result = deviceInfo.brokers[unexeaqua3s.deviceinfo.anomalySetting_label].create_instance(settings_model, deviceInfo.service)

            if result[0] != 201:
                print(str(inspect.currentframe()) + ' ' + str(result[1]))

        except Exception as e:
            print(str(inspect.currentframe()) + ' ' + str(e))

        self.finish_task()

    def build_limit(self, deviceInfo, device_id, fiware_time):

        start_time = '1970-01-01T00:00:00Z'
        end_time = fiware_time

        data = deviceInfo.brokers[unexeaqua3s.deviceinfo.device_label].get_temporal_orion(deviceInfo.service, device_id, start_time, end_time)

        bucketiser = Bucketiser()

        if data[0] != -1:
            for entry in data:
                try:
                    if 'value' in entry:
                        bucketiser.add(float(entry['value']), entry['observedAt'])
                    else:
                        # gareth - this is for oldie stylee data
                        prop = entry['controlledProperty']['value']
                        bucketiser.add(float(entry[prop]['value']), entry[prop]['observedAt'])
                except Exception as e:
                    print(str(inspect.currentframe()) + ' ' + str(e))

        return bucketiser.generate_results()

    def create_anomaly_status(self, name, fiware_time):
        fiware_data = {}
        fiware_data['@context'] = 'https://schema.lab.fiware.org/ld/context'
        fiware_data['type'] = unexeaqua3s.deviceinfo.anomalyStatus_label
        fiware_data['id'] = self.name_to_fiware_type(name, fiware_data['type'])

        default_payload = {
            'triggered': 'False',
            'reason': 'None',
            'count': '0',
        }

        fiware_data['status'] = {'observedAt': fiware_time, 'type': 'Property', 'value': unexeaqua3s.json.dumps(default_payload)}

        return fiware_data

    def create_anomaly_settings(self, name, fiware_time, data=None):
        fiware_data = {}
        fiware_data['@context'] = 'https://schema.lab.fiware.org/ld/context'
        fiware_data['type'] = unexeaqua3s.deviceinfo.anomalySetting_label
        fiware_data['id'] = self.name_to_fiware_type(name, fiware_data['type'])

        if data == None:
            fiware_data['status'] = {'observedAt': fiware_time, 'type': 'Property', 'value': unexeaqua3s.json.dumps([])}
        else:
            fiware_data['status'] = {'observedAt': fiware_time, 'type': 'Property', 'value': unexeaqua3s.json.dumps(data)}

        return fiware_data

    def process(self, deviceInfo, device_id, observedAt, setting_data, previous_status, current_value):

        result = super().process(deviceInfo,device_id,observedAt,setting_data, previous_status, current_value)

        #this is service specific
        # reading is newer than status
        triggered = 'False'
        reason = 'Nothing at the moment'

        #do stuff here
        date = unexefiware.time.fiware_to_datetime(observedAt)
        index = int(date.strftime('%w')) * 3
        index += int((date.hour) / 8)

        # use index to get min/max values from anomalysetting
        # update anomalystatus

        setting_value = unexeaqua3s.json.loads(result['setting_data']['status']['value'])

        count = 0

        if previous_status:
            status_value = unexeaqua3s.json.loads(previous_status['status']['value'])
            count = int(status_value['count'])

        triggered = 'False'
        reason = 'Fine'


        if (current_value > setting_value[index]['max']) or (current_value < setting_value[index]['min']):
            count += 1
        else:
            count = 0

        if count > 3:
            triggered = 'True'
            reason = 'cur:'
            reason += str(current_value)
            reason += ' min:' + str(setting_value[index]['min'])
            reason += ' max:' + str(setting_value[index]['max'])

            result['diagnostic_text'] += 'out of range: ' + reason
        else:
            reason = ''

            if count == 0:
                reason = 'Fine:' + str(current_value)
                result['diagnostic_text'] += 'In range: ' + str(count) + '/4'
            else:
                reason = 'Warn:' + str(current_value)
                result['diagnostic_text'] += 'Warn: ' + str(count) + '/4'

            reason += ' (min:' + str(setting_value[index]['min'])
            reason += ' max:' + str(setting_value[index]['max'])
            reason += ')'

        # write data here for return
        sensor_name = self.device_id_to_name(device_id)
        result['status_data'] = self.create_anomaly_status(sensor_name, observedAt)

        result['status_data']['status']['value'] = unexeaqua3s.json.loads(result['status_data']['status']['value'])
        result['status_data']['status']['value']['triggered'] = triggered
        result['status_data']['status']['value']['reason'] = reason
        result['status_data']['status']['value']['count'] = str(count)
        result['status_data']['status']['observedAt'] = observedAt

        result['status_data']['status']['value'] = unexeaqua3s.json.dumps(result['status_data']['status']['value'])

        return result


    def update(self, deviceInfo):
        try:
            for device_id in deviceInfo.deviceInfoList:
                result = {}
                result['diagnostic_text'] = ''
                result['status_data'] = self.create_anomaly_status(self.device_id_to_name(device_id), deviceInfo.property_observedAt(device_id))
                result['status_data']['status']['value'] = unexeaqua3s.json.loads(result['status_data']['status']['value'])

                if deviceInfo.hasData(device_id, self.status_label()) == False:
                    self.createOrGetData(deviceInfo, device_id, self.status_label(), deviceInfo.property_observedAt(device_id))

                #do we have new data, i.e. device data is newer than current anomaly status
                if (deviceInfo.hasData(device_id, self.status_label()) == False) or (deviceInfo.property_observedAt(device_id) > deviceInfo.anomaly_observedAt(device_id)):

                    #is the device offline?
                    if deviceInfo.device_status(device_id) == 'Red':
                        result['status_data']['status']['value']['triggered'] = 'True'
                        result['status_data']['status']['value']['reason'] = 'Device State Red'
                        result['status_data']['status']['value'] = unexeaqua3s.json.dumps(result['status_data']['status']['value'])

                        result['diagnostic_text'] = device_id + ' ' + 'is RED'
                    else:
                        #normal processing
                        result = self.process(deviceInfo,
                                              device_id,
                                              deviceInfo.property_observedAt(device_id),
                                              deviceInfo.deviceInfoList[device_id][self.setting_label()]['data'],
                                              deviceInfo.deviceInfoList[device_id][self.status_label()]['data'],
                                              float(deviceInfo.property_value(device_id)))

                    if deviceInfo.hasData(device_id, self.status_label()) == False:
                        # no current status data in broker, so add one - with the correct data
                        deviceInfo.brokers[self.status_label()].create_instance(result['status_data'], deviceInfo.service)
                        deviceInfo.deviceInfoList[device_id][self.status_label()]['data'] = result['status_data']
                    else:

                        result['status_data']['status']['value'] = unexeaqua3s.json.loads(result['status_data']['status']['value'])

                        deviceInfo.anomalystatus_set_entry(device_id, 'triggered', result['status_data']['status']['value']['triggered'])
                        deviceInfo.anomalystatus_set_entry(device_id, 'reason', result['status_data']['status']['value']['reason'])
                        deviceInfo.anomalystatus_set_entry(device_id, 'count', result['status_data']['status']['value']['count'])
                        deviceInfo.anomalystatus_patch(device_id, deviceInfo.property_observedAt(device_id))
                else:
                    #no new device data, just log it
                    result['diagnostic_text'] = device_id + ' ' + 'No recent device data: ' + deviceInfo.property_observedAt(device_id) +' vs. Anomaly:' + deviceInfo.anomaly_observedAt(device_id)

                if self.logger:
                    self.logger.log(inspect.currentframe(), result['diagnostic_text'])
        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e )

        return
        try:

            for device_id in deviceInfo.deviceInfoList:

                diagnostic_text = device_id
                diagnostic_text += ' '

                if deviceInfo.deviceInfoList[device_id][unexeaqua3s.deviceinfo.anomalyStatus_label]['data'] == []:
                    # gareth -  If there's no data for the anomalyStatus, create some
                    #           It suggests that the data has been reset elsewhere
                    if self.logger:
                        text = 'AnomalyService: No data for: ' + deviceInfo.deviceInfoList[device_id][unexeaqua3s.deviceinfo.anomalyStatus_label]['id']
                        text += '\n'
                        text += 'Building new data'

                        diagnostic_text += 'No Anomaly Status Record .. building'

                    self.build_from_deviceid(deviceInfo, device_id)

                else:
                    if deviceInfo.device_status(device_id) == 'Red':
                        # gareth -   what do we do if the device is offline
                        deviceInfo.anomalystatus_set_entry(device_id, 'triggered', 'True')
                        deviceInfo.anomalystatus_set_entry(device_id, 'reason', 'Device State Red')
                        deviceInfo.anomalystatus_patch(device_id, deviceInfo.property_observedAt(device_id))

                        diagnostic_text += 'Device is RED'

                    else:
                        if deviceInfo.property_hasvalue(device_id) and deviceInfo._get_value_data(device_id, unexeaqua3s.deviceinfo.anomalyStatus_label):
                            if deviceInfo.property_observedAt(device_id) > deviceInfo.anomaly_observedAt(device_id):
                                # convert device reading time into anomaly index
                                date = unexefiware.time.fiware_to_datetime(deviceInfo.property_observedAt(device_id))
                                index = int(date.strftime('%w')) * 3
                                index += int((date.hour) / 8)

                                # use index to get min/max values from anomalysetting
                                # update anomalystatus

                                triggered = 'False'
                                reason = 'Fine'
                                count = deviceInfo._get_value_entry(device_id, unexeaqua3s.deviceinfo.anomalyStatus_label, 'count')
                                count = float(count)

                                anomalydata = deviceInfo._get_value_data(device_id, unexeaqua3s.deviceinfo.anomalySetting_label)

                                current_value = float(deviceInfo.property_value(device_id))
                                if (current_value > anomalydata[index]['max']) or (current_value < anomalydata[index]['min']):
                                    count += 1
                                else:
                                    count = 0

                                if count > 3:
                                    triggered = 'True'
                                    reason = 'cur:'
                                    reason += str(current_value)
                                    reason += ' min:' +str(anomalydata[index]['min'])
                                    reason += ' max:'+ str(anomalydata[index]['max'])

                                    diagnostic_text += 'out of range: ' + reason
                                else:
                                    reason = 'Fine:' +str(current_value)
                                    reason += ' (min:' + str(anomalydata[index]['min'])
                                    reason += ' max:' + str(anomalydata[index]['max'])
                                    reason += ')'

                                    diagnostic_text += 'In range: ' + str(count)+'/4'

                                # patch data
                                deviceInfo.anomalystatus_patch(device_id, deviceInfo.property_observedAt(device_id))

                                deviceInfo.anomalystatus_set_entry(device_id, 'triggered', triggered)
                                deviceInfo.anomalystatus_set_entry(device_id, 'reason', reason)
                                deviceInfo.anomalystatus_set_entry(device_id, 'count', str(int(count)))
                                deviceInfo.anomalystatus_patch(device_id, deviceInfo.property_observedAt(device_id))

                if self.logger:
                    self.logger.log(inspect.currentframe(), diagnostic_text)
        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e )

    def create_setting_from_historic_data(self, deviceInfo, device_id, raw_device_data):
        now = datetime.datetime.utcnow()
        min_date = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))

        if raw_device_data != [] and len(raw_device_data) > 10:
            sensor_name = self.device_id_to_name(device_id)

            for entry in raw_device_data:
                if min_date < entry['observedAt']:
                    min_date = entry['observedAt']

            settings_model = self.create_anomaly_settings(sensor_name, min_date, self.build_limit(deviceInfo, device_id, min_date))

            deviceInfo.brokers[self.setting_label()].create_instance(settings_model, deviceInfo.service)
            deviceInfo.deviceInfoList[device_id][self.setting_label()]['data'] = settings_model

    def update2(self, deviceInfo, fiware_time):
        #gareth -   process alerts based on lumpy data
        #           This is called when the a&a service starts and there may be no alert (setting) data present
        #           If there's no setting data, try and build some
        #           If there is setting data, do lumpy historic processing
        #           Do current processing

        try:
            for device_id in deviceInfo.key_list:
                if deviceInfo.deviceInfoList[device_id][self.setting_label()]['data'] == []:
                    #no setting data, let's try and build some
                    raw_device_data = deviceInfo.brokers[unexeaqua3s.deviceinfo.device_label].get_temporal_orion(deviceInfo.service, device_id
                                                                                                                 , '1970-01-01T00:00:00Z'
                                                                                                                 , fiware_time)

                    min_date = fiware_time
                    if raw_device_data != [] and len(raw_device_data) > 10:
                        sensor_name = self.device_id_to_name(device_id)

                        settings_model = self.create_anomaly_settings(sensor_name, fiware_time, self.build_limit(deviceInfo, device_id, fiware_time))

                        deviceInfo.brokers[self.setting_label()].create_instance(settings_model, deviceInfo.service)
                        deviceInfo.deviceInfoList[device_id][self.setting_label()]['data'] = settings_model

                if deviceInfo.deviceInfoList[device_id][self.setting_label()]['data'] != []:
                    #we have some setting data ...
                    self.lumpyprocess_device(deviceInfo, device_id, fiware_time)

                #do regular processing

        except Exception as e:
            if self.logger:
                self.logger.fail(inspect.currentframe(),str(e))
