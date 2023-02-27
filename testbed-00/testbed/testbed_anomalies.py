import local_environment_settings
import os

import unexefiware.base_logger
import unexefiware.fiwarewrapper
import unexefiware.time
import datetime
import unexe_epanet.epanet_fiware
import unexewrapper
import threading
import time

import testbed_fiware
import unexe_epanet.epanet_anomaly_detection

def testbed(fiware_wrapper:unexewrapper, logger:unexefiware.base_logger.BaseLogger, sim_inst:unexe_epanet.epanet_fiware.epanet_fiware, sensor_list:list):
    quitApp = False

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + sim_inst.fiware_service)

        print('\n')
        print('1..Build Anomaly Detection Data')
        print('X..Back')
        print('\n')

        key = input('>')

        if key == 'x':
            quitApp = True

        if key == '1':
            print('Build Detection Data')
            ad = unexe_epanet.epanet_anomaly_detection.epanet_anomaly_detection()
            ad.inp_file = sim_inst.inp_file
            ad.build_anomaly_data(fiware_service= sim_inst.fiware_service, sensors=sensor_list, leak_node_ids=None)
            ad.save_anomaly_data(os.environ['LOAD_LOCAL_ANOMALY_DATA_PATH']+ os.sep + sim_inst.fiware_service+'_')
