import datetime

import unexefiware.workertask
import unexefiware.ngsildv1
import unexefiware.model
import unexefiware.base_logger
import unexefiware.units
import unexefiware.device
import unexefiware.fiwarewrapper
import unexefiware.time

import unexeaqua3s.kibanablelog
import unexeaqua3s.anomalies

import inspect
import requests
import unexeaqua3s.json
import time
import os
import copy

epanomaly_status_label = 'epanomaly_status'
epanomaly_setting_label = 'epanomaly_setting'
anomaly_status_label = 'anomaly_status'
anomaly_setting_label = 'anomaly_setting'

alert_status_label = 'alert_status'
alert_setting_label = 'alert_setting'


def name_to_fiware_type(name, type):
    return "urn:ngsi-ld:" + type + ':' + name


invalid_string = 'N/A'
logger = unexeaqua3s.kibanablelog.KibanableLog('DeviceInfo')


def device_id_to_name(name):
    return name[19:]


class DeviceSmartModel:
    def __init__(self, device: dict):
        self.model = copy.deepcopy(device)
        self.deviceState_labels = ['https://uri.fiware.org/ns/data-models#deviceState', 'deviceState']

    def get_fiware(self) -> dict:
        return self.model

    def get_id(self) -> str:
        try:
            return self.get_fiware()['id']
        except Exception as e:
            logger.exception(inspect.currentframe(), e)

        return invalid_string

    def name(self) -> str:
        return self.model['name']['value']

    def sensorName(self) -> str:
        if unexefiware.model.has_property_from_label(self.model, 'sensorName') != None:
            return unexefiware.model.get_property_value(self.model, 'sensorName')

        return device_id_to_name(self.model['id'])

    def isEPANET(self) -> bool:
        if 'epanet_reference' in self.model and len(self.model['epanet_reference']['value']) > 0:
            return True

        return False

    def EPANET_id(self) -> str:
        if self.isEPANET():
            return self.model['epanet_reference']['value']

        return None

    def is_UNEXETEST(self) -> bool:
        return 'UNEXE' in self.name()

    # -----------------------------------------------------------------------------------------------------------------------------
    # base functions for settings & status
    def _isTriggered(self, label: str) -> bool:
        try:

            if label not in self.model:
                return False

            if len(self.model[label]['value']):
                return unexeaqua3s.json.loads(self.model[label]['value'])['triggered'] == 'True'

            # raise Exception('empty packet')
        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)
        return False

    def _observedAt_prettyprint(self, label: str = None) -> str:
        if self.property_observedAt(label) is not invalid_string:
            return unexefiware.time.prettyprint_fiware(self.property_observedAt(label))
        else:
            return invalid_string

    def _reason_prettyprint(self, label) -> str:
        if label in self.model and len(self.model[label]['value']):
            return unexeaqua3s.json.loads(self.model[label]['value'])['reason']

        return invalid_string

    def _get(self, label: str) -> str:
        try:
            if label in self.model:
                data = self.model[label]
                if data != None and 'value' in data and len(data['value']) > 0:
                    return unexeaqua3s.json.loads(data['value'])

        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)

        return None

    def _get_entry(self, label: str, entry: str) -> str:
        try:
            data = self._get(label)
            if data != None and entry in data:
                return data[entry]

        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)

        return None

    def _set_entry(self, label: str, entry: str, value: str):
        try:
            data = self._get(label)

            if data != None:
                data[entry] = value

                settings = self.model[label]
                settings['value'] = unexeaqua3s.json.dumps(data)

        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)

    def _patch(self, fiware_service: str, label: str) -> bool:
        try:
            patch_data = {}
            patch_data[label] = self.model[label]
            fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            result = fiware_wrapper.patch_entity(self.model['id'], patch_data, service=fiware_service)

            return result[0] == 204
        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)

        return False

    def _is_valid(self, fiware_service: str, label: str) -> bool:
        try:
            if label not in self.model:
                return False

            if self.model[label]['value'] == '':
                return False

            return True
        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)

    # -----------------------------------------------------------------------------------------------------------------------------
    # GARETH -   not all the devices use deviceState, some use https://uri.fiware.org/ns/data-models and some use both
    #           need to make the updating a bit more robust
    def deviceState_getlabel(self) -> str:
        for deviceState_label in self.deviceState_labels:
            if deviceState_label in self.model:
                return deviceState_label

        raise Exception('Device:' + self.model['id'] + ' hase no deviceState')

    def deviceState_set(self, value: str) -> str:
        if 'https://uri.fiware.org/ns/data-models#deviceState' in self.model and 'deviceState' in self.model:
            labels = ['https://uri.fiware.org/ns/data-models#deviceState', 'deviceState']

            for deviceState_label in labels:
                self.model[deviceState_label]['value'] = value
        else:
            self.model[self.deviceState_getlabel()]['value'] = value

    def deviceState(self) -> str:

        if 'https://uri.fiware.org/ns/data-models#deviceState' in self.model and 'deviceState' in self.model:
            if self.model['https://uri.fiware.org/ns/data-models#deviceState'] == self.model['deviceState']:
                return self.model['deviceState']['value']
            else:
                'unclear'

        return self.model[self.deviceState_getlabel()]['value']

    def deviceState_patch(self, fiware_service: str):
        try:
            for deviceState_label in self.deviceState_labels:

                if deviceState_label in self.model:
                    patch_data = {}
                    patch_data[deviceState_label] = copy.deepcopy(self.model[deviceState_label])

                    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
                    result = fiware_wrapper.patch_entity(self.model['id'], patch_data, service=fiware_service)

        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)

    def value_patch(self, fiware_service: str, fiware_time: str):
        try:
            patch_data = {}
            patch_data['value'] = copy.deepcopy(self.model['value'])
            patch_data['value']['observedAt'] = fiware_time
            fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            result = fiware_wrapper.patch_entity(self.model['id'], patch_data, service=fiware_service)

        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)

    def property_unitCode(self, prop: str = None):

        if prop in self.model:
            return self.model[prop]['unitCode']

        if 'value' in self.model:
            return self.model['value']['unitCode']

        return invalid_string

    def property_get(self):

        result = unexefiware.model.get_property_from_label(self.model, 'controlledProperty')

        if result != None:
            return result['value']

        if 'controlledProperty' in self.model:
            return self.model['controlledProperty']['value']

        return invalid_string

    def property_hasvalue(self, prop: str = None):

        if prop in self.model:
            return True

        return 'value' in self.model

    def property_get_dp(self, prop=None):

        if self.model['id'] == 'urn:ngsi-ld:Device:MIR':
            return 3

        return 2

    def print_with_dp(self, value: float, prop: str = None) -> str:

        if prop == None:
            prop = self.property_get()

        dp = self.property_get_dp(prop)

        return str(round(float(value), dp))

    def property_prettyprint(self, prop: str = None) -> str:
        if prop == None:
            prop = self.property_get()

        if prop != invalid_string:
            return unexefiware.units.get_property_printname(prop)

        return invalid_string

    def property_unitCode_prettyprint(self, prop: str = None) -> str:
        if prop == None:
            prop = self.property_get()

        return unexefiware.units.get_property_unitcode_printname(self.property_unitCode(prop))

    def property_value(self, prop: str = None):

        if prop == None:
            prop = self.property_get()

        dp = self.property_get_dp(prop)

        if 'value' in self.model:
            value = self.model['value']['value']

            if isinstance(value, str):
                value = float(value)

            return str(round(float(value), dp))

        if self.property_get() != invalid_string:

            result = unexefiware.model.get_property_from_label(self.model, prop)

            if result != None:
                value = result['value']

                if isinstance(value, str):
                    return str(value)

                return str(round(float(value), dp))

        return invalid_string

    def property_value_prettyprint(self, prop=None):
        return self.property_value(prop)

    def property_observedAt(self, prop: str = 'value') -> str:
        if prop in self.model:
            return self.model[prop]['observedAt']
        else:
            return invalid_string

    def property_observedAt_prettyprint(self, prop: str = 'value') -> str:
        if self.property_observedAt(prop) is not invalid_string:
            return unexefiware.time.prettyprint_fiware(self.property_observedAt(prop))
        else:
            return invalid_string

    # -----------------------------------------------------------------------------------------------------------------------------
    # alerts

    def alertsetting_get(self):
        return self._get(alert_setting_label)

    def alertsetting_get_entry(self, entry: str):
        return self._get_entry(alert_setting_label, entry)

    def alertsetting_set_entry(self, entry: str, value: str):
        try:
            data = self.alertsetting_get()

            if data != None:
                data[entry] = value

                settings = self.model['alert_setting']
                settings['value'] = unexeaqua3s.json.dumps(data)

        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)

    def alertsetting_initialise(self, fiware_service: str):
        label = alert_setting_label
        if label in self.model:
            self.model[label]['value'] = unexeaqua3s.json.dumps({"min": "-9999", "max": "9999", "step": "1", "current_min": "-9999", "current_max": "9999", "active": "True"})
            self._patch(fiware_service, label)

    def alertstatus_initialise(self, fiware_service: str):
        label = alert_status_label
        if label in self.model:
            self.model[label]['value'] = unexeaqua3s.json.dumps({"triggered": "False", "reason": "AlertStatus - Initialised"})
            self._patch(fiware_service, label)

    def alertstatus_update_and_patch(self, fiware_service: str) -> bool:
        triggered = 'False'
        reason = 'Nothing at the moment'

        if self._is_valid(fiware_service, alert_status_label) == False:
            self.alertstatus_initialise(fiware_service)

        if self._is_valid(fiware_service, alert_setting_label) == False:
            self.alertsetting_initialise(fiware_service)

        if self._is_valid(fiware_service, alert_setting_label) == False:
            return

        if self.alertsetting_get_entry('active').lower() == 'false':
            triggered = 'False'
            reason = 'User set to inactive'

        else:
            if self.deviceState() == 'Green':
                # do stuff
                device_value = float(self.property_value())

                value_min = float(self.alertsetting_get_entry('current_min'))
                value_max = float(self.alertsetting_get_entry('current_max'))

                if ((device_value > value_max) or (device_value < value_min)):
                    triggered = 'True'
                    reason = 'Outside of Limits'
                    reason += '<br>'

                    if device_value > value_max:
                        reason += 'Overtopping'
                    else:
                        reason += 'Underbottoming'

                    reason += ' '
                    reason += str(device_value)
                    reason += self.property_unitCode_prettyprint()

                    reason += ' '

                    if device_value > value_max:
                        reason += '> '
                        reason += self.print_with_dp(value_max, self.property_get())
                        reason += self.property_unitCode_prettyprint()
                    else:
                        reason += '< '
                        reason += self.print_with_dp(value_min, self.property_get())
                        reason += self.property_unitCode_prettyprint()
                else:
                    reason = 'Fine:' + str(device_value)
                    reason += ' (min:' + self.print_with_dp(value_min, self.property_get())
                    reason += ' max:' + self.print_with_dp(value_max, self.property_get())
                    reason += ')'
                    # reason += ' ' + str(datetime.datetime.utcnow())
            else:
                triggered = 'True'
                reason = 'Device State Red'

        alertstatus = copy.deepcopy(self.model['alert_status'])
        alertstatus['value'] = unexeaqua3s.json.loads(alertstatus['value'])
        alertstatus['value']['triggered'] = triggered
        alertstatus['value']['reason'] = reason
        alertstatus['value'] = unexeaqua3s.json.dumps(alertstatus['value'])

        try:
            patch_data = {}
            patch_data['alert_status'] = alertstatus
            fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            result = fiware_wrapper.patch_entity(self.model['id'], patch_data, service=fiware_service)

            return result[0] == 204
        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)

        return False

    def alertsettings_update_and_patch(self, fiware_service: str, current_min: float, current_max: float, active: bool) -> bool:

        label = 'alert_setting'

        data = copy.deepcopy(self.model[label])
        data['value'] = unexeaqua3s.json.loads(data['value'])

        if float(current_min) < float(current_max):
            data['value']['current_min'] = str(current_min)
            data['value']['current_max'] = str(current_max)
        else:
            data['value']['current_max'] = str(current_min)
            data['value']['current_min'] = str(current_max)

        data['value']['active'] = str(active)
        data['value'] = unexeaqua3s.json.dumps(data['value'])

        try:
            patch_data = {}
            patch_data[label] = data
            fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            result = fiware_wrapper.patch_entity(self.model['id'], patch_data, service=fiware_service)

            return result[0] == 204
        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)

        return False

    def alertstatus_reason_prettyprint(self) -> str:
        return self._reason_prettyprint(alert_status_label)

    def alert_isTriggered(self) -> bool:
        return self._isTriggered(alert_status_label)

    def alert_observedAt(self) -> str:
        return self.property_observedAt()

    def alert_observedAt_prettyprint(self) -> str:
        return self._observedAt_prettyprint(alert_status_label)

    # -----------------------------------------------------------------------------------------------------------------------------
    # anomalies
    def anomalysetting_get(self):
        return self._get(anomaly_setting_label)

    def anomalysetting_initialise(self, fiware_service: str, do_patch: bool = True):
        label = anomaly_setting_label

        if label in self.model:
            data = {}

            data['ranges'] = unexeaqua3s.anomalies.build_limit(fiware_service, self.model, self.anomaly_observedAt())
            data['timelog'] = str(60)

            self.model[label]['value'] = unexeaqua3s.json.dumps(data)

            if do_patch:
                self._patch(fiware_service, label)

    def anomalystatus_initialise(self, fiware_service: str):
        label = anomaly_status_label

        if label in self.model:
            self.model[label]['value'] = unexeaqua3s.json.dumps({"triggered": "False", "reason": "AnomalyStatus - Initialised"})
            self._patch(fiware_service, label)

    def get_anomaly_raw_values(self, fiware_time: str, lerp: bool = False) -> dict:

        try:
            if lerp:
                date = unexefiware.time.fiware_to_datetime(fiware_time)
                start = unexefiware.time.round_time(date, date_delta=datetime.timedelta(hours=8), to='down')
                end = unexefiware.time.round_time(date, date_delta=datetime.timedelta(hours=8), to='up')

                start_index = (int(start.strftime('%w')) * 3) + int(start.hour / 8)
                end_index = (int(end.strftime('%w')) * 3) + int(end.hour / 8)

                diff = ((date - start).total_seconds() / (60 * 60) / 8)

                setting_value = unexeaqua3s.json.loads(self.model['anomaly_setting']['value'])['ranges']

                result = {'min': 0.0, 'max': 0.0, 'average': 0.0}

                dp = self.property_get_dp()

                result['min'] = (float(setting_value[start_index]['min']) * (1 - diff)) + (float(setting_value[end_index]['min']) * diff)
                result['max'] = (float(setting_value[start_index]['max']) * (1 - diff)) + (float(setting_value[end_index]['max']) * diff)
                result['average'] = (float(setting_value[start_index]['average']) * (1 - diff)) + (float(setting_value[end_index]['average']) * diff)

                result['min'] = str(round(result['min'], dp))
                result['max'] = str(round(result['max'], dp))
                result['average'] = str(round(result['average'], dp))

                return result

            else:
                date = unexefiware.time.fiware_to_datetime(fiware_time)
                index = int(date.strftime('%w')) * 3
                index += int(date.hour / 8)

                setting_value = unexeaqua3s.json.loads(self.model['anomaly_setting']['value'])['ranges']

                return setting_value[index]

        except Exception as e:
            logger.exception(inspect.currentframe(), e)

        return {'min': str(0.0), 'max': str(0.0), 'average': str(0.0)}

    # GARETH - return a value that will trigger an anomalt
    def get_anomaly_value(self, fiware_time: str, high_value: bool = True) -> float:
        try:
            data = self.get_anomaly_raw_values(fiware_time, lerp=True)

            if high_value:
                return float(data['max']) * 1.1
            else:
                return float(data['min']) * 0.90

        except Exception as e:
            logger.exception(inspect.currentframe(), e)

        return 0.0

    def anomaly_isTriggered(self) -> bool:
        return self._isTriggered(anomaly_status_label)

    def anomalystatus_reason_prettyprint(self) -> str:
        return self._reason_prettyprint(anomaly_status_label)

    def anomaly_observedAt(self) -> str:
        return self.property_observedAt()

    def anomalysettings_update_and_patch(self, fiware_service: str):
        label = anomaly_setting_label

        data = copy.deepcopy(self.model[label])
        data['value'] = unexeaqua3s.json.loads(data['value'])
        # do stuff to data ..
        data['value'] = unexeaqua3s.json.dumps(data['value'])

        data = copy.deepcopy(self.model[label])

        try:
            patch_data = {}
            patch_data[label] = data
            fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            result = fiware_wrapper.patch_entity(self.model['id'], patch_data, service=fiware_service)

            return result[0] == 204
        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)

        return False

    def anomalystatus_update_and_patch(self, fiware_service: str):
        label = anomaly_status_label

        if self._is_valid(fiware_service, anomaly_status_label) == False:
            self.anomalystatus_initialise(fiware_service)

        if self._is_valid(fiware_service, anomaly_setting_label) == False:
            self.anomalysetting_initialise(fiware_service)

        if self._is_valid(fiware_service, anomaly_setting_label) == False:
            return

        triggered = 'False'
        reason = 'Nothing at the moment'

        if True:  # GARETH - disable for VVQ demo
            pass
        else:
            if self.deviceState() == 'Green':
                # do stuff to data ..
                device_value = float(self.property_value())
                anomaly_range = self.get_anomaly_raw_values(self.property_observedAt(), lerp=True)

                anomaly_max = float(self.print_with_dp(float(anomaly_range['max'])))
                anomaly_min = float(self.print_with_dp(float(anomaly_range['min'])))

                if device_value > anomaly_max or device_value < anomaly_min:
                    triggered = 'True'
                    reason = 'Outside of Limits'
                    reason += '<br>'
                    reason += str(device_value)
                    if device_value > float(anomaly_range['max']):
                        reason += ' > ' + str(anomaly_max)
                    else:
                        reason += ' < ' + str(anomaly_min)

                else:
                    reason = 'Fine:' + str(device_value)
            else:
                triggered = 'True'
                reason = 'Device State Red'

        anomalystatus = copy.deepcopy(self.model[label])
        anomalystatus['value'] = unexeaqua3s.json.loads(anomalystatus['value'])
        anomalystatus['value']['triggered'] = triggered
        anomalystatus['value']['reason'] = reason
        anomalystatus['value'] = unexeaqua3s.json.dumps(anomalystatus['value'])

        try:
            patch_data = {}
            patch_data[label] = anomalystatus
            fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            result = fiware_wrapper.patch_entity(self.model['id'], patch_data, service=fiware_service)

            return result[0] == 204
        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)

        return False

    def anomalysetting_patch(self, fiware_service: str) -> bool:
        return self._patch(fiware_service, anomaly_setting_label)

    def anomalysetting_set_entry(self, entry: str, value: str):
        self._set_entry(anomaly_setting_label, entry, value)

    # -----------------------------------------------------------------------------------------------------------------------------
    # epanomalies

    def epanomalysetting_get(self):
        return self._get(epanomaly_setting_label)

    def epanomalysetting_get_entry(self, entry: str):
        return self._get_entry(epanomaly_setting_label, entry)

    def epanomalysetting_set_entry(self, entry: str, value: str):
        self._set_entry(epanomaly_setting_label, entry, value)

    def epanomalystatus_get_entry(self, entry: str):
        self._get_entry(epanomaly_status_label, entry)

    def epanomalystatus_set_entry(self, entry: str, value: str):
        self._set_entry(epanomaly_status_label, entry, value)

    def epanomaly_isTriggered(self) -> bool:
        return self._isTriggered(epanomaly_status_label)

    def epanomaly_observedAt_prettyprint(self) -> str:
        return self._observedAt_prettyprint(epanomaly_status_label)

    def epanomaly_observedAt(self) -> str:
        return self.property_observedAt()

    def epanomalystatus_reason_prettyprint(self) -> str:
        return self._reason_prettyprint(epanomaly_status_label)

    def epanomalysettings_update_and_patch(self, fiware_service: str):
        label = epanomaly_setting_label

        data = copy.deepcopy(self.model[label])
        data['value'] = unexeaqua3s.json.loads(data['value'])
        # do stuff to data ..
        data['value'] = unexeaqua3s.json.dumps(data['value'])

        data = copy.deepcopy(self.model[label])

        try:
            patch_data = {}
            patch_data[label] = data
            fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            result = fiware_wrapper.patch_entity(self.model['id'], patch_data, service=fiware_service)

            return result[0] == 204
        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)

        return False

    def epanomaly_fudge_setting(self, fiware_serivce: str, state: bool):
        try:
            label = 'epanomaly_setting'

            data = copy.deepcopy(self.model[label])
            if len(data['value']):
                data['value'] = unexeaqua3s.json.loads(data['value'])
            else:
                data['value'] = {}
            data['value']['fudge_state'] = str(state)
            data['value'] = unexeaqua3s.json.dumps(data['value'])

            self.model[label]['value'] = data['value']

            return self.epanomalysettings_update_and_patch(fiware_serivce)

        except Exception as e:
            if logger:
                logger.exception(inspect.currentframe(), e)

        return False

    def epanomalystatus_is_valid(self) -> bool:
        label = 'epanomaly_status'

        if self.isEPANET():
            status = self._get(label)

            if status:
                if 'triggered' not in status:
                    return False

                if 'reason' not in status:
                    return False

                return True

        return False

    def epanomalystatus_set_with_defaults(self, fiware_service: str) -> bool:

        label = 'epanomaly_status'

        if self.isEPANET():
            status = self._get(label)

            if status:
                if 'triggered' not in status:
                    status['triggered'] = str(False)

                if 'reason' not in status:
                    status['reason'] = 'Fine: Initial Setup'

                self.model[label]['value'] = unexeaqua3s.json.dumps(status)

                try:
                    patch_data = {}
                    patch_data[label] = self.model[label]
                    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
                    result = fiware_wrapper.patch_entity(self.model['id'], patch_data, service=fiware_service)

                    return result[0] == 204
                except Exception as e:
                    if logger:
                        logger.exception(inspect.currentframe(), e)

        return False

    def epanomalysetting_reset(self):
        label = 'epanomaly_setting'

        data = self.model[label]
        data['value'] = unexeaqua3s.json.loads(data['value'])
        data['value'] = {}
        data['value'] = unexeaqua3s.json.dumps(data['value'])

    def epanomalystatus_reset(self):
        label = 'epanomaly_status'

        data = self.model[label]
        data['value'] = unexeaqua3s.json.loads(data['value'])
        data['value'] = {}
        data['value'] = unexeaqua3s.json.dumps(data['value'])

    def epanomalysetting_is_valid(self) -> bool:
        label = 'epanomaly_setting'

        if self.isEPANET():
            settings = self.epanomalysetting_get()
            if 'ewma_value' not in settings:
                return False

            if 'threshold' not in settings:
                return False

            if 'fudge_state' not in settings:
                return False

            return True

        return False

    def epanomalysetting_set_with_defaults(self, fiware_service: str) -> bool:

        label = 'epanomaly_setting'

        if self.isEPANET():
            settings = self._get(label)
            if 'ewma_value' not in settings:
                settings['ewma_value'] = '0.0'

            if 'threshold' not in settings:
                settings['threshold'] = '0.0'

            if 'fudge_state' not in settings:
                settings['fudge_state'] = str(False)

            self.model[label]['value'] = unexeaqua3s.json.dumps(settings)

            try:
                patch_data = {}
                patch_data[label] = self.model[label]
                fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
                result = fiware_wrapper.patch_entity(self.model['id'], patch_data, service=fiware_service)

                return result[0] == 204
            except Exception as e:
                if logger:
                    logger.exception(inspect.currentframe(), e)

        return False

    def epanomalystatus_patch(self, fiware_service: str) -> bool:
        return self._patch(fiware_service, epanomaly_status_label)

    def epanomalysetting_patch(self, fiware_service: str) -> bool:
        return self._patch(fiware_service, epanomaly_setting_label)


class DeviceInfo2(unexefiware.workertask.WorkerTask):

    def __init__(self, fiware_service: str):
        super().__init__()
        self.session = None
        self.deviceInfoList = {}
        self.debug_mode = False

        self.fiware_service = fiware_service
        self.logger = unexefiware.base_logger.BaseLogger()

        self.execution_time = 0

        self.fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])

    def get_model_from_fiware(self, device_id: str) -> dict:
        try:
            result = self.fiware_wrapper.get_entity(entity_id=device_id, service=self.fiware_service)

            if type(result) is dict:
                return unexeaqua3s.deviceinfo.DeviceSmartModel(result)
        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

        return None

    def get_historic(self, device: DeviceSmartModel, fiware_start_time: str, fiware_end_time: str) -> list:
        try:
            return self.fiware_wrapper.get_temporal_orion(self.fiware_service, device.model['id'], fiware_start_time=fiware_start_time, fiware_end_time=fiware_end_time)
        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

        return []

    def run(self):
        try:
            self.deviceInfoList = {}
            self.deviceModelList = {}
            self.session = requests.session()

            # GARETH - put this into fiwarewrapper class
            result = unexefiware.ngsildv1.get_all_orion(requests.session(), self.fiware_wrapper.url, 'Device', link=self.fiware_wrapper.link, fiware_service=self.fiware_service)

            if result[0] == 200:
                for entry in result[1]:
                    self.deviceInfoList[entry['id']] = entry

                    self.deviceModelList[entry['id']] = DeviceSmartModel(entry)
            else:
                if self.logger:
                    self.logger.log(inspect.currentframe(), self.fiware_service + ':' + str(result))


        except Exception as e:
            if self.logger:
                self.logger.log(inspect.currentframe(), self.fiware_service)
                self.logger.exception(inspect.currentframe(), e)

        self.execution_time = time.perf_counter() - self.execution_time

    def get_smart_model(self, device_id: str) -> DeviceSmartModel:
        return self.deviceModelList[device_id]

    def update_and_patch(self):
        for entry in self.deviceModelList:
            self.deviceModelList[entry].alertstatus_update_and_patch(self.fiware_service)

    def alertsettings_update_and_patch(self, device_id: str, current_min: float, current_max: float):
        self.deviceModelList[device_id].alertsettings_update_and_patch(current_min, current_max)

    def get_EPANET_sensors(self):
        key_list = []

        for entry in self.deviceModelList:
            if self.deviceModelList[entry].isEPANET():
                key_list.append(entry)

        key_list = sorted(key_list)

        return key_list

    def is_leaky(self):
        for entity in self.deviceModelList:
            device = self.deviceModelList[entity]

            if device.isEPANET() and device.epanomaly_isTriggered():
                return True

        return False

    def device_get(self, device_id) -> DeviceSmartModel:
        try:
            return self.deviceModelList[device_id].model
        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e)

        return None

    def property_observedAt(self, device_id, prop=None):
        try:
            device = self.device_get(device_id)

            value = ''

            if 'value' in device:
                value = device['value']['observedAt']
            else:
                if self.property_get(device_id) != invalid_string:

                    result = unexefiware.model.get_property_from_label(device, self.property_get(device_id))

                    if result != None:
                        value = result['observedAt']

            if value != '':
                return unexefiware.time.datetime_to_fiware(unexefiware.time.fiware_to_datetime(value))

        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e)

        return invalid_string

    def build_prop_list(self, visualiseUNEXE=True):

        prop_data = {}

        try:
            for device_id in self.deviceInfoList:

                device = self.get_smart_model(device_id)

                if (visualiseUNEXE == True) or (not device.is_UNEXETEST() and visualiseUNEXE == False):

                    props = unexefiware.model.get_controlled_properties(device.model)

                    for prop in props:
                        # 20220218 - gareth - got some issues with case in prop labels
                        prop = prop.lower()

                        if prop not in prop_data:
                            prop_data[prop] = {}
                            prop_data[prop]['devices'] = []

                            # gareth - not all the devices are generating data at the moment ...
                            if device.property_unitCode(prop) != invalid_string:
                                prop_data[prop]['unit_code'] = device.property_unitCode(prop)
                                prop_data[prop]['unit_text'] = device.property_unitCode_prettyprint(prop)
                            else:
                                prop_data[prop]['unit_code'] = invalid_string
                                prop_data[prop]['unit_text'] = invalid_string

                            prop_data[prop]['prop_name'] = prop
                            prop_data[prop]['print_text'] = device.property_prettyprint(prop)

                        # gareth - so see if we can find a prop with labels
                        if device.property_unitCode(prop) != invalid_string:
                            prop_data[prop]['unit_code'] = device.property_unitCode(prop)
                            prop_data[prop]['unit_text'] = device.property_unitCode_prettyprint(prop)

                        prop_data[prop]['devices'].append(device_id)

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

        return prop_data

    def get_alert_data_for_giota(self):

        data = {}
        data['alerts'] = {}
        data['alerts']['device'] = []

        data['anomalies'] = {}
        data['anomalies']['device'] = []

        data['epanomalies'] = {}
        data['epanomalies']['device'] = []

        try:
            for device_id in self.deviceModelList:
                device = self.deviceModelList[device_id]

                if device.alert_isTriggered():
                    data['alerts']['device'].append({'reason': device.alertstatus_reason_prettyprint().replace('<br>', ' ')
                                                        , 'property': device.property_prettyprint()
                                                        , 'source_id': device_id
                                                        , 'timestamp': device.alert_observedAt()}
                                                    )
                if device.anomaly_isTriggered():
                    data['anomalies']['device'].append({'reason': device.anomalystatus_reason_prettyprint().replace('<br>', ' ')
                                                           , 'property': device.property_prettyprint()
                                                           , 'source_id': device_id
                                                           , 'timestamp': device.anomaly_observedAt()}
                                                       )

                if device.epanomaly_isTriggered():
                    data['epanomalies']['device'].append({'reason': device.epanomalystatus_reason_prettyprint().replace('<br>', ' ')
                                                             , 'property': device.property_prettyprint()
                                                             , 'source_id': device_id
                                                             , 'timestamp': device.epanomaly_observedAt()}
                                                         )
        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

        return data


# --------------------------------------------------------------------------------------------------------------------------

def testbed(fiware_service: str):
    logger = unexefiware.base_logger.BaseLogger()