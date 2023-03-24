import gc

import local_environment_settings
import os

import unexefiware.base_logger
import unexefiware.time
import unexeaqua3s.resourcebuilder
import datetime
import unexe_epanet.epanet_fiware
import unexewrapper
import testbed_fiware
import models

import unexe_epanet.epanet_anomaly_detection
import unexe_epanet.epanet_anomaly_localisation
import gc


#GARETH - persistent simstep means that we need to run the sim from in here and do other stuff (from in here)
#other stuff
#   -gen new data
#   -set and stop leaks
#   -setup epanomaly data
#   -do leak localisation (on demmand?)

start_datetime = datetime.datetime(year=2023, month=1, day=1, hour=0,minute=0,second=0)

def sim_management(sim_inst:models.Aqua3S_Fiware, sensor_list:list):
    quitApp = False
    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + sim_inst.fiware_service)
        print('Sim time: ' + str(sim_inst.get_sim_time()) + ' ' + str(sim_inst.elapsed_datetime()))
        print('Sim step: ' + str(unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step())) + 'min')

        print('\n')
        print('99..Reset Sim')
        print('2..Run a step: ' + str(int(unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step()))) + ' min')
        print('3..Run 12 hours: ' + str(int(12 * 60 / unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step()))) + ' steps')
        print('4..Run a day: ' + str(int(24 * 60 / unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step()))) + ' steps')
        print('4a..Run a week')
        print('4b..Run a month')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == 'x':
            quitApp = True

        if key == '99':
            print('Reset')
            sim_inst.reset(sensor_list, start_datetime)

        if key == '2':
            print('Run a step')
            sim_inst.simulate(1)


        if key == '3':
            print('Run 12 steps')
            time_steps = int(12*60 / unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step()))

            sim_inst.simulate(time_steps)

        if key == '4':
            print('Run a day')
            time_steps = int(24*60 / unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step()))

            sim_inst.simulate(time_steps)

        if key == '4a':
            print('Run a week')
            time_steps = int((7*24*60) / unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step()))

            sim_inst.simulate(time_steps)

        if key == '4b':
            print('Run a month')
            time_steps = int((31*24*60) / unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step()))

            sim_inst.simulate(time_steps)

def anomaly_management(sim_inst:models.Aqua3S_Fiware, sensor_list:list):
    quitApp = False
    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + sim_inst.fiware_service)
        print('Sim time: ' + str(sim_inst.get_sim_time()) + ' ' + str(sim_inst.elapsed_datetime()))
        print('Sim step: ' + str(unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step())) + 'min')

        print('\n')
        print('1..Build Anomaly Detection Data')
        print('2..Build Anomaly Localisation Data')
        print('3..Run Anomaly Localisation')
        print('X..Back')
        print('\n')

        key = input('>')

        if key == 'x':
            quitApp = True

        if key == '1':
            print('Build Detection Data')
            ad = unexe_epanet.epanet_anomaly_detection.epanet_anomaly_detection()
            ad.inp_file = sim_inst.inp_file
            ad.build_anomaly_data(simulation_start= sim_inst.start_datetime,fiware_service= sim_inst.fiware_service, sensors=sensor_list, leak_node_ids=None)
            ad.save_anomaly_data(sim_inst, os.environ['LOAD_LOCAL_ANOMALY_DATA_PATH'])

        if key == '2':
            print('Build Localisation Data')
            al = unexe_epanet.epanet_anomaly_localisation.epanet_anomaly_localisation()
            al.init(sim_inst,sensor_list)

            step_duration_as_minutes = 15

            if sim_inst.fiware_service == 'GUW':
                step_duration_as_minutes = 60

            al.build_datasets( sim_inst.start_datetime, stepDuration_as_seconds = step_duration_as_minutes*60)

        if key == '3':
            print('Run Anomaly Localisation')

            al = unexe_epanet.epanet_anomaly_localisation.epanet_anomaly_localisation()
            al.init(sim_inst, sensor_list)
            al.load_datasets()
            al.anomaly_localisation.ML_buildModel()

            step_duration_as_minutes = 15

            if sim_inst.fiware_service == 'GUW':
                step_duration_as_minutes = 60

            al.run_leak_localisation_test( sim_inst.start_datetime,step_duration_as_minutes)



def testbed(fiware_wrapper:unexewrapper, sim_inst:models.Aqua3S_Fiware):
    quitApp = False

    sensor_list = []

    juncs = None
    pipes = None

    if sim_inst.fiware_service == 'GUW':
        pipes = ['GP1', 'GP585', '6', 'GP269', 'GP544', '2', 'GP523', 'GP453']
        juncs = ['GJ409', 'GJ507', 'GJ533', 'GJ525','GJ258', 'GJ379', 'GJ397']

    if sim_inst.fiware_service == 'AAA':
        pipes = ['POZZO_3.R.M..1']
        juncs = ['POZZO_11']

    if sim_inst.fiware_service == 'TTT':
        juncs = ['76','104','72','96']
        pipes = ['2','5','23','1']
        #juncs = ['76']
        #juncs = None
        #pipes = ['GP1']

    if pipes:
        for pipe in pipes:
            sensor_list.append({'ID': pipe, 'Type': 'flow'})

    if juncs:
        for junc in juncs:
            sensor_list.append({'ID': junc, 'Type': 'pressure'})


    #GARETH don't set this, see fn() notes
    #sim_inst.set_hyd_step(MIN_TO_SEC(120))
    sim_inst.set_hyd_step(sim_inst.get_pattern_step())
    sim_inst.reset(sensor_list, start_datetime)

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + sim_inst.fiware_service)
        print('Sim time: ' + str(sim_inst.get_sim_time()) + ' ' + str(sim_inst.elapsed_datetime() ))
        print('Sim step: ' + str(unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step())) +'min' )

        print('\n')
        print('1..Sim Management')
        print('2..Leak Creation Management')
        print('3..Anomaly Management')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == 'x':
            quitApp = True

        if key == '1':
            sim_management(sim_inst,sensor_list)

        if key == '2':
            testbed_fiware.sim_leak_management(sim_inst, fiware_wrapper)

        if key == '3':
            anomaly_management(sim_inst, sensor_list)

