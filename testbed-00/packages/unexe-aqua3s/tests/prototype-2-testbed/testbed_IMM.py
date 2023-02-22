import os

import unexeaqua3s.service_alert
import unexeaqua3s.service_anomaly
import unexeaqua3s.epanet_data_generator

import unexefiware.fiwarewrapper
import unexefiware.fiwarewrapper_debug
import unexefiware.base_logger
import unexefiware.time

import unexeaqua3s.deviceinfo
import unexeaqua3s.IMM_PI

import numpy as np
import datetime
import inspect

import unexeaqua3s.immwrapper_mo

import resourcemanager
import unexefiware.model

def inp_file_location(fiware_wrapper, fiware_service):

    if 'WEBDAV_URL' not in os.environ:
        raise Exception('Webdav not defined')

    options = {
        'webdav_hostname':  os.environ['WEBDAV_URL'],
        'webdav_login': os.environ['WEBDAV_NAME'],
        'webdav_password': os.environ['WEBDAV_PASS']
    }

    resource_manager = resourcemanager.ResouceManager(options=options)
    fiware_service_list = [fiware_service]
    resource_manager.init(url=os.environ['USERLAYER_BROKER'], file_root=os.environ['FILE_PATH']+'/visualiser', fiware_service_list=fiware_service_list)
    resource_manager.has_loaded_content = True

    try:
        water_network = resource_manager.resources[fiware_service]['epanet']
        inp_file = water_network.epanetmodel.inp_file
        return inp_file
    except Exception as e:
        print('Pilot has no water network!')
        return

    #simulation_model = unexeaqua3s.epanet_data_generator.simulation_model(epanet_model, sensors)


def testbed(fiware_wrapper, fiware_service):

    quitApp = False

    while quitApp is False:
        print('aqua3s:' + '\n')

        print('\nIMM Testbed')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])

        print('\n')
        print('1..Calculate IMM Solution')
        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            try:
                #collect epanet model from contextbroker - could rewrite this hardcoded?
                fiware_service = 'P2B'
                inp_file = '/docker/aqua3s-brett-test//visualiser/data/' + fiware_service + '/waternetwork/epanet.inp'
                #inp_file = inp_file_location(fiware_wrapper, fiware_service)
                imm = unexeaqua3s.immwrapper_mo.IMM_Wrapper()
                imm.do_it(fiware_service= fiware_service, #self.pilot_name,
                          leakPipeID='14',
                          repair_duration='4',
                          n_solutions = 3,
                          logger='blah')

            except Exception as e:
                logger = unexefiware.base_logger.BaseLogger()
                logger.exception(inspect.currentframe(),e)

        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    logger = unexefiware.base_logger.BaseLogger()

    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    fiware_wrapper.init(logger=logger)
    fiware_service = 'P2B'

    testbed(fiware_wrapper, fiware_service)
