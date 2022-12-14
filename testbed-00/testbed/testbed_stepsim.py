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
import testbed_fiware

import epanet.toolkit as en
import matplotlib.pyplot as plt
import numpy as np


def testbed(fiware_wrapper:unexewrapper, fiware_service:str, logger:unexefiware.base_logger.BaseLogger, sim_inst:unexe_epanet.epanet_fiware.epanet_fiware, sensor_list:list):
    quitApp = False
    start_datetime = datetime.datetime(year=2023, month=1, day=1, hour=0,minute=0,second=0)

    #GARETH don't set this, see fn() notes
    #sim_inst.set_hyd_step(MIN_TO_SEC(120))
    sim_inst.set_hyd_step(sim_inst.get_pattern_step())
    sim_inst.reset(sensor_list, start_datetime)

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + fiware_service)
        print('Sim time: ' + str(sim_inst.get_sim_time()) + ' ' + str(sim_inst.elapsed_datetime() ))
        print('Sim step: ' + str(unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step())) +'min' )

        print('\n')
        print('1..Reset Sim')
        print('2..Run a step: ' + str( int(unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step()))) + ' min' )
        print('3..Run 12 hours: ' + str( int(12*60 / unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step()))) + ' steps')
        print('4..Run a day: '  + str( int(24*60 / unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step()))) + ' steps')
        print('5..Leak Management')
        print('8..WDN graph')
        print('9..FIWARE')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == 'x':
            quitApp = True

        if key == '1':
            print('Reset')
            sim_inst.reset(sensor_list, start_datetime)

        if key == '2':
            print('Run a step')
            sim_inst.step()

        if key == '3':
            print('Run 12 steps')
            time_steps = int(12*60 / unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step()))

            for i in range(0, time_steps):
                sim_inst.step()

        if key == '4':
            print('Run a day')
            time_steps = int(24*60 / unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step()))

            for i in range(0, time_steps):
                sim_inst.step()

        if key == '5':
            testbed_fiware.sim_leak_management(sim_inst, fiware_wrapper, logger)

        if key =='8':
            testbed_fiware.epanet_graph(sim_inst, logger)

        if key == '9':
            testbed_fiware.testbed(fiware_wrapper, sim_inst)
