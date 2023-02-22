import unexefiware.fiwarewrapper
import unexefiware.base_logger
import unexeaqua3s.deviceinfo
import unexeaqua3s.json
import datetime
import unexefiware.time
import unexeaqua3s.service
import inspect
import copy


def create_alert_settings(name, fiware_time, normal_min, normal_max, logger = None):
    normal_min = float(normal_min)
    normal_max = float(normal_max)

    fiware_data = {}
    fiware_data['@context'] = 'https://schema.lab.fiware.org/ld/context'
    fiware_data['type'] = unexeaqua3s.deviceinfo.alertSetting_label

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


aaa_alert_Settings = [{'device_id': 'urn:ngsi-ld:Device:MIR', 'device_name': 'MIR', 'property': 'ammonia', 'property_print_name': 'ammonia', 'min': 0.003, 'max': 0.037, 'step': 0.00013, 'current_min': 0.005, 'current_max': 0.018, 'active': True, 'triggered': False, 'alert_reason': 'Fine:0.0166 (min:0.005 max:0.018)', 'current_print_value': '0.02 '}
    , {'device_id': 'urn:ngsi-ld:Device:Sensor_BROMATI', 'device_name': 'Sensor_BROMATI', 'property': 'bromati', 'property_print_name': 'bromati', 'min': 0.0, 'max': 0.0, 'step': 0.0, 'current_min': 0.0, 'current_max': 0.0, 'active': True, 'triggered': False, 'alert_reason': 'Fine:0.0 (min:0.0 max:0.0)', 'current_print_value': '0.0 '}
    , {'device_id': 'urn:ngsi-ld:Device:Sensor_BROMURI', 'device_name': 'Sensor_BROMURI', 'property': 'bromuri', 'property_print_name': 'bromuri', 'min': 0.0, 'max': 0.0, 'step': 0.0, 'current_min': 0.0, 'current_max': 0.0, 'active': True, 'triggered': False, 'alert_reason': 'Fine:0.0 (min:0.0 max:0.0)', 'current_print_value': '0.0 '}
    , {'device_id': 'urn:ngsi-ld:Device:Sensor_CLORATI', 'device_name': 'Sensor_CLORATI', 'property': 'clorati', 'property_print_name': 'clorati', 'min': 0.0, 'max': 0.0, 'step': 0.0, 'current_min': 0.0, 'current_max': 0.0, 'active': True, 'triggered': False, 'alert_reason': 'Fine:0.0 (min:0.0 max:0.0)', 'current_print_value': '0.0 '}
    , {'device_id': 'urn:ngsi-ld:Device:Sensor_CLORITI', 'device_name': 'Sensor_CLORITI', 'property': 'cloriti', 'property_print_name': 'cloriti', 'min': 0.0, 'max': 0.0, 'step': 0.0, 'current_min': 0.0, 'current_max': 0.0, 'active': True, 'triggered': False, 'alert_reason': 'Fine:0.0 (min:0.0 max:0.0)', 'current_print_value': '0.0 '}
    , {'device_id': 'urn:ngsi-ld:Device:Sensor_CLORURI', 'device_name': 'Sensor_CLORURI', 'property': 'cloruri', 'property_print_name': 'cloruri', 'min': 4.941, 'max': 26.961, 'step': 0.03597, 'current_min': 9.883, 'current_max': 13.48, 'active': True, 'triggered': False, 'alert_reason': 'Fine:11.627 (min:9.883 max:13.48)', 'current_print_value': '11.63 '}
    , {'device_id': 'urn:ngsi-ld:Device:Sensor_FLUORURI', 'device_name': 'Sensor_FLUORURI', 'property': 'fluoruri', 'property_print_name': 'fluoruri', 'min': 0.021, 'max': 0.147, 'step': 0.00031, 'current_min': 0.042, 'current_max': 0.073, 'active': True, 'triggered': False, 'alert_reason': 'Fine:0.0525 (min:0.042 max:0.073)', 'current_print_value': '0.05 '}
    , {'device_id': 'urn:ngsi-ld:Device:Sensor_FOSFATI', 'device_name': 'Sensor_FOSFATI', 'property': 'fosfati', 'property_print_name': 'fosfati', 'min': 0.0, 'max': 0.0, 'step': 0.0, 'current_min': 0.0, 'current_max': 0.0, 'active': True, 'triggered': False, 'alert_reason': 'Fine:0.0 (min:0.0 max:0.0)', 'current_print_value': '0.0 '}
    , {'device_id': 'urn:ngsi-ld:Device:Sensor_NITRATI', 'device_name': 'Sensor_NITRATI', 'property': 'nitrati', 'property_print_name': 'nitrati', 'min': 3.154, 'max': 18.661, 'step': 0.03023, 'current_min': 6.308, 'current_max': 9.33, 'active': True, 'triggered': False, 'alert_reason': 'Fine:7.1981 (min:6.308 max:9.33)', 'current_print_value': '7.2 '}
    , {'device_id': 'urn:ngsi-ld:Device:Sensor_NITRITI', 'device_name': 'Sensor_NITRITI', 'property': 'nitriti', 'property_print_name': 'nitriti', 'min': 0.0, 'max': 0.0, 'step': 0.0, 'current_min': 0.0, 'current_max': 0.0, 'active': True, 'triggered': False, 'alert_reason': 'Fine:0.0 (min:0.0 max:0.0)', 'current_print_value': '0.0 '}
    , {'device_id': 'urn:ngsi-ld:Device:Sensor_RI', 'device_name': 'Sensor_RI', 'property': 'refractiveIndex', 'property_print_name': 'refractiveIndex', 'min': 0.238, 'max': 3.458, 'step': 0.01253, 'current_min': 0.476, 'current_max': 1.729, 'active': True, 'triggered': False, 'alert_reason': 'Fine:1.1047 (min:0.476 max:1.729)', 'current_print_value': '1.1 '}
    , {'device_id': 'urn:ngsi-ld:Device:Sensor_SOLFATI', 'device_name': 'Sensor_SOLFATI', 'property': 'solfati', 'property_print_name': 'solfati', 'min': 3.751, 'max': 24.424, 'step': 0.04709, 'current_min': 7.503, 'current_max': 12.212, 'active': True, 'triggered': False, 'alert_reason': 'Fine:10.478 (min:7.503 max:12.212)', 'current_print_value': '10.48 '}
    , {'device_id': 'urn:ngsi-ld:Device:TGO0P12AGOP1_1_K_LIV_FALD001_MFCON01', 'device_name': 'TGO0P12AGOP1_1_K_LIV_FALD001_MFCON01', 'property': 'conducibility', 'property_print_name': 'Conductibility(mS/cm)', 'min': 59.503, 'max': 1305.546, 'step': 5.33766, 'current_min': 123.55492, 'current_max': 652.773, 'active': True, 'triggered': False, 'alert_reason': 'Fine:336.37 (min:123.55492 max:652.773)', 'current_print_value': '336.37 mS/cm'}
    , {'device_id': 'urn:ngsi-ld:Device:TGO0P12AGOP1_1_K_LIV_FALD001_MFLIV01', 'device_name': 'TGO0P12AGOP1_1_K_LIV_FALD001_MFLIV01', 'property': 'level', 'property_print_name': 'Level(m)', 'min': 2.282, 'max': 21.912, 'step': 0.06393, 'current_min': 4.563, 'current_max': 10.956, 'active': True, 'triggered': False, 'alert_reason': 'Fine:7.43 (min:4.563 max:10.956)', 'current_print_value': '7.43 m'}
    , {'device_id': 'urn:ngsi-ld:Device:TGO0P12AGOP1_1_K_VLP_VLPA001_MFPOR01', 'device_name': 'TGO0P12AGOP1_1_K_VLP_VLPA001_MFPOR01', 'property': 'level', 'property_print_name': 'Level(m\u00b3/h)', 'min': -42.575, 'max': 2261.248, 'step': 12.15773, 'current_min': -85.149, 'current_max': 1130.624, 'active': True, 'triggered': False, 'alert_reason': 'Fine:0.0 (min:-85.149 max:1130.624)', 'current_print_value': '0 m\u00b3/h'}
    , {'device_id': 'urn:ngsi-ld:Device:TGO0P12AGOP1_1_K_VLP_VLPA001_MFPRE01', 'device_name': 'TGO0P12AGOP1_1_K_VLP_VLPA001_MFPRE01', 'property': 'pressure', 'property_print_name': 'Pressure(mH\u2082O)', 'min': 0.45, 'max': 20.086, 'step': 0.09143, 'current_min': 0.9, 'current_max': 10.043, 'active': True, 'triggered': False, 'alert_reason': 'Fine:1.43 (min:0.9 max:10.043)', 'current_print_value': '1.43 mH\u2082O'}
    , {'device_id': 'urn:ngsi-ld:Device:TTS0RANATSN9_3_K_GEN_IMPI001_MFPOR01', 'device_name': 'TTS0RANATSN9_3_K_GEN_IMPI001_MFPOR01', 'property': 'discharge', 'property_print_name': 'Discharge(m\u00b3/h)', 'min': 0.0, 'max': 5590.464, 'step': 27.95232, 'current_min': 0.0, 'current_max': 2795.232, 'active': True, 'triggered': False, 'alert_reason': 'Fine:1112.5 (min:0.0 max:2795.232)', 'current_print_value': '1112.5 m\u00b3/h'}
    , {'device_id': 'urn:ngsi-ld:Device:TTS0RANATSN9_3_K_MQL_MISU001_MFPAR03', 'device_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR03', 'property': 'turbidity', 'property_print_name': 'Turbidity(NTU)', 'min': 0.0, 'max': 1171.83, 'step': 5.85915, 'current_min': 0.0, 'current_max': 585.915, 'active': True, 'triggered': False, 'alert_reason': 'Fine:1.26 (min:0.0 max:585.915)', 'current_print_value': '1.26 NTU'}
    , {'device_id': 'urn:ngsi-ld:Device:TTS0RANATSN9_3_K_MQL_MISU001_MFPAR04', 'device_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR04', 'property': 'conducibility', 'property_print_name': 'Conductibility(mS/cm)', 'min': 0.0, 'max': 4674.846, 'step': 23.37423, 'current_min': 0.0, 'current_max': 2337.423, 'active': True, 'triggered': False, 'alert_reason': 'Fine:341.42 (min:0.0 max:2337.423)', 'current_print_value': '341.42 mS/cm'}
    , {'device_id': 'urn:ngsi-ld:Device:TTS0RANATSN9_3_K_MQL_MISU001_MFPAR05', 'device_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR05', 'property': 'pH', 'property_print_name': 'pH(pH)', 'min': 0.0, 'max': 19.91, 'step': 0.09955, 'current_min': 0.0, 'current_max': 9.955, 'active': True, 'triggered': False, 'alert_reason': 'Fine:7.67 (min:0.0 max:9.955)', 'current_print_value': '7.67 pH'}
    , {'device_id': 'urn:ngsi-ld:Device:TTS0RANATSN9_3_K_MQL_MISU001_MFPAR06', 'device_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR06', 'property': 'UV', 'property_print_name': 'UV', 'min': 0.0, 'max': 1.958, 'step': 0.00979, 'current_min': 0.0, 'current_max': 0.979, 'active': True, 'triggered': False, 'alert_reason': 'Fine:0.05 (min:0.0 max:0.979)', 'current_print_value': '.05 '}
    , {'device_id': 'urn:ngsi-ld:Device:TTS0RANATSN9_3_K_STC_VASC001_MFLIV06', 'device_name': 'TTS0RANATSN9_3_K_STC_VASC001_MFLIV06', 'property': 'level', 'property_print_name': 'Level(m)', 'min': -0.225, 'max': 4.18, 'step': 0.0254, 'current_min': -0.45, 'current_max': 2.09, 'active': True, 'triggered': False, 'alert_reason': 'Fine:1.57 (min:-0.45 max:2.09)', 'current_print_value': '1.57 m'}
    , {'device_id': 'urn:ngsi-ld:Device:TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV01', 'device_name': 'TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV01', 'property': 'level', 'property_print_name': 'Level(m)', 'min': 0.634, 'max': 6.314, 'step': 0.01888, 'current_min': 1.269, 'current_max': 3.157, 'active': True, 'triggered': False, 'alert_reason': 'Fine:1.86 (min:1.269 max:3.157)', 'current_print_value': '1.86 m'}
    , {'device_id': 'urn:ngsi-ld:Device:TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV02', 'device_name': 'TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV02', 'property': 'level', 'property_print_name': 'Level(m)', 'min': 0.846, 'max': 6.006, 'step': 0.01311, 'current_min': 1.692, 'current_max': 3.003, 'active': True, 'triggered': False, 'alert_reason': 'Fine:2.27 (min:1.692 max:3.003)', 'current_print_value': '2.27 m'}
    , {'device_id': 'urn:ngsi-ld:Device:TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV03', 'device_name': 'TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV03', 'property': 'level', 'property_print_name': 'Level(m)', 'min': 0.41, 'max': 5.896, 'step': 0.02129, 'current_min': 0.819, 'current_max': 2.948, 'active': True, 'triggered': False, 'alert_reason': 'Fine:1.87 (min:0.819 max:2.948)', 'current_print_value': '1.87 m'}
    , {'device_id': 'urn:ngsi-ld:Device:TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR01', 'device_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR01', 'property': 'conducibility', 'property_print_name': 'Conductibility(mS/cm)', 'min': -112.352, 'max': 2196.986, 'step': 13.23196, 'current_min': -224.703, 'current_max': 1098.493, 'active': True, 'triggered': False, 'alert_reason': 'Fine:379.75 (min:-224.703 max:1098.493)', 'current_print_value': '379.75 mS/cm'}
    , {'device_id': 'urn:ngsi-ld:Device:TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR02', 'device_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR02', 'property': 'turbidity', 'property_print_name': 'Turbidity(NTU)', 'min': -1.688, 'max': 33.0, 'step': 0.19875, 'current_min': -3.375, 'current_max': 16.5, 'active': True, 'triggered': False, 'alert_reason': 'Fine:0.84 (min:-3.375 max:16.5)', 'current_print_value': '.84 NTU'}
    , {'device_id': 'urn:ngsi-ld:Device:TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR03', 'device_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR03', 'property': 'pH', 'property_print_name': 'pH(pH)', 'min': 3.195, 'max': 15.62, 'step': 0.0142, 'current_min': 6.39, 'current_max': 7.81, 'active': True, 'triggered': False, 'alert_reason': 'Fine:7.1 (min:6.39 max:7.81)', 'current_print_value': '7.1 pH'}
    , {'device_id': 'urn:ngsi-ld:Device:TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR04', 'device_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR04', 'property': 'UV', 'property_print_name': 'UV', 'min': 0.0, 'max': 0.0, 'step': 0.0, 'current_min': 0.0, 'current_max': 0.0, 'active': True, 'triggered': False, 'alert_reason': 'Fine:0.0 (min:0.0 max:0.0)', 'current_print_value': '0 '}

    , {'device_id': 'urn:ngsi-ld:Device:UNEXE_TEST_1',   'min': 1500.0, 'max': 4600.0}
    , {'device_id': 'urn:ngsi-ld:Device:UNEXE_TEST_2',   'min': -4500.0, 'max': 2700.0}
    , {'device_id': 'urn:ngsi-ld:Device:UNEXE_TEST_76',  'min': 60.0, 'max': 90.0}
    , {'device_id': 'urn:ngsi-ld:Device:UNEXE_TEST_87',  'min': 60.0, 'max': 85.0}
    , {'device_id': 'urn:ngsi-ld:Device:UNEXE_TEST_94',  'min': 40.0, 'max': 85.0}
    , {'device_id': 'urn:ngsi-ld:Device:UNEXE_TEST_97',  'min': 40.0, 'max': 85.0}
    , {'device_id': 'urn:ngsi-ld:Device:UNEXE_TEST_103', 'min': 50.0, 'max': 90.0}
    , {'device_id': 'urn:ngsi-ld:Device:UNEXE_TEST_32',  'min': 0.0, 'max': 900.0}
    , {'device_id': 'urn:ngsi-ld:Device:UNEXE_TEST_9',   'min': 10.0, 'max': 1500.0}
    , {'device_id': 'urn:ngsi-ld:Device:UNEXE_TEST_28',  'min': -100.0, 'max': 1000.0}
]


class AlertService(unexeaqua3s.service.ServiceBase):
    def __init__(self):
        super().__init__()

    def name(self):
        return 'AlertService'

    def status_label(self):
        return unexeaqua3s.deviceinfo.alertStatus_label

    def setting_label(self):
        return unexeaqua3s.deviceinfo.alertSetting_label

    def build_from_deviceInfo(self, deviceInfo, fiware_wrapper):
        try:
            fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.utcnow())

            for device_id in deviceInfo.deviceInfoList:
                self.build_from_deviceid(deviceInfo, device_id)
        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e )

    def build_setting_data(self, deviceInfo, device_id, observedAt):

        sensor_name = self.device_id_to_name(device_id)

        min_value = -100
        max_value = 100

        if deviceInfo.service == 'P2B' or deviceInfo.service == 'AAA':
            global aaa_alert_Settings
            for entry in aaa_alert_Settings:
                if entry['device_id'] == device_id:
                    min_value = entry['min']
                    max_value = entry['max']

        if deviceInfo.service == 'WBL':
            try:
                alert_settings = {'freechlorine': [0.0, 0.18],
                                  'conductivity': [670, 690],
                                  'temperature': [12, 18],
                                  'ph': [8.1, 8.4],
                                  'turbidity': [15, 2000.2],
                                  'orp': [750, 795],
                                  'toc': [0.5, 18],
                                  'uv254': [2, 28]}

                prop = deviceInfo.property_get(device_id).lower()

                min_value = alert_settings[prop][0]
                max_value = alert_settings[prop][1]
            except Exception as e:
                print(str(e))



        return self.create_alert_settings(sensor_name, observedAt, normal_min=min_value, normal_max=max_value)

    def build_from_deviceid(self, deviceInfo, device_id, fiware_time = None):

        if fiware_time == None:
            fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.utcnow())

        try:
            sensor_name = self.device_id_to_name(device_id)

            status_model = self.create_alert_status(sensor_name, fiware_time)
            settings_model = self.create_alert_settings(sensor_name, fiware_time, normal_min=-100, normal_max=100)

            deviceInfo.brokers[unexeaqua3s.deviceinfo.alertStatus_label].delete_instance(status_model['id'], deviceInfo.service)
            deviceInfo.brokers[unexeaqua3s.deviceinfo.alertSetting_label].delete_instance(settings_model['id'], deviceInfo.service)

            deviceInfo.brokers[unexeaqua3s.deviceinfo.alertStatus_label].create_instance(status_model, deviceInfo.service)
            deviceInfo.brokers[unexeaqua3s.deviceinfo.alertSetting_label].create_instance(settings_model, deviceInfo.service)

            deviceInfo.deviceInfoList[device_id][unexeaqua3s.deviceinfo.alertStatus_label]['data'] = status_model
            deviceInfo.deviceInfoList[device_id][unexeaqua3s.deviceinfo.alertSetting_label]['data'] = settings_model

        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e )

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

        if not deviceInfo.device_isEPANET(device_id):
            if current_value > current_max or current_value < current_min:
                triggered = 'True'
                reason = 'Outside of Limits'
                reason += '<br>'

                if current_value > current_max:
                    reason += 'Overtopping'
                else:
                    reason += 'Underbottoming'

                reason += ' '
                reason += str(current_value)
                reason += deviceInfo.property_unitCode_prettyprint(device_id)

                reason += ' '

                if current_value > current_max:
                    reason += '> '
                    reason += str(round(current_max,2))
                    reason += deviceInfo.property_unitCode_prettyprint(device_id)
                else:
                    reason += '< '
                    reason += str(round(current_min,2))
                    reason += deviceInfo.property_unitCode_prettyprint(device_id)

                result['diagnostic_text'] += 'out of range: ' + reason
            else:
                result['diagnostic_text'] += 'In range: ' + reason

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

    def update(self, deviceInfo):

        for device_id in deviceInfo.deviceInfoList:
            result = {}
            result['diagnostic_text'] = ''
            result['status_data'] = self.create_alert_status(self.device_id_to_name(device_id), deviceInfo.property_observedAt(device_id))
            result['status_data']['status']['value'] = unexeaqua3s.json.loads(result['status_data']['status']['value'])

            #do we have new data, i.e. device data is newer than current alert status
            if (deviceInfo.hasData(device_id, self.status_label()) == False) or (deviceInfo.property_observedAt(device_id) > deviceInfo.alertstatus_observedAt(device_id)):
                #is the device offline?
                if deviceInfo.device_status(device_id) == 'Red':
                    result['status_data']['status']['value']['triggered'] = 'True'
                    result['status_data']['status']['value']['reason'] = 'Device State Red'

                    result['diagnostic_text'] = device_id + ' ' + 'is RED'
                    result['status_data']['status']['value'] = unexeaqua3s.json.dumps(result['status_data']['status']['value'])
                else:
                    #normal processing
                    result = self.process(deviceInfo,
                                          device_id,
                                          deviceInfo.property_observedAt(device_id),
                                          deviceInfo.deviceInfoList[device_id][self.setting_label()]['data'],
                                          None,
                                          float(deviceInfo.property_value(device_id)))

                if deviceInfo.hasData(device_id, self.status_label()) == False:
                    #no current status data in broker, so add one - with the correct data
                    deviceInfo.brokers[self.status_label()].create_instance(result['status_data'], deviceInfo.service)
                    deviceInfo.deviceInfoList[device_id][self.status_label()]['data'] = result['status_data']
                else:
                    #patch the existing data
                    result['status_data']['status']['value'] = unexeaqua3s.json.loads(result['status_data']['status']['value'])

                    deviceInfo.alertstatus_set_entry(device_id, 'triggered', result['status_data']['status']['value']['triggered'])
                    deviceInfo.alertstatus_set_entry(device_id, 'reason', result['status_data']['status']['value']['reason'])

                    deviceInfo.alertstatus_patch(device_id, deviceInfo.property_observedAt(device_id))
            else:
                #no new device data, just log it
                result['diagnostic_text'] = device_id + ' ' + 'No recent device data: ' + deviceInfo.property_observedAt(device_id) +' vs. Alert:' + deviceInfo.alertstatus_observedAt(device_id)

            if self.logger:
                self.logger.log(inspect.currentframe(), result['diagnostic_text'])

    def create_alert_status(self, name, fiware_time):
        fiware_data = {}
        fiware_data['@context'] = 'https://schema.lab.fiware.org/ld/context'
        fiware_data['type'] = unexeaqua3s.deviceinfo.alertStatus_label
        fiware_data['id'] = self.name_to_fiware_type(name, fiware_data['type'])

        default_payload = {
            'triggered': 'False',
            'reason': 'None',
        }

        fiware_data['status'] = {'observedAt': fiware_time, 'type': 'Property', 'value': unexeaqua3s.json.dumps(default_payload)}

        return fiware_data

    def create_alert_settings(self,name, fiware_time, normal_min, normal_max):

        normal_min = float(normal_min)
        normal_max = float(normal_max)

        fiware_data = {}
        fiware_data['@context'] = 'https://schema.lab.fiware.org/ld/context'
        fiware_data['type'] = self.setting_label()

        try:
            fiware_data['id'] = self.name_to_fiware_type(name, fiware_data['type'])

            range = normal_max - normal_min
            default_payload = {
                'min': str(round(normal_min/2, 3)),
                'max': str(round(normal_max*2, 3)),
                'step': str(round((range) / 100,5)),
                'current_min': str(round(normal_min, 3)),
                'current_max': str(round(normal_max, 3)),
                'active': 'True',
            }

            fiware_data['status'] = {'observedAt': fiware_time, 'type': 'Property', 'value': unexeaqua3s.json.dumps(default_payload)}
        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e )

        return fiware_data

    def create_setting_from_historic_data(self, deviceInfo, device_id, raw_device_data):

        now = datetime.datetime.utcnow()
        min_date = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))

        min_value = -9000.0
        max_value = 9000.0

        if raw_device_data != [] and len(raw_device_data) > 10:

            # create alert setting data here - if you can
            for entry in raw_device_data:
                value = float(entry['value'])
                if value > max_value:
                    max_value = value

                if value < min_value:
                    min_value = value

                if min_date < entry['observedAt']:
                    min_date = entry['observedAt']

            max_value *= 1.1
            min_value *= 0.9

        if deviceInfo.service == 'P2B':
            global aaa_alert_Settings
            for entry in aaa_alert_Settings:
                if entry['device_id'] == device_id:
                    min_value = entry['min']
                    max_value = entry['max']

        if deviceInfo.service == 'WBL':
            try:
                alert_settings = {'freechlorine': [0.0, 0.18],
                                  'conductivity': [670, 690],
                                  'temperature': [12, 18],
                                  'ph': [8.1, 8.4],
                                  'turbidity': [15, 2000.2],
                                  'orp': [750, 795],
                                  'toc': [0.5, 18],
                                  'uv254': [2, 28]}

                prop = deviceInfo.property_get(device_id).lower()

                min_value = alert_settings[prop][0]
                max_value = alert_settings[prop][1]
            except Exception as e:
                print(str(e))

        sensor_name = self.device_id_to_name(device_id)
        settings_model = self.create_alert_settings(sensor_name, min_date, normal_min=min_value, normal_max=max_value)
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

                        # create alert setting data here - if you can
                        min_value = float('inf')
                        max_value = float('-inf')

                        for entry in raw_device_data:
                            value = float(entry['value'])
                            if value > max_value:
                                max_value = value

                            if value < min_value:
                                min_value = value

                            if min_date > entry['observedAt']:
                                min_date = entry['observedAt']

                        max_value *= 1.1
                        min_value *= 0.9

                        sensor_name = self.device_id_to_name(device_id)
                        settings_model = self.create_alert_settings(sensor_name, min_date, normal_min=min_value, normal_max=max_value)
                        deviceInfo.brokers[self.setting_label()].create_instance(settings_model, deviceInfo.service)
                        deviceInfo.deviceInfoList[device_id][self.setting_label()]['data'] = settings_model

                if deviceInfo.deviceInfoList[device_id][self.setting_label()]['data'] != []:
                    #we have some setting data ...
                    self.lumpyprocess_device(deviceInfo, device_id, fiware_time)

                #do regular processing

        except Exception as e:
            if self.logger:
                self.logger.fail(inspect.currentframe(),str(e))