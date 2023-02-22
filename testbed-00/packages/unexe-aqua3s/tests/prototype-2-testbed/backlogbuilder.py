import unexefiware.base_logger
import datetime

import unexefiware.fiwarewrapper
import unexefiware.fiwarewrapper_debug
import unexefiware.base_logger
import unexeaqua3s.brokerdefinition

import unexeaqua3s.resourcebuilder
import unexeaqua3s.fiwareresources
import os

pilot_definition = [
        {'pilot': 'AAA', 'sensor_name': 'TGO0P12AGOP1_1_K_VLP_VLPA001_MFPRE01', 'name': 'P12', 'property': 'pressure', 'source': 'WELL', 'unitcode': 'N23', 'location': [45.84470284, 13.45316127], 'limit': {'normal_min': 50, 'normal_max': 70}},
        {'pilot': 'AAA', 'sensor_name': 'TGO0P12AGOP1_1_K_LIV_FALD001_MFCON01', 'name': 'P12', 'property': 'conductibility', 'source': 'WELL', 'unitcode': 'H61', 'location': [45.84470284, 13.45316127], 'limit': {'normal_min': 200, 'normal_max': 220}},
        {'pilot': 'AAA', 'sensor_name': 'TGO0P12AGOP1_1_K_LIV_FALD001_MFLIV01', 'name': 'P12', 'property': 'level', 'source': 'WELL', 'unitcode': 'MTR', 'location': [45.84470284, 13.45316127], 'limit': {'normal_min': 3, 'normal_max': 5}},
        {'pilot': 'AAA', 'sensor_name': 'TGO0P12AGOP1_1_K_VLP_VLPA001_MFPOR01', 'name': 'P12', 'property': 'level', 'source': 'WELL', 'unitcode': 'm3/h', 'location': [45.84470284, 13.45316127], 'limit': {'normal_min': 3, 'normal_max': 5}},

        {'pilot': 'AAA', 'sensor_name': 'TTS0RANATSN9_3_K_STC_VASC001_MFLIV06', 'name': 'SARDOS', 'property': 'level', 'source': 'CHANNEL', 'unitcode': 'MTR', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 3, 'normal_max': 5}},
        {'pilot': 'AAA', 'sensor_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR05', 'name': 'SARDOS', 'property': 'ph', 'source': 'SPRING', 'unitcode': 'Q30', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 6.95, 'normal_max': 7.2}},
        {'pilot': 'AAA', 'sensor_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR03', 'name': 'SARDOS', 'property': 'turbidity', 'source': 'SPRING', 'unitcode': 'NTU', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 1, 'normal_max': 3}},
        {'pilot': 'AAA', 'sensor_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR04', 'name': 'SARDOS', 'property': 'conductibility', 'source': 'SPRING', 'unitcode': 'H61', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 200, 'normal_max': 220}},
        {'pilot': 'AAA', 'sensor_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR06', 'name': 'SARDOS', 'property': 'uv', 'source': 'SPRING', 'unitcode': 'UV', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 0, 'normal_max': 0.1}},
        {'pilot': 'AAA', 'sensor_name': 'TTS0RANATSN9_3_K_GEN_IMPI001_MFPOR01', 'name': 'SARDOS', 'property': 'discharge', 'source': 'SPRING', 'unitcode': 'm3/h', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 0, 'normal_max': 2}},

        {'pilot': 'AAA', 'sensor_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR03', 'name': 'CAPTAZIONE TIMAVO - RAMO 1', 'property': 'pH', 'source': 'SPRING', 'unitcode': 'Q30', 'location': [45.787659, 13.590759], 'limit': {'normal_min': 6.95, 'normal_max': 7.2}},
        {'pilot': 'AAA', 'sensor_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR04', 'name': 'CAPTAZIONE TIMAVO - RAMO 1', 'property': 'UV', 'source': 'SPRING', 'unitcode': 'UV', 'location': [45.787659, 13.590759], 'limit': {'normal_min': 0, 'normal_max': 0.1}},
        {'pilot': 'AAA', 'sensor_name': 'TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV01', 'name': 'CAPTAZIONE TIMAVO - RAMO 1', 'property': 'level', 'source': 'SPRING', 'unitcode': 'MTR', 'location': [45.787659, 13.590759], 'limit': {'normal_min': 3, 'normal_max': 5}},

        {'pilot': 'AAA', 'sensor_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR02', 'name': 'CAPTAZIONE TIMAVO - RAMO 2', 'property': 'turbidity', 'source': 'SPRING', 'unitcode': 'NTU', 'location': [45.78673, 13.59128], 'limit': {'normal_min': 1, 'normal_max': 3}},
        {'pilot': 'AAA', 'sensor_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR01', 'name': 'CAPTAZIONE TIMAVO - RAMO 2', 'property': 'conductibility', 'source': 'SPRING', 'unitcode': 'H61', 'location': [45.78673, 13.59128], 'limit': {'normal_min': 200, 'normal_max': 220}},
        {'pilot': 'AAA', 'sensor_name': 'TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV02', 'name': 'CAPTAZIONE TIMAVO - RAMO 2', 'property': 'level', 'source': 'SPRING', 'unitcode': 'MTR', 'location': [45.78673, 13.59128], 'limit': {'normal_min': 3, 'normal_max': 5}},

        #{'pilot': 'AAA', 'sensor_name': 'TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV03', 'name': 'CAPTAZIONE TIMAVO - RAMO 3', 'property': 'level', 'source': 'SPRING', 'unitcode': 'MTR', 'location': [45.78673, 13.59128], 'limit': {'normal_min': 3, 'normal_max': 5}},
        {'pilot': 'AAA', 'sensor_name': 'TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV03', 'name': 'CAPTAZIONE TIMAVO - RAMO 3', 'property': 'level', 'source': 'SPRING', 'unitcode': 'MTR', 'location': [45.78773, 13.59228], 'limit': {'normal_min': 3, 'normal_max': 5}},

        {'pilot': 'SVK', 'sensor_name': 'CDGEastpressuredevice', 'name': 'CDGEastpressuredevice', 'location': [42.9025605, 23.8058583], 'property': 'pressure', 'unitcode': 'N23', 'limit': {'normal_min': 50, 'normal_max': 70}},
        {'pilot': 'SOF', 'sensor_name': 'RI1_PRESSURE', 'name': 'RI1', 'location': [42.603111, 23.178722], 'property': 'pressure', 'unitcode': 'N23', 'limit': {'normal_min': 50, 'normal_max': 70}},
        {'pilot': 'EYA', 'sensor_name': 'TH1_PRESSURE', 'name': 'TH1', 'location': [40.628, 22.95], 'property': 'pressure', 'unitcode': 'N23', 'limit': {'normal_min': 50, 'normal_max': 70}},
        {'pilot': 'WBL', 'sensor_name': 'WBL1_PRESSURE', 'name': 'WBL1', 'location': [50.89, 4.34], 'property': 'pressure', 'unitcode': 'N23', 'limit': {'normal_min': 50, 'normal_max': 70}},

        {'pilot': 'GT', 'sensor_name': 'GT1_PRESSURE', 'name': 'GT1', 'location': [50.954, -4.137], 'property': 'pressure', 'unitcode': 'N23', 'limit': {'normal_min': 50, 'normal_max': 70}},

        {'pilot': 'WIS', 'sensor_name': 'WIS1_PRESSURE', 'name': 'WIS1', 'location': [50.814, -4.257], 'property': 'pressure', 'unitcode': 'N23', 'limit': {'normal_min': 50, 'normal_max': 70}},
        {'pilot': 'WIS', 'sensor_name': 'GT1_PRESSURE', 'name': 'GT1', 'location': [50.954, -4.137], 'property': 'pressure', 'unitcode': 'N23', 'limit': {'normal_min': 50, 'normal_max': 70}},
    ]

debug_pilot_definition = [
         {'pilot': 'AAA', 'sensor_name': 'TGO0P12AGOP1_1_K_VLP_VLPA001_MFPRE01', 'name': 'P12', 'property': 'pressure', 'source': 'WELL', 'unitcode': 'N23', 'location': [45.84470284, 13.45316127], 'limit': {'normal_min': 50, 'normal_max': 70}},
         {'pilot': 'AAA', 'sensor_name': 'TGO0P12AGOP1_1_K_LIV_FALD001_MFCON01', 'name': 'P12', 'property': 'conductibility', 'source': 'WELL', 'unitcode': 'H61', 'location': [45.84470284, 13.45316127], 'limit': {'normal_min': 200, 'normal_max': 220}},
         {'pilot': 'AAA', 'sensor_name': 'TGO0P12AGOP1_1_K_LIV_FALD001_MFLIV01', 'name': 'P12', 'property': 'level', 'source': 'WELL', 'unitcode': 'MTR', 'location': [45.84470284, 13.45316127], 'limit': {'normal_min': 3, 'normal_max': 5}},
         {'pilot': 'AAA', 'sensor_name': 'TGO0P12AGOP1_1_K_VLP_VLPA001_MFPOR01', 'name': 'P12', 'property': 'level', 'source': 'WELL', 'unitcode': 'm3/h', 'location': [45.84470284, 13.45316127], 'limit': {'normal_min': 3, 'normal_max': 5}},

         {'pilot': 'AAA', 'sensor_name': 'TTS0RANATSN9_3_K_STC_VASC001_MFLIV06', 'name': 'SARDOS', 'property': 'level', 'source': 'CHANNEL', 'unitcode': 'MTR', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 3, 'normal_max': 5}},
         {'pilot': 'AAA', 'sensor_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR05', 'name': 'SARDOS', 'property': 'ph', 'source': 'SPRING', 'unitcode': 'Q30', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 6.95, 'normal_max': 7.2}},
         {'pilot': 'AAA', 'sensor_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR03', 'name': 'SARDOS', 'property': 'turbidity', 'source': 'SPRING', 'unitcode': 'NTU', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 1, 'normal_max': 3}},
         {'pilot': 'AAA', 'sensor_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR04', 'name': 'SARDOS', 'property': 'conductibility', 'source': 'SPRING', 'unitcode': 'H61', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 200, 'normal_max': 220}},
         {'pilot': 'AAA', 'sensor_name': 'TTS0RANATSN9_3_K_MQL_MISU001_MFPAR06', 'name': 'SARDOS', 'property': 'uv', 'source': 'SPRING', 'unitcode': 'UV', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 0, 'normal_max': 0.1}},
         {'pilot': 'AAA', 'sensor_name': 'TTS0RANATSN9_3_K_GEN_IMPI001_MFPOR01', 'name': 'SARDOS', 'property': 'discharge', 'source': 'SPRING', 'unitcode': 'm3/h', 'location': [45.7911853, 13.58792344], 'limit': {'normal_min': 0, 'normal_max': 2}},

         {'pilot': 'AAA', 'sensor_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR03', 'name': 'CAPTAZIONE TIMAVO - RAMO 1', 'property': 'pH', 'source': 'SPRING', 'unitcode': 'Q30', 'location': [45.787659, 13.590759], 'limit': {'normal_min': 6.95, 'normal_max': 7.2}},
         {'pilot': 'AAA', 'sensor_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR04', 'name': 'CAPTAZIONE TIMAVO - RAMO 1', 'property': 'UV', 'source': 'SPRING', 'unitcode': 'UV', 'location': [45.787659, 13.590759], 'limit': {'normal_min': 0, 'normal_max': 0.1}},
         {'pilot': 'AAA', 'sensor_name': 'TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV01', 'name': 'CAPTAZIONE TIMAVO - RAMO 1', 'property': 'level', 'source': 'SPRING', 'unitcode': 'MTR', 'location': [45.787659, 13.590759], 'limit': {'normal_min': 3, 'normal_max': 5}},

         {'pilot': 'AAA', 'sensor_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR02', 'name': 'CAPTAZIONE TIMAVO - RAMO 2', 'property': 'turbidity', 'source': 'SPRING', 'unitcode': 'NTU', 'location': [45.78673, 13.59128], 'limit': {'normal_min': 1, 'normal_max': 3}},
         {'pilot': 'AAA', 'sensor_name': 'TTS0TIMATSN9_1_K_MQL_MISU001_MFPAR01', 'name': 'CAPTAZIONE TIMAVO - RAMO 2', 'property': 'conductibility', 'source': 'SPRING', 'unitcode': 'H61', 'location': [45.78673, 13.59128], 'limit': {'normal_min': 200, 'normal_max': 220}},
         {'pilot': 'AAA', 'sensor_name': 'TTS0TIMATSN9_1_K_LIV_FIUM001_MFLIV02', 'name': 'CAPTAZIONE TIMAVO - RAMO 2', 'property': 'level', 'source': 'SPRING', 'unitcode': 'MTR', 'location': [45.78673, 13.59128], 'limit': {'normal_min': 3, 'normal_max': 5}},

         #new sensors
         {'pilot': 'AAA', 'sensor_name': 'MIR', 'name': 'MIR Ammonia Sensor', 'property': 'ammonia','source': 'SPRING', 'unitcode': '', 'location': [45.791185,13.587923 ], 'limit':{'normal_min':0.0061, 'normal_max':0.0167}},

         {'pilot': 'AAA', 'sensor_name': 'Sensor_BROMATI', 'name': 'Chromatograph', 'property': 'bromati','source': 'SPRING', 'unitcode': '', 'location': [45.790813,13.589325], 'limit':{'normal_min':0.0, 'normal_max':0.0}},
         {'pilot': 'AAA', 'sensor_name': 'Sensor_BROMURI', 'name': 'Chromatograph', 'property': 'bromuri','source': 'SPRING', 'unitcode': '', 'location': [45.790813,13.589325], 'limit':{'normal_min':0.0, 'normal_max':0.0}},
         {'pilot': 'AAA', 'sensor_name': 'Sensor_CLORATI', 'name': 'Chromatograph', 'property': 'clorati','source': 'SPRING', 'unitcode': '', 'location': [45.790813,13.589325], 'limit':{'normal_min':0.0, 'normal_max':0.0}},
         {'pilot': 'AAA', 'sensor_name': 'Sensor_CLORITI', 'name': 'Chromatograph', 'property': 'cloriti','source': 'SPRING', 'unitcode': '', 'location': [45.790813,13.589325], 'limit':{'normal_min':0.0, 'normal_max':0.0}},
         {'pilot': 'AAA', 'sensor_name': 'Sensor_CLORURI', 'name': 'Chromatograph', 'property': 'cloruri','source': 'SPRING', 'unitcode': '', 'location': [45.790813,13.589325], 'limit':{'normal_min':10.981, 'normal_max':12.2549}},
         {'pilot': 'AAA', 'sensor_name': 'Sensor_FLUORURI', 'name': 'Chromatograph', 'property': 'fluoruri','source': 'SPRING', 'unitcode': '', 'location': [45.790813,13.589325], 'limit':{'normal_min':0.047, 'normal_max':0.0667}},
         {'pilot': 'AAA', 'sensor_name': 'Sensor_FOSFATI', 'name': 'Chromatograph', 'property': 'fosfati','source': 'SPRING', 'unitcode': '', 'location': [45.790813,13.589325], 'limit':{'normal_min':0.0, 'normal_max':0.0}},
         {'pilot': 'AAA', 'sensor_name': 'Sensor_NITRATI', 'name': 'Chromatograph', 'property': 'nitrati','source': 'SPRING', 'unitcode': '', 'location': [45.790813,13.589325], 'limit':{'normal_min':7.0086, 'normal_max':8.4822}},
         {'pilot': 'AAA', 'sensor_name': 'Sensor_NITRITI', 'name': 'Chromatograph', 'property': 'nitriti','source': 'SPRING', 'unitcode': '', 'location': [45.790813,13.589325], 'limit':{'normal_min':0.0, 'normal_max':0.0}},
         {'pilot': 'AAA', 'sensor_name': 'Sensor_SOLFATI', 'name': 'Chromatograph', 'property': 'solfati','source': 'SPRING', 'unitcode': '', 'location': [45.790813,13.589325], 'limit':{'normal_min':8.3366, 'normal_max':11.1019}},

         {'pilot': 'AAA', 'sensor_name': 'Sensor_RI', 'name': 'RISensor', 'property': 'refractiveIndex','source': 'SPRING', 'unitcode': '', 'location': [45.791185,13.587923], 'limit':{'normal_min':0.5287, 'normal_max':1.572}},

         {'pilot': 'AAA', 'sensor_name': 'UNEXE_TEST_103', 'name': '103', 'property': 'Pressure','source': 'SPRING', 'unitcode': '', 'location': [45.643916,13.802638, ], 'limit':{'normal_min':69.96, 'normal_max':70.08}},
         {'pilot': 'AAA', 'sensor_name': 'UNEXE_TEST_2', 'name': '2', 'property': 'flow', 'source': 'SPRING', 'unitcode': '', 'location': [45.647352,13.830895], 'limit':{'normal_min':-1833.37 ,'normal_max':-1718.88}},
         {'pilot': 'AAA', 'sensor_name': 'UNEXE_TEST_28', 'name': '28', 'property': 'flow','source': 'SPRING', 'unitcode': '', 'location': [45.63977,13.782224], 'limit':{'normal_min':473.59 ,'normal_max':474.2}},
         {'pilot': 'AAA', 'sensor_name': 'UNEXE_TEST_32', 'name': '32', 'property': 'flow','source': 'SPRING', 'unitcode': '', 'location': [45.628976,13.799513], 'limit':{'normal_min':541.71 ,'normal_max':541.87}},
         {'pilot': 'AAA', 'sensor_name': 'UNEXE_TEST_76', 'name': '76', 'property': 'Pressure','source': 'SPRING', 'unitcode': '', 'location': [ 45.661797, 13.777806], 'limit':{'normal_min':40.92 ,'normal_max':56.42}},
         {'pilot': 'AAA', 'sensor_name': 'UNEXE_TEST_87', 'name': '87', 'property': 'Pressure','source': 'SPRING', 'unitcode': '', 'location': [45.643063,13.78091], 'limit':{'normal_min':73.07 ,'normal_max':73.36}},
         {'pilot': 'AAA', 'sensor_name': 'UNEXE_TEST_9', 'name': '9', 'property': 'flow','source': 'SPRING', 'unitcode': '', 'location': [45.624498,13.806597], 'limit':{'normal_min':824.86 ,'normal_max':826.21}},
         {'pilot': 'AAA', 'sensor_name': 'UNEXE_TEST_94', 'name': '94', 'property': 'Pressure','source': 'SPRING', 'unitcode': '', 'location': [45.625097, 13.790958], 'limit':{'normal_min':65.7 ,'normal_max':65.82}},

        {'pilot': 'AAA', 'sensor_name': 'UNEXE_TEST_97', 'name': '97', 'property': 'Pressure','source': 'SPRING', 'unitcode': '', 'location': [45.623024, 13.817798], 'limit':{'normal_min':64.59 ,'normal_max':65.58}},
    ]


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

def build_backlog(fiware_wrapper, days = None, timestep = None, all_pilots = True):
    brokerInst = unexeaqua3s.brokerdefinition.BrokerDefinition()
    brokerInst.bulk_patch = True

    print('Building Started')

    print('Erase Broker Content')
    #fiware_wrapper.erase_broker()

    brokerInst.init(fiware_wrapper, run_as_thread=False)

    brokerInst.backlog_in_days = 400
    brokerInst.generation_timestep_mins = 15

    brokerInst.backlog_in_days = days

    if timestep != None:
        brokerInst.generation_timestep_mins = timestep

    print('Build Backlog -Started')

    if all_pilots:
        global pilot_definition
        brokerInst.build_backlog(pilot_definition)
    else:
        global debug_pilot_definition

        brokerInst.build_backlog(debug_pilot_definition)

def patch_backlog(fiware_wrapper, all_pilots = True, bulk_patch = False):
    brokerInst = unexeaqua3s.brokerdefinition.BrokerDefinition()
    brokerInst.bulk_patch = bulk_patch

    brokerInst.init(fiware_wrapper, run_as_thread=False)

    print('patch Backlog -Started')

    now = datetime.datetime.utcnow()
    start = now
    start = start.replace(second=0, microsecond=0)

    if all_pilots:
        global pilot_definition
        brokerInst.new_build_backlog(start, pilot_definition,0,1)
    else:
        global debug_pilot_definition

        fiware_time = unexefiware.time.datetime_to_fiware(start)

        for service in brokerInst.service_list:
            brokerInst.update_devices(service, fiware_time)

