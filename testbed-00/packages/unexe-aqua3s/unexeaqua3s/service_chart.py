import os

import unexeaqua3s.service
import unexeaqua3s.chartingsupport

import datetime
import unexefiware.debug
import unexefiware.base_logger
import unexefiware.fiwarewrapper
import inspect
import threading
import unexefiware.model
import unexefiware.time
import unexefiware.units
import unexefiware.workertask
import copy
import time
import unexeaqua3s.json
import copy
import sys

import unexeaqua3s.deviceinfo

import zlib
import base64



class Bucketiser:
    def __init__(self):
        self.logger = None
        self.logger = unexefiware.base_logger.BaseLogger()

    def process(self, deviceInfo, device_id, input_bucket, raw_device_data, prop):

        bucket = copy.deepcopy(input_bucket)

        dp = deviceInfo.get_smart_model(device_id).property_get_dp(prop)

        for entry in bucket:
            entry['results'] = {}
            entry['results']['val'] = 0
            entry['results']['count'] = 0
            entry['results']['result'] = None
            entry['results']['min'] = sys.float_info.max
            entry['results']['max'] = sys.float_info.min

        try:
            bucket_index = 1

            for entry in raw_device_data:
                bucket_index = 1

                if 'deviceState' in entry:
                    # gareth -   this is a device model
                    if unexefiware.model.get_property_value(entry, 'deviceState') == 'Green':
                        while entry[prop]['observedAt'] > bucket[bucket_index]['date']:
                            bucket_index += 1

                        if bucket[bucket_index - 1]['results']['max'] < float(entry[prop]['value']):
                            bucket[bucket_index - 1]['results']['max'] = float(entry[prop]['value'])

                        if bucket[bucket_index - 1]['results']['min']  > float(entry[prop]['value']):
                            bucket[bucket_index - 1]['results']['min'] = float(entry[prop]['value'])

                        bucket[bucket_index - 1]['results']['val'] += float(entry[prop]['value'])
                        bucket[bucket_index - 1]['results']['count'] += 1
                else:

                    if isinstance(entry, list) and len(entry) == 2: #this is from stellio
                        self.process_value(bucket, entry[1], float(entry[0]) )

                    if 'value' in entry:
                        # gareth -   this is a giorgos cygnus model

                        if float(entry['value']) < 99999:
                            if entry['observedAt'] >= bucket[bucket_index]['date']:

                                try:
                                    while entry['observedAt'] > bucket[bucket_index]['date']:
                                        bucket_index += 1
                                except Exception as e:
                                    print(str(entry['observedAt']) + ' ' + str(bucket[bucket_index-1]['date']))
                                    return None

                                bucket[bucket_index - 1]['results']['val'] += float(entry['value'])
                                bucket[bucket_index - 1]['results']['count'] += 1

                                if bucket[bucket_index - 1]['results']['max'] < float(entry['value']):
                                    bucket[bucket_index - 1]['results']['max'] = float(entry['value'])

                                if bucket[bucket_index - 1]['results']['min']  > float(entry['value']):
                                    bucket[bucket_index - 1]['results']['min'] = float(entry['value'])
            for entry in bucket:
                if entry['results']['count'] > 0:
                    entry['results']['result'] = round(entry['results']['val'] / entry['results']['count'], dp)

                    entry['results']['val'] = round(entry['results']['val'], dp)
                    entry['results']['result'] = round(entry['results']['max'], dp)

        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e)

        return bucket

    def process_value(self, bucket, date:str, value:float):
        bucket_index = 1

        if value < 99999:
            if date >= bucket[bucket_index]['date']:

                try:
                    while date > bucket[bucket_index]['date']:
                        bucket_index += 1
                except Exception as e:
                    print(str(date) + ' ' + str(bucket[bucket_index - 1]['date']))
                    return None

                bucket[bucket_index - 1]['results']['val'] += value
                bucket[bucket_index - 1]['results']['count'] += 1

                if bucket[bucket_index - 1]['results']['max'] < value:
                    bucket[bucket_index - 1]['results']['max'] = value

                if bucket[bucket_index - 1]['results']['min'] > value:
                    bucket[bucket_index - 1]['results']['min'] = value

    def get_device_property_data(self, prop, raw_device_data):

        data = []
        try:
            for entry in raw_device_data:
                data.append([unexefiware.model.get_property_observedAt(entry, prop), unexefiware.model.get_property_value(entry, prop)])
        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

        return data


chart_modes = ['daily', 'weekly', 'monthly', 'quarterly', 'half-year', 'year']


class ChartService(unexeaqua3s.service.ServiceBase):
    def __init__(self):
        super().__init__()
        self.chartStatus_label = 'ChartStatus'

        self.chartID = self.name_to_fiware_type('1', self.chartStatus_label)

    def name(self):
        return 'ChartService'

    def build_from_deviceInfo(self, deviceInfo:unexeaqua3s.deviceinfo.DeviceInfo2, now:datetime.datetime):
        try:
#            self.logger.log(inspect.currentframe(), 'Start Chart building')
            json_data = {}

            broker = deviceInfo.fiware_wrapper

            global chart_modes

            for period in chart_modes:
                json_data[period] = {}

                time_attribs = self.get_time_attribs(period)
                timewindow = self.get_time_from(time_attribs, now)
                json_data[period]['labels'] = self.create_buckets(time_attribs, timewindow)
                json_data[period]['timestamp'] = '1970-01-01T00:00:00Z'

                for device_id in deviceInfo.deviceInfoList:
                    json_data[period][device_id] = {}
                    props = unexefiware.model.get_controlled_properties(deviceInfo.deviceInfoList[device_id])

                    for prop in props:
                        json_data[period][device_id][prop] = []
                        for value in range(0, len(json_data[period]['labels'])):
                            json_data[period][device_id][prop].append(value + 1000.123)

                    # add data here!
            chart_data = self.create_chart_data('1', json_data)
            broker.delete_instance(chart_data['id'], deviceInfo.fiware_service)

            data_to_write = copy.deepcopy(chart_data)
            data_to_write['status']['value'] = self._chartdata_to_fiware(data_to_write['status']['value'])

            broker.create_instance(data_to_write, deviceInfo.fiware_service)

#            self.logger.log(inspect.currentframe(), 'Charting Packet size:' + str(len(unexeaqua3s.json.dumps(data_to_write))))
#            self.logger.log(inspect.currentframe(), 'Chart building done')

        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e)
            return [500, str(e)]

    def create_chart_data(self, name, json_data):
        fiware_data = {}
        fiware_data['@context'] = 'https://schema.lab.fiware.org/ld/context'
        fiware_data['type'] = self.chartStatus_label
        fiware_data['id'] = self.chartID

        fiware_data['status'] = {'type': 'Property', 'value': unexeaqua3s.json.dumps({'value': json_data})}

        return fiware_data

    def get_chart_data(self, deviceInfo:unexeaqua3s.deviceinfo.DeviceInfo2):
        fiware_data = deviceInfo.fiware_wrapper.get_entity(self.chartID, deviceInfo.fiware_service)

        if fiware_data == []:
            return fiware_data

        fiware_data['status']['value'] = self._chartdata_from_fiware(fiware_data['status']['value'])

        return fiware_data

    def patch_chart_data(self, deviceInfo:unexeaqua3s.deviceinfo.DeviceInfo2, fiware_charting_data:dict):

        data_to_write = copy.deepcopy(fiware_charting_data)
        data_to_write['status']['value'] = self._chartdata_to_fiware(data_to_write['status']['value'])

        deviceInfo.fiware_wrapper.patch_entity(entity_id=self.chartID, json_data={'status': data_to_write['status']}, service=deviceInfo.fiware_service)

        return len(unexeaqua3s.json.dumps(data_to_write))

    def _chartdata_to_fiware(self, data:str):
        return data #disable compression
        return base64.urlsafe_b64encode(zlib.compress(data.encode())).decode('utf8').replace("'", '"')

    def _chartdata_from_fiware(self, data) -> str:
        return data #disable compression
        try:
            return zlib.decompress(base64.urlsafe_b64decode(data)).decode()
        except Exception as e:
            return data

    def process_a_device(self, deviceInfo:unexeaqua3s.deviceinfo.DeviceInfo2, charting_data:dict, device_id:str, current_time:datetime.datetime):
        #get alll the temporal data for a give entity for all the time options and properties
        broker = deviceInfo.fiware_wrapper

        time_attribs = self.get_time_attribs('year',current_time)
        timewindow = self.get_time_from(time_attribs, current_time)

        props = unexefiware.model.get_controlled_properties(deviceInfo.deviceInfoList[device_id])

        raw_device_data = broker.get_temporal(deviceInfo.fiware_service, device_id
                                              , properties=props
                                              , start_date=unexefiware.time.datetime_to_fiware(timewindow[0])
                                              , end_date=unexefiware.time.datetime_to_fiware(timewindow[1]))

        if raw_device_data[0] == 200:
            #for each time window and each property, add stuff
            timelists = ['daily', 'weekly', 'monthly', 'quarterly', 'half-year', 'year']
            #timelists = ['monthly']

            for tm in timelists:
                charting_data[tm]['timestamp'] = unexefiware.time.datetime_to_fiware(current_time)
                time_attribs = self.get_time_attribs(tm,current_time)
                timewindow = self.get_time_from(time_attribs, current_time)

                charting_data[tm]['labels'] = self.create_buckets(time_attribs, timewindow)

                for prop in props:
                    bucketiser = Bucketiser()
                    raw_result = bucketiser.process(deviceInfo, device_id, charting_data[tm]['labels'], raw_device_data[1][prop]['values'], prop)

                    charting_data[tm][device_id][prop] = []

                    for result in raw_result:
                        charting_data[tm][device_id][prop].append(result['results']['result'])

                        
    def update(self, deviceInfo:unexeaqua3s.deviceinfo.DeviceInfo2, write_to_broker:bool=True, force_process:bool=False, force_interday:bool=False, charting_time:datetime.datetime=None):

        update_data = False
        broker = deviceInfo.fiware_wrapper

        try:
#            self.logger.log(inspect.currentframe(), 'Charting Update: ' + deviceInfo.fiware_service)
            t0 = time.perf_counter()

            now = datetime.datetime.now(unexeaqua3s.pilot_timezone.get(deviceInfo.fiware_service)).replace(tzinfo=None)

            if charting_time != None:
                now = charting_time

            fiware_charting_data = self.get_chart_data(deviceInfo)

            if fiware_charting_data == []:
                self.build_from_deviceInfo(deviceInfo,now)
                fiware_charting_data = self.get_chart_data(deviceInfo)

            if fiware_charting_data:
                charting_data = unexeaqua3s.json.loads(fiware_charting_data['status']['value'])['value']
                # gareth -   do the daily update first

                time_diff = (now - unexefiware.time.fiware_to_datetime(charting_data['daily']['timestamp'])).total_seconds() / 60

                for device_id in deviceInfo.deviceInfoList:
                    self.process_a_device(deviceInfo,charting_data,device_id, now)

                update_data = True  # we will write this back to the db

                # now write it back
                text = deviceInfo.fiware_service
                text += ' '
                if update_data == True:

                    fiware_charting_data['status']['value'] = unexeaqua3s.json.dumps({'value': charting_data})

                    if write_to_broker:
                        payload = self.patch_chart_data(deviceInfo, fiware_charting_data)
                        text += 'Charting Packet size:' + str(payload)
                else:
                    text += ' No updates required'

#                self.logger.log(inspect.currentframe(), text + ' Time Taken: ' + str(round(time.perf_counter() - t0,1))+'s')

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

    def get_properties_by_sensor(self, deviceInfo, time_mode, visualiseUNEXE=True):
        data = {}

        t0 = time.perf_counter()
        broker = deviceInfo.fiware_wrapper

        try:
            lookup = self.get_chart_data(deviceInfo)

            if lookup:
                charting_data = unexeaqua3s.json.loads(lookup['status']['value'])['value']

                bucket_list = charting_data[time_mode]['labels']

                data['props'] = []
                data['labels'] = []
                data['tick_interval'] = 1
                time_attribs = self.get_time_attribs(time_mode)
                data['tick_interval'] = time_attribs['tick_interval']

                prop_labels = []

                for entry in bucket_list:
                    data['labels'].append(entry['labels'])

                # gareth -   get props in order
                prop_data = deviceInfo.build_prop_list(visualiseUNEXE)
                for prop in prop_data:
                    prop_labels.append(prop)

                prop_labels = sorted(prop_labels)

                for prop in prop_labels:
                    prop_record = {}
                    prop_record['main_text'] = unexefiware.units.get_property_printname(prop)
                    prop_record['sub_text'] = broker.get_name()
                    prop_record['unit_code'] = prop_data[prop]['unit_code']
                    prop_record['unit_text'] = prop_data[prop]['unit_text']
                    prop_record['tick_interval'] = time_attribs['tick_interval']
                    prop_record['devices'] = []

                    data['props'].append(prop_record)

                    for device_id in prop_data[prop]['devices']:
                        device_record = {}

                        device_record['name'] = deviceInfo.get_smart_model(device_id).sensorName()
                        device_record['values'] = []

                        # get data for device(ID) over period (time_mode)

                        if device_id in charting_data[time_mode]:
                            device_record['values'] = charting_data[time_mode][device_id][prop].copy()
                        else:
                            device_record['values'] = None

                        if time_mode == 'daily' and device_record['values'] != None:
                            index = 0
                            in_data = False
                            start_index = -1

                            while index < len(device_record['values']):

                                if device_record['values'][index] != None:  # is something
                                    if in_data == False:
                                        in_data = True
                                        start_index = index
                                    else:
                                        end_index = index
                                        in_data = True

                                        steps = (index) - (start_index + 1)

                                        diff = (device_record['values'][index] - device_record['values'][start_index])
                                        diff /= steps + 1

                                        for fill_index in range(start_index + 1, index):
                                            a = fill_index - (start_index)
                                            device_record['values'][fill_index] = device_record['values'][start_index] + (diff * a)

                                        start_index = index

                                index += 1

                        prop_record['devices'].append(device_record)

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

        self.logger.log(inspect.currentframe(), 'get_properties_by_sensor() - Time Taken: ' + str(time.perf_counter() - t0))
        return data

    def get_sensor_by_properties(self, deviceInfo, time_mode, prop, visualiseUNEXE = True):
        data = {}
        broker = deviceInfo.fiware_wrapper

        t0 = time.perf_counter()

        time_attribs = self.get_time_attribs(time_mode)

        # add all the properties
        prop_data = deviceInfo.build_prop_list(visualiseUNEXE)
        prop_labels = []
        for entry in prop_data:
            prop_labels.append(entry)

        prop_labels = sorted(prop_labels)

        if prop_data:
            data['prop_data'] = []
            data['device_data'] = []

            for entry in prop_labels:
                data['prop_data'].append({'print_text': prop_data[entry]['print_text']
                                             , 'prop_name': prop_data[entry]['prop_name']})

                # if the prop param is empty from the client, set it to the first prop we have
                if prop == None:
                    prop = entry

            try:
                lookup = self.get_chart_data(deviceInfo)

                if lookup:
                    charting_data = unexeaqua3s.json.loads(lookup['status']['value'])['value']

                    bucket_list = charting_data[time_mode]['labels']
                    time_attribs = self.get_time_attribs(time_mode)

                    # gareth -   there's an inconsistence in Device[prop] names, most are lower case, but UV and pH aren't
                    #           this should address that
                    prop_list = None

                    if prop in prop_data:
                        prop_list = prop_data[prop]
                    else:

                        if prop == 'uv':
                            prop_list = prop_data['UV']

                        if prop == 'ph':
                            prop_list = prop_data['pH']

                    for device_id in prop_list['devices']:
                        device_record = {}
                        data['device_data'].append(device_record)

                        device_label = device_id

                        device_record['name'] = deviceInfo.get_smart_model(device_id).sensorName()

                        device_record['values'] = []
                        device_record['labels'] = []
                        device_record['tick_interval'] = time_attribs['tick_interval']

                        for entry in bucket_list:
                            device_record['labels'].append(entry['labels'])

                        if device_id in charting_data[time_mode]:

                            device_record['values'] = charting_data[time_mode][device_id][prop].copy()

                            charting_support = unexeaqua3s.chartingsupport.ChartingSupport()

                            for value in device_record['values']:
                                if value is not None:
                                    charting_support.add_value(value)

                            device_record['y_plotlines'] = [];
                            device = deviceInfo.get_smart_model(device_id)

                            if device.alertsetting_get_entry('current_max') is not None:
                                device_record['y_plotlines'].append({'color': '#FF0000', 'width': 2, 'value': float(device.alertsetting_get_entry('current_max'))})
                                device_record['y_plotlines'].append({'color': '#FF00FF', 'width': 2, 'value': float(device.alertsetting_get_entry('current_min'))})

                                charting_support.add_value(device.alertsetting_get_entry('current_max'), is_limit=True)
                                charting_support.add_value(device.alertsetting_get_entry('current_min'), is_limit=True)

                            device_record['graph_range'] = charting_support.get_range()



                        else:
                            device_record['values'] = None

                        device_record['main_text'] = device_record['name']  # gareth - use the device name rather than the prop name here
                        device_record['sub_text'] = broker.get_name()
                        device_record['unit_text'] = prop_list['unit_text']

            except Exception as e:
                self.logger.exception(inspect.currentframe(), e)

        self.logger.log(inspect.currentframe(), 'get_sensor_by_properties() - Time Taken: ' + str(time.perf_counter() - t0))
        return data

    def get_time_from(self, time_attribs, starting_date:datetime.datetime):
        starting_date = starting_date.replace(hour=0, minute=0, second=0, microsecond=0)
        starting_date = starting_date - datetime.timedelta(days=int(time_attribs['days']))

        #GARETH - Add 1 day to get the 'current' day's data in the >1day charts
        real_end = starting_date + datetime.timedelta(days=int(time_attribs['days'] +  1.0))

        return [starting_date, real_end]

    def get_time_attribs(self, label, current_time:datetime.datetime=None):
        global chart_modes
        
        if current_time == None:
            #GARETH !?!?!?!? - change this for the viz server
            current_time = datetime.datetime.now()

        if label not in chart_modes:
            raise Exception('Unknown mode: ' + str(label))

        data = {}
        data['days'] = 1  # length of chart
        data['timestep_minutes'] = 60  # timestep
        data['tick_interval'] = 1  # chart x-axis legend interval (for highcharts, how many labels to not print)

        data['mode'] = label

        if data['mode'] == 'daily':
            data['days'] = current_time.hour / 24
            data['timestep_minutes'] = 15
            # data['timestep_minutes'] = 60*4
            data['tick_interval'] = 8
            return data

        if data['mode'] == 'weekly':
            data['days'] = 7
            data['timestep_minutes'] = 60
            data['tick_interval'] = 8 * 3
            return data

        if data['mode'] == 'monthly':
            data['days'] = 28
            data['timestep_minutes'] = 60 * 6
            data['tick_interval'] = (8)
            return data

        if data['mode'] == 'quarterly':
            data['days'] = 28 * 3
            data['timestep_minutes'] = 60 * 12
            data['tick_interval'] = (14)
            return data

        if data['mode'] == 'half-year':
            data['days'] = 28 * 6
            data['timestep_minutes'] = 60 * 24 * 1
            data['tick_interval'] = (14)
            return data

        if data['mode'] == 'year':
            data['days'] = 365
            # data['timestep_minutes'] = (60 * 24 * 1)/3
            data['timestep_minutes'] = (60 * 24 * 1)
            data['tick_interval'] = (28) * 3
            return data

        raise Exception('Unknown mode: ' + str(data['mode']))

    def create_buckets(self, time_attribs, timewindow):

        start_time = timewindow[0]
        end_time = timewindow[1]

        buckets = []

        try:
            while start_time <= end_time:
                record = {}
                record['date'] = unexefiware.time.datetime_to_fiware(start_time)
                record['labels'] = []

                if time_attribs['mode'] == 'daily':
                    record['labels'].append(str(start_time.hour).zfill(2) + ':' + str(start_time.minute).zfill(2))  # TOD

                if time_attribs['mode'] == 'weekly' or time_attribs['mode'] == 'monthly' or time_attribs['mode'] == 'quarterly':
                    record['labels'].append(str(start_time.hour).zfill(2) + ':' + str(start_time.minute).zfill(2))  # TOD
                    record['labels'].append(str(start_time.day).zfill(2) + ':' + str(start_time.month).zfill(2) + ':' + str(start_time.year))  # DOY

                if (time_attribs['mode'] == 'half-year') or (time_attribs['mode'] == 'year'):
                    record['labels'].append(str(start_time.day).zfill(2) + ':' + str(start_time.month).zfill(2) + ':' + str(start_time.year))  # DOY

                buckets.append(record)
                start_time += datetime.timedelta(minutes=time_attribs['timestep_minutes'])

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

        return buckets


def testbed(fiware_service):
    quitApp = False
    current_service = fiware_service

    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service)
    deviceInfo.run()

    while quitApp is False:
        print('aqua3s:' + os.environ['DEVICE_BROKER'] + ' pilot:' + current_service + '\n')

        print('1..Build Charting Data')
        print('2..Update Charting Data')
        print('3..Get properties by sensor')
        print('4..Get sensors by property')
        print('5..Delete charting data')
        print('9..Update DeviceInfo')


        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            chartingService = unexeaqua3s.service_chart.ChartService()
            now = datetime.datetime.now(unexeaqua3s.pilot_timezone.get(deviceInfo.fiware_service)).replace(tzinfo=None)

            chartingService.build_from_deviceInfo(deviceInfo, now)

        if key == '2':
            chartingService = unexeaqua3s.service_chart.ChartService()
            chartingService.update(deviceInfo, write_to_broker=True, force_process=True,force_interday=True)


        if key == '3':
            chartingService = unexeaqua3s.service_chart.ChartService()
            result = chartingService.get_properties_by_sensor(deviceInfo, unexeaqua3s.service_chart.chart_modes[0])

            print(unexeaqua3s.json.dumps(result, indent=4) )

        if key == '4':
            chartingService = unexeaqua3s.service_chart.ChartService()
            result = chartingService.get_sensor_by_properties(deviceInfo, unexeaqua3s.service_chart.chart_modes[3], 'ph')

            #print(unexeaqua3s.json.dumps(result, indent=4) )

        if key == '5':
            chartingService = unexeaqua3s.service_chart.ChartService()

            now = datetime.datetime.now(unexeaqua3s.pilot_timezone.get(deviceInfo.fiware_service)).replace(tzinfo=None)
            chartingService.build_from_deviceInfo(deviceInfo, now)

        if key == '9':
            deviceInfo.run()


        if key == 'x':
            quitApp = True


if __name__ == '__main__':
    testbed('AAA')



