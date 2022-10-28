import datetime
import os
import threading
import time
import unexefiware.time

import unexefiware.base_logger
import inspect
import json

import epanet_fiware.epanetmodel
import epanet_fiware.enumerations as enu
import epanet.toolkit as en
import sim.epanet_model
import matplotlib.pyplot as plt


class SimInstance():
    def __init__(self):
        self.run_step = True
        self.elapsed_time_in_sec = 0

    def init(self, inp_file: str):

        self.epanetmodel = epanet_fiware.epanetmodel.EPAnetModel('sim network', inp_file)

        self.run_step = True
        self.elapsed_time_in_sec = 0

    def freewheel_process(self):

        if False:
            stepDuration = 1 * 60

            self.epanetmodel.set_time_param(enu.TimeParams.HydStep, (stepDuration))
            self.epanetmodel.set_time_param(enu.TimeParams.ReportStep, (stepDuration))

        en.openH(self.epanetmodel.proj_for_simulation)
        en.initH(self.epanetmodel.proj_for_simulation, en.NOSAVE)

        """
            get initial data for sim
                get the 'current' time (whereever that may be) and work out where the sim_time should start for the initial go
                    that means, take the current time and work out what the time was for sun-00:00

                while sim_time < current time
                    iterate through sim backlog                    
        """
        self.elapsed_time_in_sec = 0
        self.sim_step_in_minutes = 60 * 1

        starting_time = unexefiware.time.fiware_to_datetime('2022-08-22T07:30:00Z')

        print('Current time:' + str(starting_time))

        rounded_time = unexefiware.time.round_time(dt=starting_time, date_delta=datetime.timedelta(minutes=self.sim_step_in_minutes), to='up')

        week_time = rounded_time.strftime("%A-%H:%M")

        date_string = week_time.replace(':', '-').split('-')

        sim_start_time = rounded_time.replace(hour=0, minute=0, second=0)

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

        sim_start_time -= datetime.timedelta(minutes=time_add)

        sim_time = sim_start_time.strftime("%A-%H:%M")

        while sim_start_time < rounded_time:
            # do a sim step
            print('Doing catch-up: ' + str(sim_start_time.strftime("%A-%H:%M")))

            # add 15 min onto sim_start_time
            sim_start_time += datetime.timedelta(minutes=self.sim_step_in_minutes)

        # we should now be at sim_start > rounded time
        print('Do proper stuff')

        debug_sim_steps_to_do = 0

        while debug_sim_steps_to_do < 10:

            if sim_start_time <= starting_time:

                print(str(starting_time) + ' Doing FIWARE: ' + str(sim_start_time.strftime("%A-%H:%M")))
                sim_start_time += datetime.timedelta(minutes=self.sim_step_in_minutes)

                debug_sim_steps_to_do += 1
            else:
                print(str(starting_time))

            starting_time += datetime.timedelta(minutes=15)
            rounded_time = unexefiware.time.round_time(dt=starting_time, date_delta=datetime.timedelta(minutes=self.sim_step_in_minutes), to='up')

        # add 15 min onto sim_start_time

        print('freewheel_process started')

        """
        while self.run_step:
            assume simulation starts at 00:00 on Sunday            

                sim_time = sun-00:00

                while running:            
                    if current time > sim_time
                        run sim_step()
                        sim_time += sim_step_time

                        if do_catch_up == False:
                            send results to FIWARE
                            time_step = sim_time_step
                        else:
                            time_step = something_short


                    else
                        do_catch_up = False

                    sleep(time_step) 


        while run_step:
            en.runH(self.epanetmodel.proj_for_simulation)
            t = en.nextH(self.epanetmodel.proj_for_simulation)

            elapsed_time_in_sec += t

            dur = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.DURATION)
            en.settimeparam(self.epanetmodel.proj_for_simulation, en.DURATION, dur + t)

            time.sleep(1)
        """
        print('freewheel_process stopped')


class EPASim(sim.epanet_model.epanet_model):
    def __init__(self):
        super().__init__()

        self.elapsed_time_in_sec = 0
        self.sim_fiware_start = unexefiware.time.datetime_to_fiware(datetime.datetime.now())
        self.sim_fiware_current = self.sim_fiware_start

    def init(self, inp_file: str):
        super().init(inp_file)
        self.reset()

    def reset(self):
        try:
            if self.epanetmodel is not None:
                timestep = self.get_hyd_step()
                self.load_file(self.inp_file)
                self.set_hyd_step(timestep)
            else:
                self.load_file(self.inp_file)

            en.openH(self.epanetmodel.proj_for_simulation)
            en.initH(self.epanetmodel.proj_for_simulation, en.NOSAVE)

            self.elapsed_time_in_sec = 0
            self.sim_fiware_start = unexefiware.time.datetime_to_fiware(datetime.datetime.now())
            self.sim_fiware_current = self.sim_fiware_start
        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

    def time_for_step(self, current_fiware_time: str):
        now = unexefiware.time.fiware_to_datetime(current_fiware_time)
        time_step = self.get_hyd_step()
        now = unexefiware.time.round_time(dt=now, date_delta=datetime.timedelta(seconds=time_step), to='down')

        td = now - unexefiware.time.fiware_to_datetime(self.sim_fiware_current)

        return td >= datetime.timedelta(seconds=time_step)

    def do_a_step(self):
        en.runH(self.epanetmodel.proj_for_simulation)
        t = en.nextH(self.epanetmodel.proj_for_simulation)
        self.elapsed_time_in_sec += t

        # extend simulation by t
        dur = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.DURATION)
        en.settimeparam(self.epanetmodel.proj_for_simulation, en.DURATION, dur + t)

        self.sim_fiware_current = unexefiware.time.datetime_to_fiware(unexefiware.time.fiware_to_datetime(self.sim_fiware_current) + datetime.timedelta(seconds=t))

        return self.sim_fiware_current

    def step_to(self, fiware_time: str) -> str:
        now = unexefiware.time.fiware_to_datetime(fiware_time)
        now = unexefiware.time.round_time(dt=now, date_delta=datetime.timedelta(seconds=self.get_hyd_step() ), to='down')
        idx = (now.weekday() + 1) % 7

        sun = now - datetime.timedelta(days=idx)

        sun = sun.replace(hour=0, minute=0, second=0, microsecond=0)
        diff = (now - sun).total_seconds()

        self.sim_fiware_start = unexefiware.time.datetime_to_fiware(sun)

        run_step = True
        self.elapsed_time_in_sec = 0

        while run_step:
            en.runH(self.epanetmodel.proj_for_simulation)
            t = en.nextH(self.epanetmodel.proj_for_simulation)
            self.elapsed_time_in_sec += t

            # extend simulation by t
            dur = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.DURATION)
            en.settimeparam(self.epanetmodel.proj_for_simulation, en.DURATION, dur + t)

            run_step = self.elapsed_time_in_sec < diff

        self.sim_fiware_current = unexefiware.time.datetime_to_fiware(sun + datetime.timedelta(seconds=self.elapsed_time_in_sec))

        return self.sim_fiware_current

    def step(self):
        try:
            en.runH(self.epanetmodel.proj_for_simulation)
            t = en.nextH(self.epanetmodel.proj_for_simulation)
            self.elapsed_time_in_sec += t

            if True:
                dur = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.DURATION)
                en.settimeparam(self.epanetmodel.proj_for_simulation, en.DURATION, dur + t)

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

    def freewheel(self):
        run_step = True
        while run_step:
            en.runH(self.epanetmodel.proj_for_simulation)
            t = en.nextH(self.epanetmodel.proj_for_simulation)

            pipeIndex = en.getlinkindex(self.epanetmodel.proj_for_simulation, '5')
            flow = en.getlinkvalue(self.epanetmodel.proj_for_simulation, pipeIndex, en.FLOW)

            en.getnodeindex(self.epanetmodel.proj_for_simulation, '105')
            pressure = en.getnodevalue(self.epanetmodel.proj_for_simulation, pipeIndex, en.PRESSURE)

            print(str(datetime.timedelta(seconds=self.elapsed_time_in_sec) + datetime.timedelta(days=1)) + ' 5:' + str(round(flow, 2)) + ' 105:' + str(round(pressure, 2)))

            self.elapsed_time_in_sec += t

            dur = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.DURATION)
            en.settimeparam(self.epanetmodel.proj_for_simulation, en.DURATION, dur + t)

            run_step = t > 0

    def freewheel_process(self, run_step: threading.Event):

        epanetmodel = epanet_fiware.epanetmodel.EPAnetModel('sim network', self.inp_file)

        stepDuration = 1 * 60

        epanetmodel.set_time_param(enu.TimeParams.HydStep, (stepDuration))  # set hydraulic time step to 15min
        epanetmodel.set_time_param(enu.TimeParams.ReportStep, (stepDuration))  # set reporting time step to 15min

        en.openH(epanetmodel.proj_for_simulation)
        en.initH(epanetmodel.proj_for_simulation, en.NOSAVE)

        elapsed_time_in_sec = 0

        print('freewheel_process started')

        while run_step.is_set():
            en.runH(epanetmodel.proj_for_simulation)
            t = en.nextH(epanetmodel.proj_for_simulation)

            pipeIndex = en.getlinkindex(epanetmodel.proj_for_simulation, '5')
            flow = en.getlinkvalue(epanetmodel.proj_for_simulation, pipeIndex, en.FLOW)

            en.getnodeindex(epanetmodel.proj_for_simulation, '105')
            pressure = en.getnodevalue(epanetmodel.proj_for_simulation, pipeIndex, en.PRESSURE)

            # print(str(datetime.timedelta(seconds=self.elapsed_time_in_sec) + datetime.timedelta(days=1)) + ' 5:' + str(round(flow, 2)) + ' 105:' + str(round(pressure, 2)) )

            elapsed_time_in_sec += t

            dur = en.gettimeparam(epanetmodel.proj_for_simulation, en.DURATION)
            en.settimeparam(epanetmodel.proj_for_simulation, en.DURATION, dur + t)

            time.sleep(1)

        print('freewheel_process stopped')

    def proper_freewheel(self):

        run_step = threading.Event()
        run_step.set()
        thread = threading.Thread(target=self.freewheel_process, args=(run_step,))
        thread.start()

        while run_step.is_set():
            print('1..Current Stats')
            print('X..Quit Thread')

            key = input('>')

            if key == '1':
                pass

            if key == 'x':
                run_step.clear()


def testbed(fiware_service):
    quitApp = False

    epasim = EPASim()

    fiware_service = 'AAA'
    inp_file = os.environ['FILE_PATH'] + os.sep + os.environ['FILE_VISUALISER_FOLDER'] + os.sep + 'data' + os.sep + fiware_service + os.sep + 'waternetwork' + os.sep + 'epanet.inp'
    epasim.init(inp_file)

    while quitApp is False:
        print('\nEPASim Testbed')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + fiware_service)

        print('\n')
        print('1..Reset Sim')
        print('2..Run a step')
        print('2a..Graph steps')
        print('3..Freewheel sim')
        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            epasim.reset()

        if key == '2':
            for i in range(0, 10):
                epasim.step()

            if fiware_service == 'GUW':
                try:
                    pipeIndex = en.getlinkindex(epasim.epanetmodel.proj_for_simulation, '5')
                    val = en.getlinkvalue(epasim.epanetmodel.proj_for_simulation, pipeIndex, en.FLOW)

                    print(str(datetime.timedelta(seconds=epasim.elapsed_time_in_sec) + datetime.timedelta(days=1)) + ' ' + str(round(val, 2)))
                except Exception as e:
                    logger = unexefiware.base_logger.BaseLogger()
                    logger.exception(inspect.currentframe(), e)

            if fiware_service == 'AAA':
                try:
                    pipeIndex = en.getlinkindex(epasim.epanetmodel.proj_for_simulation, 'NRV10.400-1000.1')
                    val = en.getlinkvalue(epasim.epanetmodel.proj_for_simulation, pipeIndex, en.FLOW)

                    elapsed_time = epasim.elapsed_time_in_sec
                    elapsed_time /= (60 * 60)
                    elapsed_time = int(elapsed_time)

                    print(str(elapsed_time) + ' ' + str(round(val, 2)))

                except Exception as e:
                    logger = unexefiware.base_logger.BaseLogger()
                    logger.exception(inspect.currentframe(), e)

        if key == '2a':
            y = []
            x = []
            for i in range(0, 350):
                epasim.step()

                x.append(i)

                if fiware_service == 'AAA':
                    try:
                        pipeIndex = en.getlinkindex(epasim.epanetmodel.proj_for_simulation, 'NRV10.400-1000.1')
                        y.append(en.getlinkvalue(epasim.epanetmodel.proj_for_simulation, pipeIndex, en.FLOW))

                    except Exception as e:
                        logger = unexefiware.base_logger.BaseLogger()
                        logger.exception(inspect.currentframe(), e)

            fig = plt.figure(dpi=200)
            ax = fig.add_subplot(1, 1, 1)
            ax.plot(x, y)

            plt.show()

        if key == '3':
            instance = SimInstance()
            # epasim.proper_freewheel()
            instance.init(inp_file)
            instance.freewheel_process()

        if key == 'x':
            quitApp = True
