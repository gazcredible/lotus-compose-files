import datetime
import os
import unexeaqua3s.json
import inspect
import copy

import unexefiware.fiwarewrapper
import unexefiware.fiwarewrapper_debug
import unexefiware.base_logger
import unexefiware.time

import unexeaqua3s.deviceinfo
import unexeaqua3s.visualiser
import unexeaqua3s.service_anomaly
import unexeaqua3s.webdav

import pandas
import io

class EPAnomalies:
    def __init__(self, fiware_service:str, logger:unexefiware.base_logger.BaseLogger = None):
        self.fiware_service = fiware_service

        self.collect_data_results = []
        self.anomaly_modelData = {}
        self.time_window_in_days = 31

        self.logger = logger
        if self.logger == None:
            self.logger = unexefiware.base_logger.BaseLogger()

    def load_data(self):

        if False:
            try:
                path_root = os.environ['FILE_PATH'] + os.sep + os.environ['FILE_VISUALISER_FOLDER'] + os.sep + 'data' + os.sep + self.fiware_service + os.sep + 'epanet_anomaly'
                self.anomaly_modelData['avg_values_DB'] = pandas.read_pickle(path_root + os.sep + "avg_values")
            except Exception as e:
                self.logger.exception(inspect.currentframe(),e)

        try:
            webdav_options = {
                'webdav_hostname': os.environ['WEBDAV_URL'],
                'webdav_login': os.environ['WEBDAV_NAME'],
                'webdav_password': os.environ['WEBDAV_PASS']
            }

            file_path = 'kr_10' + os.sep + 'data' + os.sep + self.fiware_service + os.sep + 'epanet_anomaly' + os.sep + "avg_values"

            webdav = unexeaqua3s.webdav.webdav(options=webdav_options)

            #webdav.print_remote_tree(root='/')
            try:
                info = webdav.client.resource(file_path)
                buffer = io.BytesIO()
                info.write_to(buffer)
                buffer.seek(0,0)
                self.anomaly_modelData['avg_values_DB'] = pandas.read_pickle(buffer)
            except Exception as e:
                pass

        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

    def process_device(self, fiware_service:str, device:unexeaqua3s.deviceinfo.DeviceSmartModel):
        try:
            if device is not None and device.isEPANET():
                if device.epanomalystatus_is_valid() == False:
                    device.epanomalystatus_set_with_defaults(fiware_service)

                if device.epanomalystatus_is_valid() == True:
                    device_id_simple = device.EPANET_id()
                    avg_valuesDB = self.anomaly_modelData['avg_values_DB'][self.anomaly_modelData['avg_values_DB'].Sensor_ID == device_id_simple]

                    alpha = 0.9
                    L = 5.4
                    threshold = L * ((alpha / (2 - alpha)) ** 0.5)

                    if device.epanomalysetting_is_valid() == False:
                        device.epanomalysetting_set_with_defaults(fiware_service)
                        # GARETH - Brett said to do this
                        current_ewma = 0
                    else:
                        prev_ewma = float(device.epanomalysetting_get_entry('ewma_value'))
                        next_read = float(device.property_value())

                        current_ewma = self.calc_ewma(device.property_observedAt(), next_read, prev_ewma, alpha, avg_valuesDB)

                    if abs(current_ewma) > threshold:
                        # print(current_ewma)
                        triggered = 'True'  # i.e. an alarm
                        reason = 'Surpasses_Threshold'
                        reason += ' cur.reading: '+ str(round(next_read,2) )
                        reason += ' prev ewma: ' + str(round(prev_ewma,2))
                        reason += ' curr. ewma: ' +str(round(current_ewma,2))
                        reason += ' thresh: ' +str(round(threshold,2))
                    else:
                        triggered = 'False'
                        reason = 'None'

                    if device.epanomalysetting_get_entry('fudge_state') == 'True':
                        triggered = 'True'
                        reason = 'Outside of Limits by fudge_state'

                    #debug info
                    reason += ' ' + str(datetime.datetime.utcnow().replace(microsecond=0))

                    device.epanomalystatus_set_entry('triggered', str(triggered))
                    device.epanomalystatus_set_entry('reason', str(reason))

                    device.epanomalysetting_set_entry('ewma_value', str(current_ewma))
                    device.epanomalysetting_set_entry('threshold', str(threshold))

                    device.epanomalystatus_patch(fiware_service)
                    device.epanomalysetting_patch(fiware_service)

                    print(device.get_id() + ' ' + reason)
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

        return

    def get_device_prop_value(self, device_id_simple:str, fiware_time:str, in_range:bool=True) -> float:
        try:
            avg_valuesDB = self.anomaly_modelData['avg_values_DB'][self.anomaly_modelData['avg_values_DB'].Sensor_ID == device_id_simple]

            rounded_time = unexefiware.time.round_time(dt=unexefiware.time.fiware_to_datetime(fiware_time), date_delta=datetime.timedelta(minutes=15), to='up')

            week_time = rounded_time.strftime("%A-%H:%M")
            # get avg. value
            avg_value = avg_valuesDB.Read_avg[avg_valuesDB.timestamp == week_time]
            avg_value = avg_value.iloc[0]
            # get std
            std_value = avg_valuesDB.Read_std[avg_valuesDB.timestamp == week_time]
            std_value = std_value.iloc[0]

            if in_range == False:
                return avg_value *99999

            return avg_value
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

        return 0

    def calc_ewma(self, observed_date:str, current_value:float, prev_ewma:float, alpha:float, avg_valuesDB) ->float:
        #collect std, avg for time step

        rounded_time = unexefiware.time.round_time(dt=unexefiware.time.fiware_to_datetime(observed_date), date_delta=datetime.timedelta(minutes=15), to='up')

        week_time = rounded_time.strftime("%A-%H:%M")
        #get avg. value
        avg_value = avg_valuesDB.Read_avg[avg_valuesDB.timestamp == week_time]
        avg_value = avg_value.iloc[0]
        #get std
        std_value = avg_valuesDB.Read_std[avg_valuesDB.timestamp == week_time]
        std_value = std_value.iloc[0]
        z = (current_value - avg_value)/std_value
        ewma = (1 - alpha) * prev_ewma + alpha * z
        return ewma


    def build_anomaly_settings(self, fiware_service:str):
        deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service)
        deviceInfo.run()

        self.load_data()

        for device_id in deviceInfo.deviceModelList:
            device = deviceInfo.get_smart_model(device_id)

            try:
                if device.isEPANET():
                    device_id_simple = device.EPANET_id()
                    avg_valuesDB = self.anomaly_modelData['avg_values_DB'][self.anomaly_modelData['avg_values_DB'].Sensor_ID == device_id_simple]

                    print(device_id)

                    if device_id == 'urn:ngsi-ld:Device:UNEXE_TEST_2':
                        print()

                    bucketiser = unexeaqua3s.service_anomaly.Bucketiser()

                    for index, row in avg_valuesDB.iterrows():
                        date_string  = row['timestamp'].replace(':','-').split('-')

                        base_date = datetime.datetime.strptime('2021-01-01',"%Y-%m-%d")

                        time_add = 0

                        #GARETH- is sunday actually the first day of the avg_valuesDB week?
                        #first day of week is FRIDAY, from anomaly_detection_class:62, uses 2021-01-01 (friday)

                        if date_string[0] == 'Sunday':
                            time_add += 24*60*2

                        if date_string[0] == 'Monday':
                            time_add += 24*60*3

                        if date_string[0] == 'Tuesday':
                            time_add += 24*60*4

                        if date_string[0] == 'Wednesday':
                            time_add += 24*60*5

                        if date_string[0] == 'Thursday':
                            time_add += 24*60*6

                        if date_string[0] == 'Friday':
                            time_add += 24*60*0

                        if date_string[0] == 'Saturday':
                            time_add += 24*60*1

                        time_add += float(date_string[1])*60
                        time_add += float(date_string[2])

                        base_date += datetime.timedelta(minutes=time_add)

                        fiware_time = unexefiware.time.datetime_to_fiware(base_date)

                        bucketiser.add(row['Read_avg'], fiware_time)
                        #bucketiser.add(row['Read_avg'] + (4 * row['Read_std']), fiware_time)
                        #bucketiser.add(row['Read_avg'] - (4 * row['Read_std']), fiware_time)

                    results = bucketiser.generate_results()

                    dp = 2

                    for entry in results:
                        entry['min'] = str(round(float(entry['min']), dp))
                        entry['max'] = str(round(float(entry['max']), dp))
                        entry['average'] = str(round(float(entry['average']), dp))

                    device.anomalysetting_set_entry('ranges', results)
                    device.anomalysetting_patch(fiware_service)
            except Exception as e:
                self.logger.exception(inspect.currentframe(), e)
