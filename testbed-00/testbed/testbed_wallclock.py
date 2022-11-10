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

class epanet_wallclock():
    def __init__(self, sim_inst:unexe_epanet.epanet_fiware):
        self.sim_inst = sim_inst
        self.run_thread = False
        self.thread_is_done = True
        self.process_thread = None

    def reset(self, sensor_list: list, current_datetime: datetime.datetime):

        if self.process_thread != None:
            while self.thread_is_done != True:
                self.run_thread = False
                time.sleep(1)

            self.process_thread = None

        #work out when the simulation should have started, i.e. current_datetime - last sunday
        #spin up thread and start processing in it

        rounded_time = unexefiware.time.round_time(dt=current_datetime, date_delta=datetime.timedelta(seconds=self.sim_inst.get_hyd_step()), to='up')
        date_string = rounded_time.strftime("%A-%H:%M").replace(':', '-').split('-')

        time_add = 0

        if date_string[0] == 'Sunday':
            time_add += 24 * 60 * 0

        if date_string[0] == 'Monday':
            time_add += 24 * 60 * 1

        if date_string[0] == 'Tuesday':
            time_add += 24 * 60 * 2

        if date_string[0] == 'Wednesday':
            time_add += 24 * 60 * 3

        if date_string[0] == 'Thursday':
            time_add += 24 * 60 * 4

        if date_string[0] == 'Friday':
            time_add += 24 * 60 * 5

        if date_string[0] == 'Saturday':
            time_add += 24 * 60 * 6

        actual_sim_start_time = rounded_time.replace(hour=0, minute=0, second=0)
        actual_sim_start_time -= datetime.timedelta(minutes=time_add)

        self.sim_inst.set_hyd_step( self.sim_inst.get_pattern_step() )
        self.sim_inst.reset(sensor_list=sensor_list, start_datetime=actual_sim_start_time)

        #now start the thread
        self.run_thread = True
        self.thread_is_done = False

        self.process_thread = threading.Thread(group=None, target=self.thread_process)
        self.process_thread.start()

    def thread_process(self):
        self.thread_is_done = False

        while self.run_thread == True:
            rounded_time = unexefiware.time.round_time(dt=datetime.datetime.now(), date_delta=datetime.timedelta(seconds=self.sim_inst.get_hyd_step()), to='down')
            if self.sim_inst.elapsed_datetime() < rounded_time:
                # do a unexe_epanet step
                self.sim_inst.step()

                #print(str(self.sim_inst.elapsed_datetime()) + ' ' + str(rounded_time))
            else:
                time.sleep(1)

        self.thread_is_done = True

    def log(self):
        return str(self.sim_inst.elapsed_datetime().strftime("%A-%H:%M"))

def testbed(fiware_wrapper:unexewrapper, logger:unexefiware.base_logger.BaseLogger, sim_inst:unexe_epanet.epanet_fiware.epanet_fiware, sensor_list:list):

    quitApp = False

    wallclock_sim = epanet_wallclock(sim_inst)
    wallclock_sim.reset(sensor_list, datetime.datetime.now())

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + wallclock_sim.sim_inst.fiware_service)
        print('Sim time: ' + str(sim_inst.get_sim_time()) + ' ' + str(sim_inst.elapsed_datetime()))
        print('Sim step: ' + str(unexe_epanet.epanet_model.SEC_TO_MIN(sim_inst.get_hyd_step())) + 'min')

        print('\n')
        print('1..Reset sim')
        print('2..Pause / Resume sim')
        print('3..Sim current state:' + wallclock_sim.log())
        print('5..Leak Management')
        print('8..WDN graph')
        print('9..FIWARE')
        print('X..Back')
        print('\n')

        key = input('>')

        if key == 'x':
            quitApp = True

        if key == '1':
            print('Reset Sim - do nothing')

        if key == '2':
            print('Pause/Resume - do nothing')

        if key == '3':
            print(wallclock_sim.log() )

        if key == '5':
            testbed_fiware.sim_leak_management(wallclock_sim.sim_inst, fiware_wrapper, logger)

        if key =='8':
            testbed_fiware.epanet_graph(wallclock_sim.sim_inst, logger)

        if key == '9':
            testbed_fiware.testbed(fiware_wrapper, wallclock_sim.sim_inst) #.fiware_service, logger, unexefiware.time.datetime_to_fiware(wallclock_sim.sim_inst.elapsed_datetime()) )
