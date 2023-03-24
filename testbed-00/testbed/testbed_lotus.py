from textwrap import indent

import anomalies.testbed
import local_environment_settings
import os

import inspect
import json

import matplotlib.collections
import unexefiware.base_logger
import unexefiware.fiwarewrapper
import unexefiware.time
import unexeaqua3s.resourcebuilder
import support
import datetime
import pyproj
import unexe_epanet.epanet_fiware
import unexewrapper


import epanet.toolkit as en
import matplotlib.pyplot as plt
import numpy as np

import testbed_stepsim
import testbed_wallclock
import testbed_persistent_simstep

#for anomalies
import anomalies.testbed
import testbed_anomalies
import unexeaqua3s.visualiser
import unexeaqua3s.workhorse_backend

import models

logger = unexefiware.base_logger.BaseLogger()


def load_epanet_model(fiware_service:str) -> models.Aqua3S_Fiware:
    #GARETH - I am building the sim around aqua3S
    sim_model = models.Aqua3S_Fiware(logger)

    print('GARETH - I have changed file loading !')
    #inp_file = os.environ['FILE_PATH'] + os.sep + os.environ['FILE_VISUALISER_FOLDER'] + os.sep + 'data' + os.sep + fiware_service + os.sep + 'waternetwork' + os.sep + 'unexe_epanet.inp'

    if fiware_service == 'AAA':
        inp_file = 'local_data' + os.sep+'TS network.inp'
        coord_system = pyproj.CRS.from_epsg(32632)
        sim_model.init(epanet_file=inp_file, coord_system=coord_system, fiware_service=fiware_service, flip_coordindates=True)

    if fiware_service == 'TTT':
        inp_file = 'local_data' + os.sep+'bretts-imm-epanet.inp'
        coord_system = pyproj.CRS.from_epsg(32632)
        sim_model.init(epanet_file=inp_file, coord_system=coord_system, fiware_service=fiware_service, flip_coordindates=True)


    if fiware_service == 'GUW':
        coord_system = pyproj.CRS.from_epsg(32646)
        inp_file = 'local_data' + os.sep+'KMKHYA_GHY_WDN_24.inp'

        sim_model.init(epanet_file=inp_file, coord_system=coord_system, fiware_service=fiware_service, flip_coordindates=True)

    sim_model.fiware_service = fiware_service

    return sim_model

sim_lookup = {}

def testbed():
    global logger

    fiware_wrapper = unexewrapper.unexewrapper(url=os.environ['DEVICE_BROKER'])
    fiware_wrapper.init(logger=logger)

    # GARETH - choose epanet location here ...
    fiware_service = 'GUW'
    fiware_service = 'AAA'
    fiware_service = 'TTT'

    sensor_list = []
    start_datetime = datetime.datetime(year=2023, month=1, day=1, hour=0, minute=0, second=0)

    if fiware_service == 'GUW':
        sensor_list = [{'ID': 'GJ409', 'Type': 'pressure'}, {'ID': 'GP1', 'Type': 'flow'}]

    if fiware_service == 'AAA':
        sensor_list = [{'ID': 'R.M.', 'Type': 'pressure'}, {'ID': 'BP600.1500.BP2600.15.1', 'Type': 'flow'}]

    quitApp = False

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + fiware_service)

        print('\n')
        print('1..Sim step')
        print('2..Wall clock')
        print('3..Persistent Sim Step')
        print('X..Back')
        print('\n')

        key = input('>')

        if key == 'x':
            quitApp = True

        if key == '1':
            sim_inst = load_epanet_model(fiware_service)

            testbed_stepsim.testbed(fiware_wrapper, fiware_service, logger, sim_inst, sensor_list)

        if key == '2':
            sim_inst = load_epanet_model(fiware_service)
            sim_inst.fiware_service = fiware_service + '-WC'

            testbed_wallclock.testbed(fiware_wrapper, logger, sim_inst, sensor_list)

        if key == '3':
            sim_inst = load_epanet_model(fiware_service)
            testbed_persistent_simstep.testbed(fiware_wrapper, sim_inst)


if __name__ == '__main__':
    testbed()