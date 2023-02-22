import inspect

import unexeaqua3s.service
import unexefiware.fiwarewrapper
import unexefiware.base_logger
import unexeaqua3s.deviceinfo
import unexeaqua3s.json
import unexefiware.time
import copy

class AnomalyServiceEPAnet(unexeaqua3s.service.ServiceBase):
    def __init__(self):
        super().__init__()

    def name(self):
        return 'AnomalyService_EPAnet'

    def status_label(self):
        return unexeaqua3s.deviceinfo.anomalyStatusEPAnet_label

    def process_epanetAnomalies(self, device_id, deviceInfo, fiware_time, avg_valuesDB,historic_device_reads):
        try:
            # 1. check original anomaly status - grab last reading with an anomaly status
            alpha = 0.9
            L = 5.4
            threshold = L * ((alpha / (2 - alpha)) ** 0.5)
            sensor_name = self.device_id_to_name(device_id)

            if deviceInfo.hasData(device_id, self.status_label()) == False:
            # no current status data in broker, so add one - with the correct data
                #1. grab earliest device read:
                first_read = historic_device_reads[0]
                prev_ewma = 0
                current_ewma = self.calc_ewma(first_read, prev_ewma, alpha, avg_valuesDB)
                current_ewma = 0 #set first value to zero (initial value is somewhat screwy)
                if abs(current_ewma) > threshold:
                    triggered = 'True' #i.e. an alarm
                    reason = 'Surpasses_Threshold'
                else:
                    triggered = 'False'
                    reason = 'None'

                payload = {
                    'triggered': triggered,
                    'ewma_value': str(current_ewma),
                    'threshold' : str(threshold),
                    'reason': reason
                }


                settings_model = self.create_epanetAnomalyStatus(sensor_name, fiware_time = first_read['observedAt'], payload = payload) #create first anomaly status
                #create anomaly instance
                deviceInfo.brokers[self.status_label()].create_instance(settings_model, deviceInfo.service)
                deviceInfo.deviceInfoList[device_id][self.status_label()]['data'] = settings_model


            # do we have new data, i.e. device data is newer than current anomaly status

            patch_list = []

            while deviceInfo.property_observedAt(device_id) > deviceInfo.anomalyEPAnet_observedAt(device_id):
            #if  deviceInfo.property_observedAt(device_id) > deviceInfo.anomaly_observedAt(device_id):
                prev_ewma = float(deviceInfo._get_value_data(device_id, self.status_label())['ewma_value'])
                next_read = self.get_next_device_read(historic_device_reads, deviceInfo.anomalyEPAnet_observedAt(device_id))
                current_ewma = self.calc_ewma(next_read, prev_ewma, alpha, avg_valuesDB)

                if abs(current_ewma) > threshold:
                    #print(current_ewma)
                    triggered = 'True'  # i.e. an alarm
                    reason = 'Surpasses_Threshold'
                else:
                    triggered = 'False'
                    reason = 'None'

                payload = {
                    'triggered': str(triggered),
                    'ewma_value': str(current_ewma),
                    'threshold': str(threshold),
                    'reason': reason
                }

                settings_model = self.create_epanetAnomalyStatus(sensor_name, fiware_time=next_read['observedAt'], payload=payload)  # create first anomaly status
                model_values = unexeaqua3s.json.loads(settings_model['status']['value'])

                deviceInfo.anomalyEPAnetstatus_set_entry(device_id, 'triggered', model_values['triggered'])
                deviceInfo.anomalyEPAnetstatus_set_entry(device_id, 'ewma_value', model_values['ewma_value'])
                deviceInfo.anomalyEPAnetstatus_set_entry(device_id, 'threshold', model_values['threshold'])
                deviceInfo.anomalyEPAnetstatus_set_entry(device_id, 'reason', model_values['reason'])

                status_data = copy.deepcopy(deviceInfo.deviceInfoList[device_id][unexeaqua3s.deviceinfo.anomalyStatusEPAnet_label]['data']['status'])
                status_data['observedAt'] = next_read['observedAt']
                patch_list.append({'status': status_data})
                #deviceInfo.anomalyEPAnetstatus_patch(device_id, next_read['observedAt'])

                deviceInfo.deviceInfoList[device_id][unexeaqua3s.deviceinfo.anomalyStatusEPAnet_label]['data']['status']['observedAt'] = next_read['observedAt']

            if len(patch_list) > 0:

                epanetanomaly_label = unexeaqua3s.deviceinfo.anomalyStatusEPAnet_label
                status_id = deviceInfo.deviceInfoList[device_id][epanetanomaly_label]['data']['id']
                fiware_service = deviceInfo.service

                deviceInfo.brokers[epanetanomaly_label].patch_entity(status_id, patch_list, service=fiware_service)

        except Exception as e:
            logger = unexefiware.base_logger.BaseLogger()
            logger.exception(inspect.currentframe(), e)

    def get_next_device_read(self,historic_device_reads, last_anomaly_observedAt):
        current_read_index = next((i for i, device_read in enumerate(historic_device_reads) if device_read["observedAt"] == last_anomaly_observedAt), None)
        next_read = historic_device_reads[current_read_index+1]
        return next_read


    def create_epanetAnomalyStatus(self, sensor_name, fiware_time, payload):
        result = {}
        result['diagnostic_text'] = ''

        #fiware context
        fiware_data = {}
        fiware_data['@context'] = 'https://schema.lab.fiware.org/ld/context'
        fiware_data['type'] = unexeaqua3s.deviceinfo.anomalyStatusEPAnet_label
        fiware_data['id'] = self.name_to_fiware_type(sensor_name, fiware_data['type'])

        fiware_data['status'] = {'observedAt': fiware_time, 'type': 'Property', 'value': unexeaqua3s.json.dumps(payload)}
        return fiware_data


    def calc_ewma(self, read, prev_ewma, alpha, avg_valuesDB):
        #collect std, avg for time step
        observed_date = unexefiware.time.fiware_to_datetime(read['observedAt'])
        week_time = observed_date.strftime("%A-%H:%M")
        #get avg. value
        avg_value = avg_valuesDB.Read_avg[avg_valuesDB.timestamp == week_time]
        avg_value = avg_value.iloc[0]
        #get std
        std_value = avg_valuesDB.Read_std[avg_valuesDB.timestamp == week_time]
        std_value = std_value.iloc[0]
        z = (float(read['value']) - avg_value)/std_value
        ewma = (1 - alpha) * prev_ewma + alpha * z
        return ewma


import os
import time
import pandas as pd
import unexeaqua3s.workhorse_backend

class HistoricData(unexefiware.workertask.WorkerTask):
    def __init__(self):
        super().__init__()
        self.debug_mode = False
        self.collect_data_results = []
        self.anomaly_modelData = {}

    def collect_anomaly_webdavData(self,fiware_service):
        path_root = os.environ['FILE_PATH'] + os.sep + os.environ['FILE_VISUALISER_FOLDER'] +os.sep + 'data' +os.sep + fiware_service + os.sep + 'epanet_anomaly'
        self.anomaly_modelData['avg_values_DB'] = pd.read_pickle(path_root + os.sep +"avg_values")


    def collectData(self, deviceInfo, fiware_time):
        t0 = time.perf_counter()

        key_list = list(deviceInfo.deviceInfoList.keys())
        key_list = sorted(key_list)

        self.collect_data_results = []

        for device_id in key_list:
            args = {}
            args['deviceInfo'] = deviceInfo
            args['device_id'] = device_id
            args['fiware_time'] = fiware_time

            self.doWork(self._collect_data_task, arguments=args)

        self.wait_to_finish()

        print('Took: ' + str(time.perf_counter() - t0))

    def _collect_data_task(self, args):
        deviceInfo = args['deviceInfo']
        device_id = args['device_id']
        fiware_time = args['fiware_time']

        raw_device_data = deviceInfo.brokers[unexeaqua3s.deviceinfo.device_label].get_temporal_orion(deviceInfo.service, device_id
                                                                                                     , '1980-01-01T00:00:00Z'
                                                                                                     , fiware_time)

        self.collect_data_results.append(device_id.ljust(60, ' ') + ' ' + str(len(raw_device_data)).ljust(6, ' '))

        self.finish_task()

    def processEPAnetAnomalies(self, deviceInfo, fiware_time, fiware_service):
        t0 = time.perf_counter()
        key_list = list(deviceInfo.deviceInfoList.keys())
        if fiware_service == 'TTT': #these sensors use epanet anomaly detection

            key_list = []
            if True: #GARETH code - i've added an 'epanet_reference' to the device entity
                key_list = deviceInfo.get_EPANET_sensors()
            else:
                #GARETH FIX THIS! - get all the devices and filter out all the UNEXE ones
                 epanet_device_ids = {'urn:ngsi-ld:Device:1','urn:ngsi-ld:Device:2','urn:ngsi-ld:Device:76','urn:ngsi-ld:Device:87',
                                      'urn:ngsi-ld:Device:94', 'urn:ngsi-ld:Device:97', 'urn:ngsi-ld:Device:103', 'urn:ngsi-ld:Device:32',
                                      'urn:ngsi-ld:Device:9', 'urn:ngsi-ld:Device:28'}
                 key_list= [x for x in key_list if x in epanet_device_ids] #keep keys only within list of epanet devices

        key_list = deviceInfo.get_EPANET_sensors()
        key_list = sorted(key_list)

        self.collect_data_results = []

        for device_id in key_list:
            if deviceInfo.device_isEPANET(device_id):
                args = {}
                args['deviceInfo'] = deviceInfo
                args['device_id'] = device_id
                args['fiware_time'] = fiware_time

                self._processEPAnetAnomalies(args=args)
                #self.doWork(self._processEPAnetAnomalies, arguments=args)

        # charting_processor = unexeaqua3s.service_chart.ChartService()
        # charting_processor.update(deviceInfo)

        #self.wait_to_finish()

        print('Took: ' + str(time.perf_counter() - t0))

    def get_device_avg_values(self, device_id):
        #GARETH FIX this! - strip UNEXE devices to epanet index
        device_id_simple = device_id.replace("urn:ngsi-ld:Device:", "")
        avg_valuesDB = self.anomaly_modelData['avg_values_DB'][self.anomaly_modelData['avg_values_DB'].Sensor_ID == device_id_simple]
        return avg_valuesDB

    def _processEPAnetAnomalies(self, args):
        deviceInfo = args['deviceInfo']
        device_id = args['device_id']
        fiware_time = args['fiware_time']

        print('doing:' + device_id)

        #get historic device data
        historic_device_reads = deviceInfo.brokers[unexeaqua3s.deviceinfo.device_label].get_temporal_orion(deviceInfo.service, device_id
                                                                                                     , '1980-01-01T00:00:00Z'
                                                                                                     , fiware_time)
        if len(historic_device_reads) > 1:
            avg_valuesDB = None
            if True: #GARETH
                device_id_simple = deviceInfo.device_EPANET_id(device_id)
                avg_valuesDB = self.anomaly_modelData['avg_values_DB'][self.anomaly_modelData['avg_values_DB'].Sensor_ID == device_id_simple]
            else:
                avg_valuesDB = self.get_device_avg_values(device_id)

            anomalyEPAnet_processor = unexeaqua3s.service_anomaly_epanet.AnomalyServiceEPAnet()
            #do anomaly process
            anomalyEPAnet_processor.process_epanetAnomalies(device_id, deviceInfo, fiware_time, avg_valuesDB, historic_device_reads)
        self.finish_task()



import unexeaqua3s.service_alert
class DubiousEPAnomaly(unexeaqua3s.service_alert.AlertService):
    def __init__(self):
        super().__init__()

    def name(self):
        return 'EPAnomalyService'

    def status_label(self):
        return unexeaqua3s.deviceinfo.anomalyStatusEPAnet_label

    def setting_label(self):
        return unexeaqua3s.deviceinfo.gareths_dodgy_epasetting

    def create_alert_status(self, name, fiware_time):
        fiware_data = {}
        fiware_data['@context'] = 'https://schema.lab.fiware.org/ld/context'
        fiware_data['type'] = self.status_label()
        fiware_data['id'] = self.name_to_fiware_type(name, fiware_data['type'])

        default_payload = {
            'triggered': 'True',
            'reason': 'Because I can',
        }

        fiware_data['status'] = {'observedAt': fiware_time, 'type': 'Property', 'value': unexeaqua3s.json.dumps(default_payload)}

        return fiware_data

    def process(self, deviceInfo, device_id, observedAt, setting_data, previous_status, current_value):

        result = super().process(deviceInfo,device_id,observedAt,setting_data,previous_status, current_value)

        #this is service specific
        # reading is newer than status
        triggered = 'False'
        reason = 'Nothing at the moment'

        setting_value = unexeaqua3s.json.loads(result['setting_data']['status']['value'])

        current_max = float(setting_value['current_max'])
        current_min = float(setting_value['current_min'])

        reason = 'Fine:' + str(current_value)
        reason += ' (min:' + str(current_min)
        reason += ' max:' + str(current_max)
        reason += ')'

        #simDeviceInfo = unexeaqua3s.simdeviceinfo.SimDeviceInfo(deviceInfo.service, device_wrapper=deviceInfo.device_wrapper, other_wrapper=deviceInfo.other_wrapper)
        #simDeviceInfo.run()

        anomaly_result = unexeaqua3s.workhouse_backend.get_device_anomaly_text(device_id)

        triggered = anomaly_result['triggered']
        reason = anomaly_result['reason']
        result['diagnostic_text'] += 'out of range: ' + reason

        #write data here for return
        sensor_name = self.device_id_to_name(device_id)
        result['status_data'] = self.create_alert_status(sensor_name, observedAt)

        result['status_data']['status']['value'] = unexeaqua3s.json.loads(result['status_data']['status']['value'])
        result['status_data']['status']['value']['triggered'] = triggered
        result['status_data']['status']['value']['reason'] = reason
        result['status_data']['status']['observedAt'] = observedAt

        result['status_data']['status']['value'] = unexeaqua3s.json.dumps(result['status_data']['status']['value'])

        #if result['status_data']['status']['value']['triggered'] == True:
        #mail someone and let them know :)

        return result



def create_DubiousEPAnomaly_settings(name, fiware_time, normal_min, normal_max, logger = None):
    normal_min = float(normal_min)
    normal_max = float(normal_max)

    fiware_data = {}
    fiware_data['@context'] = 'https://schema.lab.fiware.org/ld/context'
    fiware_data['type'] = 'EPAnomalySetting'

    try:
        fiware_data['id'] = unexeaqua3s.service.name_to_fiware_type(name, fiware_data['type'])

        range = normal_max - normal_min
        default_payload = {
            'min': str(round(normal_min / 2, 3)),
            'max': str(round(normal_max * 2, 3)),
            'step': str(round((range) / 100, 5)),
            'current_min': str(round(normal_min, 3)),
            'current_max': str(round(normal_max, 3)),
            'active': 'True',
        }

        fiware_data['status'] = {'observedAt': fiware_time, 'type': 'Property', 'value': unexeaqua3s.json.dumps(default_payload)}
    except Exception as e:
        if logger:
            logger.exception(inspect.currentframe(), e)

    return fiware_data

