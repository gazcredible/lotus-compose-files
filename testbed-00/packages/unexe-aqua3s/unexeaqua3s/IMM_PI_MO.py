import epanet_fiware.epanetmodel
import epanet_fiware.enumerations as enu
import epanet_fiware.epanet_outfile_handler as outfile_handler
import epanet.toolkit as en
import pandas as pd
import numpy as np
import datetime
from typing import Optional


# %%
class IMM_model:
    def __init__(self,
                 inp_file: str,
                 network_name: str,
                 ):
        self.inp_file = inp_file
        self.network_name = network_name
        self.epanetmodel = None
        self.simulationParameters = {}
        self.PI_results = {}
        self.baseDemand_m3 = None
        self.baseDRscore = None
        self.node_pop = None

    def set_simulation_Parameters(self,
                                  awarenesstime: Optional[datetime.datetime] = datetime.datetime.now(),
                                  hyd_time_step: Optional[int] = 900,
                                  pmin: Optional[int] = 3,
                                  preq: Optional[int] = 15,
                                  leakEmitter: Optional[int] = 50,
                                  leakExponent: Optional[float] = 0.99,
                                  repair_sec: Optional[int] = 4 * 60 * 60,  # 4 hours
                                  leakNodeID=None,
                                  leakPipeID=None,
                                  OperationalPipeIDs=None,
                                  OperationalPRVIDs=None,
                                  leakStartTime=None
                                  ):

        awarenesstime = awarenesstime.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)  # rounds up to next hour
        patternStartday = datetime.date(2022, 1, 1).weekday()  # simulations must start on 5th weekday (i.e.sat)
        if awarenesstime.weekday() > patternStartday:
            simulation_start_date = (awarenesstime - datetime.timedelta(days=awarenesstime.weekday()) + datetime.timedelta(days=5))
        else:
            simulation_start_date = (awarenesstime - datetime.timedelta(days=awarenesstime.weekday()) + datetime.timedelta(days=5,
                                                                                                                           weeks=-1))
        if leakStartTime == None:
            leakStartTime = awarenesstime - datetime.timedelta(hours=2)

        simulation_start_date = simulation_start_date.replace(hour=0)
        self.simulationParameters['awarenesstime'] = awarenesstime
        self.simulationParameters['leak_start_date'] = leakStartTime
        self.simulationParameters['simulation_start_date'] = simulation_start_date
        self.simulationParameters['simulation_end_date'] = awarenesstime + datetime.timedelta(days=2)
        self.simulationParameters['hyd_time_step'] = hyd_time_step
        self.simulationParameters['Pmin'] = pmin
        self.simulationParameters['Preq'] = preq
        self.simulationParameters['leakNodeID'] = leakNodeID
        self.simulationParameters['leakPipeID'] = leakPipeID
        self.simulationParameters['repair_sec'] = repair_sec
        self.simulationParameters['leakEmitter'] = leakEmitter
        self.simulationParameters['leakExponent'] = leakExponent
        self.simulationParameters['OperationalPipeIDs'] = OperationalPipeIDs
        self.simulationParameters['OperationalPRVIDs'] = OperationalPRVIDs

    def load_epanetmodel(self):
        self.epanetmodel = epanet_fiware.epanetmodel.EPAnetModel(self.network_name, self.inp_file)

    def get_leakNodeID(self, pipe_name):
        self.load_epanetmodel()
        leak_index = en.getlinkindex(self.epanetmodel.proj_for_simulation, pipe_name)
        node1_index, node2_index = en.getlinknodes(self.epanetmodel.proj_for_simulation, leak_index)
        node1_type = en.getnodetype(self.epanetmodel.proj_for_simulation, node1_index)
        if node1_type == 0:
            leak_nodeIndex = node1_index
        else:
            leak_nodeIndex = node2_index
        leak_nodeID = en.getnodeid(self.epanetmodel.proj_for_simulation, leak_nodeIndex)
        return leak_nodeID

    def get_pop_per_node(self, total_population: Optional[int] = 1000, pop_per_node_list: Optional = False):
        if pop_per_node_list is False:  # if not provided calc weighted avg based of demand
            self.load_epanetmodel()
            nodeIDs = self.epanetmodel.get_node_ids(enu.NodeTypes.Junction)
            nodes = []
            total_base_demand = 0
            for nodeID in nodeIDs:
                node_index = en.getnodeindex(self.epanetmodel.proj_for_simulation, nodeID)
                num_demands = en.getnumdemands(self.epanetmodel.proj_for_simulation, node_index)
                base_demand = 0
                for demand_index in range(0, num_demands):
                    base_demand = base_demand + en.getbasedemand(self.epanetmodel.proj_for_simulation, node_index,
                                                                 (demand_index + 1))  # have to add one cause indexing starts at 1
                node_dict = {}
                node_dict['ID'] = nodeID
                node_dict['index'] = node_index
                node_dict['base_demand'] = base_demand
                nodes.append(node_dict)
                total_base_demand = total_base_demand + base_demand
            for node in nodes:
                node['pop'] = round(node['base_demand'] * total_population / total_base_demand)
            self.node_pop = nodes
            self.epanetmodel = None

    def base_scenario_sim(self):
        self.load_epanetmodel()
        duration = int((self.simulationParameters['simulation_end_date'] - self.simulationParameters['simulation_start_date']).total_seconds())
        stepDuration = self.simulationParameters['hyd_time_step']
        awareness_sec = int((self.simulationParameters['awarenesstime'] - self.simulationParameters['simulation_start_date']).total_seconds())
        # used to calculate basedemand & baseDRscore
        self.epanetmodel.set_time_param(enu.TimeParams.Duration, (duration))  # set simulation duration for 15 days
        self.epanetmodel.set_time_param(enu.TimeParams.HydStep, stepDuration)  # set hydraulic time step to 15min
        self.epanetmodel.set_time_param(enu.TimeParams.ReportStep, stepDuration)  # set reporting time step to 15min
        self.epanetmodel.set_epanet_mode(enu.EpanetModes.PDA, pmin=self.simulationParameters['Pmin'], preq=self.simulationParameters['Preq'], pexp=0.5)  # set demand mode
        # run simulation step-by-step
        en.openH(self.epanetmodel.proj_for_simulation)
        en.initH(self.epanetmodel.proj_for_simulation, en.NOSAVE)
        en.setoption(self.epanetmodel.proj_for_simulation, en.TRIALS, 100)  # reduce number of trials for convergence
        en.setoption(self.epanetmodel.proj_for_simulation, en.ACCURACY, 0.01)  # reduce accuracy required for convergence
        en.setoption(self.epanetmodel.proj_for_simulation, en.EMITEXPON, self.simulationParameters['leakExponent'])

        t = en.nextH(self.epanetmodel.proj_for_simulation)
        pipes = self.create_pipeDict()
        self.baseDemand_m3 = 0
        self.baseDRscore = 0

        while t > 0:
            en.runH(self.epanetmodel.proj_for_simulation)
            hyd_sim_seconds = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.HTIME)
            report_step = hyd_sim_seconds / stepDuration
            # calc basedemand and basevelocities after awarenesstime (i.e. last 48 hr of simulation)
            if hyd_sim_seconds >= awareness_sec:
                baseDemand_lps = 0
                for node in self.node_pop:
                    baseDemand_lps = baseDemand_lps + en.getnodevalue(self.epanetmodel.proj_for_simulation, node['index'], en.DEMAND)
                self.baseDemand_m3 = self.baseDemand_m3 + (baseDemand_lps * stepDuration / 1000)

                for pipe in pipes:
                    baseVelocity = en.getlinkvalue(self.epanetmodel.proj_for_simulation, pipe['index'], en.VELOCITY)
                    if baseVelocity > pipe['max_velocity']:
                        pipe['max_velocity'] = baseVelocity

            t = en.nextH(self.epanetmodel.proj_for_simulation)
        self.epanetmodel = None

        for pipe in pipes:
            if pipe['max_velocity'] < 0.4:
                self.baseDRscore = self.baseDRscore + 1
            if 0.4 <= pipe['max_velocity'] < 0.8:
                self.baseDRscore = self.baseDRscore + 2
            if 0.8 <= pipe['max_velocity'] < 1.2:
                self.baseDRscore = self.baseDRscore + 3
            if 1.2 <= pipe['max_velocity'] < 1.6:
                self.baseDRscore = self.baseDRscore + 4
            if pipe['max_velocity'] >= 1.6:
                self.baseDRscore = self.baseDRscore + 5

    def default_repair_scenario(self):
        duration = int((self.simulationParameters['simulation_end_date'] - self.simulationParameters['simulation_start_date']).total_seconds())
        stepDuration = self.simulationParameters['hyd_time_step']
        awareness_sec = int((self.simulationParameters['awarenesstime'] - self.simulationParameters['simulation_start_date']).total_seconds())
        repair_start_sec = awareness_sec
        repair_end_sec = repair_start_sec + self.simulationParameters['repair_sec']
        leak_start_sec = int((self.simulationParameters['leak_start_date'] - self.simulationParameters['simulation_start_date']).total_seconds())
        self.load_epanetmodel()
        # start_time = datetime.datetime.now()
        leakIndex = en.getnodeindex(self.epanetmodel.proj_for_simulation, self.simulationParameters['leakNodeID'])
        pipeIndex = en.getlinkindex(self.epanetmodel.proj_for_simulation, self.simulationParameters['leakPipeID'])
        self.epanetmodel.set_time_param(enu.TimeParams.Duration, (duration))  # set simulation duration for 15 days
        self.epanetmodel.set_time_param(enu.TimeParams.HydStep, stepDuration)  # set hydraulic time step to 15min
        self.epanetmodel.set_time_param(enu.TimeParams.ReportStep, stepDuration)  # set reporting time step to 15min
        self.epanetmodel.set_epanet_mode(enu.EpanetModes.PDA, pmin=self.simulationParameters['Pmin'], preq=self.simulationParameters['Preq'], pexp=0.5)  # set demand mode

        # run simulation step-by-step
        en.openH(self.epanetmodel.proj_for_simulation)
        en.initH(self.epanetmodel.proj_for_simulation, en.NOSAVE)
        en.setoption(self.epanetmodel.proj_for_simulation, en.EMITEXPON, self.simulationParameters['leakExponent'])
        en.setoption(self.epanetmodel.proj_for_simulation, en.TRIALS, 100)  # reduce number of trials for convergence
        en.setoption(self.epanetmodel.proj_for_simulation, en.ACCURACY, 0.01)  # reduce accuracy required for convergence

        t = en.nextH(self.epanetmodel.proj_for_simulation)

        PIs = {'PI1': 0, 'PI2': 0, 'PI3': 0, 'PI4': 0}
        leakDemand_m3 = 0
        leakvolume = 0
        newDRscore = 0
        pipes = self.create_pipeDict()

        while t > 0:
            en.runH(self.epanetmodel.proj_for_simulation)
            hyd_sim_seconds = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.HTIME)
            report_step = hyd_sim_seconds / stepDuration
            if report_step == int(leak_start_sec / stepDuration):  # add orifice leak
                en.setnodevalue(self.epanetmodel.proj_for_simulation, leakIndex, en.EMITTER, self.simulationParameters['leakEmitter'])
            if report_step == int(repair_start_sec / stepDuration):  # stop leak, close pipe
                en.setnodevalue(self.epanetmodel.proj_for_simulation, leakIndex, en.EMITTER, 0.00000000001)  # stop pipe leak - error with owa programming - 0 doesn't work.
                en.setlinkvalue(self.epanetmodel.proj_for_simulation, pipeIndex, en.STATUS, 0)  # 0 means closed, 1 means open
            if report_step == int(repair_end_sec / stepDuration):  # open pipe that's been repaired
                en.setlinkvalue(self.epanetmodel.proj_for_simulation, pipeIndex, en.STATUS, 1)
            # calc PIs
            if hyd_sim_seconds >= awareness_sec:
                PI1, PI2, PI3_demand = self.PI_step()
                PIs['PI1'] = PIs['PI1'] + PI1 * stepDuration
                PIs['PI2'] = PIs['PI2'] + PI2 * stepDuration
                leakDemand_m3 = leakDemand_m3 + (PI3_demand * stepDuration / 1000)

            # calc leakage volume while leak is running
            if (hyd_sim_seconds >= awareness_sec) & (hyd_sim_seconds <= repair_start_sec):
                leak_pressure = en.getnodevalue(self.epanetmodel.proj_for_simulation, leakIndex, en.PRESSURE)
                leakflow = self.simulationParameters['leakEmitter'] * (leak_pressure ** self.simulationParameters['leakExponent'])
                leakvolume = leakvolume + (leakflow * stepDuration / 1000)

            for pipe in pipes:
                velocity = en.getlinkvalue(self.epanetmodel.proj_for_simulation, pipe['index'], en.VELOCITY)
                if velocity > pipe['max_velocity']:
                    pipe['max_velocity'] = velocity

            t = en.nextH(self.epanetmodel.proj_for_simulation)
        self.epanetmodel = None

        for pipe in pipes:
            if pipe['max_velocity'] < 0.4:
                newDRscore = newDRscore + 1
            if 0.4 <= pipe['max_velocity'] < 0.8:
                newDRscore = newDRscore + 2
            if 0.8 <= pipe['max_velocity'] < 1.2:
                newDRscore = newDRscore + 3
            if 1.2 <= pipe['max_velocity'] < 1.6:
                newDRscore = newDRscore + 4
            if pipe['max_velocity'] >= 1.6:
                newDRscore = newDRscore + 5

        # print("leak Volume is " + str(leakvolume))
        PIs['PI3'] = self.baseDemand_m3 - (leakDemand_m3 - leakvolume)
        PIs['PI4'] = newDRscore - self.baseDRscore
        PIs['leakvolume'] = leakvolume
        self.PI_results['default_repair'] = PIs
        return PIs  # , self.baseDemand_m3, leakDemand_m3, leakvolume

    def assess_IMM(self, x):
        duration = int((self.simulationParameters['simulation_end_date'] - self.simulationParameters['simulation_start_date']).total_seconds())
        stepDuration = self.simulationParameters['hyd_time_step']
        awareness_sec = int((self.simulationParameters['awarenesstime'] - self.simulationParameters['simulation_start_date']).total_seconds())
        repair_start_sec = awareness_sec + (x[0] * 60 * 60)
        repair_end_sec = repair_start_sec + self.simulationParameters['repair_sec']
        leak_start_sec = int((self.simulationParameters['leak_start_date'] - self.simulationParameters['simulation_start_date']).total_seconds())
        self.load_epanetmodel()
        # start_time = datetime.datetime.now()
        leakIndex = en.getnodeindex(self.epanetmodel.proj_for_simulation, self.simulationParameters['leakNodeID'])
        pipeIndex = en.getlinkindex(self.epanetmodel.proj_for_simulation, self.simulationParameters['leakPipeID'])
        self.epanetmodel.set_time_param(enu.TimeParams.Duration, (duration))
        self.epanetmodel.set_time_param(enu.TimeParams.HydStep, (stepDuration))
        self.epanetmodel.set_time_param(enu.TimeParams.ReportStep, (stepDuration))
        self.epanetmodel.set_epanet_mode(enu.EpanetModes.PDA, pmin=3, preq=15, pexp=0.5)  # set demand mode
        # run simulation step-by-step
        en.openH(self.epanetmodel.proj_for_simulation)
        en.initH(self.epanetmodel.proj_for_simulation, en.NOSAVE)
        en.setoption(self.epanetmodel.proj_for_simulation, en.EMITEXPON, self.simulationParameters['leakExponent'])
        en.setoption(self.epanetmodel.proj_for_simulation, en.TRIALS, 100)  # reduce number of trials for convergence
        en.setoption(self.epanetmodel.proj_for_simulation, en.ACCURACY, 0.01)  # reduce accuracy required for convergence

        t = en.nextH(self.epanetmodel.proj_for_simulation)

        PIs = {'PI1': 0, 'PI2': 0, 'PI3': 0, 'PI4': 0}
        leakDemand_m3 = 0
        leakvolume = 0
        newDRscore = 0
        pipes = self.create_pipeDict()

        while t > 0:
            en.runH(self.epanetmodel.proj_for_simulation)
            hyd_sim_seconds = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.HTIME)
            report_step = hyd_sim_seconds / stepDuration
            if report_step == int(leak_start_sec / stepDuration):  # add orifice leak
                en.setnodevalue(self.epanetmodel.proj_for_simulation, leakIndex, en.EMITTER,
                                self.simulationParameters['leakEmitter'])
            if report_step == int(repair_start_sec / stepDuration):  # stop leak, close pipe for repair
                en.setnodevalue(self.epanetmodel.proj_for_simulation, leakIndex, en.EMITTER, 0.00000000001)  # stop pipe leak
                en.setlinkvalue(self.epanetmodel.proj_for_simulation, pipeIndex, en.STATUS, 0)  # 0 means closed, 1 means open
            if x[1] > 0:  # operate closed pipe
                operational_pipeIndex = en.getlinkindex(self.epanetmodel.proj_for_simulation,
                                                        self.simulationParameters['OperationalPipeIDs'][0])
                operate_pipe1_topen = awareness_sec + ((x[1] - 1) * 60 * 60)
                opreate_pipe1_tclose = awareness_sec + ((x[2] - 1) * 60 * 60)
                if report_step == int(operate_pipe1_topen / stepDuration):
                    en.setlinkvalue(self.epanetmodel.proj_for_simulation, operational_pipeIndex, en.STATUS, 1)  # 0 means closed, 1 means open
                if report_step == int(opreate_pipe1_tclose / stepDuration):
                    en.setlinkvalue(self.epanetmodel.proj_for_simulation, operational_pipeIndex, en.STATUS, 0)  # 0 means closed, 1 means open

            # PRV setting
            num_prvs = len(self.simulationParameters['OperationalPRVIDs'])
            for i in range(num_prvs):
                j = (i+1)*3 #prv location within X
                if x[j] !=2: #operate closed pipe
                    operational_pipeIndex = en.getlinkindex(self.epanetmodel.proj_for_simulation,
                                                            self.simulationParameters['OperationalPRVIDs'][i])

                    initial_prv_setting = en.getlinkvalue(self.epanetmodel.proj_for_simulation,
                                                          operational_pipeIndex,
                                                          en.SETTING)
                    if x[j] == 0:
                        new_prv_setting = 0
                    if x[j] == 1:
                        new_prv_setting = 0.5
                    if x[j] == 3:
                        new_prv_setting = 1.5
                    if x[j] == 4:
                        new_prv_setting = 2

                    operate_prv_topen = awareness_sec + ((x[j+1] - 1) * 60 * 60)
                    opreate_prv_tclose = awareness_sec + ((x[j+2] - 1) * 60 * 60)
                    if report_step == int(operate_prv_topen / stepDuration):  # adjust PRV Setting
                        en.setlinkvalue(self.epanetmodel.proj_for_simulation, operational_pipeIndex,
                                        en.SETTING, round(initial_prv_setting * (new_prv_setting)))
                    if report_step == int(opreate_prv_tclose / stepDuration):
                        en.setlinkvalue(self.epanetmodel.proj_for_simulation, operational_pipeIndex,
                                        en.SETTING, initial_prv_setting)

            if report_step == int(repair_end_sec / stepDuration):  # open pipe that's been repaired
                en.setlinkvalue(self.epanetmodel.proj_for_simulation, pipeIndex, en.STATUS, 1)
            # calc PIs
            if hyd_sim_seconds >= awareness_sec:
                PI1, PI2, PI3_demand = self.PI_step()
                PIs['PI1'] = PIs['PI1'] + PI1 * stepDuration
                PIs['PI2'] = PIs['PI2'] + PI2 * stepDuration
                leakDemand_m3 = leakDemand_m3 + (PI3_demand * stepDuration / 1000)

            # calc leakage volume while leak is running
            if (hyd_sim_seconds >= awareness_sec) & (hyd_sim_seconds <= repair_start_sec):
                leak_pressure = en.getnodevalue(self.epanetmodel.proj_for_simulation, leakIndex, en.PRESSURE)
                if leak_pressure <0:
                    leak_pressure = 0
                leakflow = self.simulationParameters['leakEmitter'] * (
                        leak_pressure ** self.simulationParameters['leakExponent'])
                leakvolume = leakvolume + (leakflow * stepDuration / 1000)

            for pipe in pipes:
                velocity = en.getlinkvalue(self.epanetmodel.proj_for_simulation, pipe['index'], en.VELOCITY)
                if velocity > pipe['max_velocity']:
                    pipe['max_velocity'] = velocity

            t = en.nextH(self.epanetmodel.proj_for_simulation)
        self.epanetmodel = None

        for pipe in pipes:
            if pipe['max_velocity'] < 0.4:
                newDRscore = newDRscore + 1
            if 0.4 <= pipe['max_velocity'] < 0.8:
                newDRscore = newDRscore + 2
            if 0.8 <= pipe['max_velocity'] < 1.2:
                newDRscore = newDRscore + 3
            if 1.2 <= pipe['max_velocity'] < 1.6:
                newDRscore = newDRscore + 4
            if pipe['max_velocity'] >= 1.6:
                newDRscore = newDRscore + 5

        PIs['PI3'] = self.baseDemand_m3 - (leakDemand_m3 - leakvolume)
        if PIs['PI3'] < 0: #this occurs when pressure increases compared to original sim due to PRV operation.
            PIs['PI3'] = 0
        PIs['PI4'] = newDRscore - self.baseDRscore
        if self.PI_results['default_repair']['PI1'] <= 0:
            PIs['PI1_marg'] = PIs['PI1']
        else:
            PIs['PI1_marg'] = (self.PI_results['default_repair']['PI1'] - PIs['PI1']) / self.PI_results['default_repair']['PI1']
        if self.PI_results['default_repair']['PI2'] <= 0:
            PIs['PI2_marg'] = (PIs['PI2'])
        else:
            PIs['PI2_marg'] = (self.PI_results['default_repair']['PI2'] - PIs['PI2']) / self.PI_results['default_repair']['PI2']
        if self.PI_results['default_repair']['PI3'] <= 0:
            PIs['PI3_marg'] = PIs['PI3']
        else:
            PIs['PI3_marg'] = (self.PI_results['default_repair']['PI3'] - PIs['PI3']) / self.PI_results['default_repair']['PI3']
        if self.PI_results['default_repair']['PI4'] <= 0:
            PIs['PI4_marg'] = (- PIs['PI4']) / 1
        else:
            PIs['PI4_marg'] = (self.PI_results['default_repair']['PI4'] - PIs['PI4']) / self.PI_results['default_repair']['PI4']

        PIs['LeakVolume_marg'] = (self.PI_results['default_repair']['leakvolume'] - leakvolume) / self.PI_results['default_repair']['leakvolume']

        Total_PI = PIs['PI1_marg'] * 5 + PIs['PI2_marg'] * 2 + PIs['PI3_marg'] * 2 + PIs['PI4_marg'] * 1 + PIs['LeakVolume_marg']*1  # objctive maximize total_PI
        Total_PI = PIs['PI1'] + PIs['PI2'] + PIs['PI3'] + PIs['PI4'] + leakvolume # objctive minimize total_PI
        return Total_PI

    def PI_Results(self, x):  # used to assess PI Results
        duration = int((self.simulationParameters['simulation_end_date'] - self.simulationParameters['simulation_start_date']).total_seconds())
        stepDuration = self.simulationParameters['hyd_time_step']
        awareness_sec = int((self.simulationParameters['awarenesstime'] - self.simulationParameters['simulation_start_date']).total_seconds())
        repair_start_sec = awareness_sec + (x[0] * 60 * 60)
        repair_end_sec = repair_start_sec + self.simulationParameters['repair_sec']
        leak_start_sec = int((self.simulationParameters['leak_start_date'] - self.simulationParameters['simulation_start_date']).total_seconds())
        self.load_epanetmodel()
        # start_time = datetime.datetime.now()
        leakIndex = en.getnodeindex(self.epanetmodel.proj_for_simulation, self.simulationParameters['leakNodeID'])
        pipeIndex = en.getlinkindex(self.epanetmodel.proj_for_simulation, self.simulationParameters['leakPipeID'])
        self.epanetmodel.set_time_param(enu.TimeParams.Duration, (duration))
        self.epanetmodel.set_time_param(enu.TimeParams.HydStep, (stepDuration))
        self.epanetmodel.set_time_param(enu.TimeParams.ReportStep, (stepDuration))
        self.epanetmodel.set_epanet_mode(enu.EpanetModes.PDA, pmin=3, preq=15, pexp=0.5)  # set demand mode
        # run simulation step-by-step
        en.openH(self.epanetmodel.proj_for_simulation)
        en.initH(self.epanetmodel.proj_for_simulation, en.NOSAVE)
        en.setoption(self.epanetmodel.proj_for_simulation, en.EMITEXPON, self.simulationParameters['leakExponent'])
        en.setoption(self.epanetmodel.proj_for_simulation, en.TRIALS, 100)  # reduce number of trials for convergence
        en.setoption(self.epanetmodel.proj_for_simulation, en.ACCURACY, 0.01)  # reduce accuracy required for convergence

        t = en.nextH(self.epanetmodel.proj_for_simulation)

        PIs = {'PI1': 0, 'PI2': 0, 'PI3': 0, 'PI4': 0}
        leakDemand_m3 = 0
        leakvolume = 0
        newDRscore = 0
        pipes = self.create_pipeDict()

        while t > 0:
            en.runH(self.epanetmodel.proj_for_simulation)
            hyd_sim_seconds = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.HTIME)
            report_step = hyd_sim_seconds / stepDuration
            if report_step == int(leak_start_sec / stepDuration):  # add orifice leak
                en.setnodevalue(self.epanetmodel.proj_for_simulation, leakIndex, en.EMITTER,
                                self.simulationParameters['leakEmitter'])
            if report_step == int(repair_start_sec / stepDuration):  # stop leak, close pipe for repair
                en.setnodevalue(self.epanetmodel.proj_for_simulation, leakIndex, en.EMITTER, 0.00000000001)  # stop pipe leak
                en.setlinkvalue(self.epanetmodel.proj_for_simulation, pipeIndex, en.STATUS, 0)  # 0 means closed, 1 means open
            if x[1] > 0:  # operate closed pipe
                operational_pipeIndex = en.getlinkindex(self.epanetmodel.proj_for_simulation,
                                                        self.simulationParameters['OperationalPipeIDs'][0])
                operate_pipe1_topen = awareness_sec + ((x[1] - 1) * 60 * 60)
                opreate_pipe1_tclose = awareness_sec + ((x[2] - 1) * 60 * 60)
                if report_step == int(operate_pipe1_topen / stepDuration):
                    en.setlinkvalue(self.epanetmodel.proj_for_simulation, operational_pipeIndex, en.STATUS, 1)  # 0 means closed, 1 means open
                if report_step == int(opreate_pipe1_tclose / stepDuration):
                    en.setlinkvalue(self.epanetmodel.proj_for_simulation, operational_pipeIndex, en.STATUS, 0)  # 0 means closed, 1 means open

            # PRV setting
            num_prvs = len(self.simulationParameters['OperationalPRVIDs'])
            for i in range(num_prvs):
                j = (i + 1) * 3  # prv location within X
                if x[j] != 2:  # operate closed pipe
                    operational_pipeIndex = en.getlinkindex(self.epanetmodel.proj_for_simulation,
                                                            self.simulationParameters['OperationalPRVIDs'][i])

                    initial_prv_setting = en.getlinkvalue(self.epanetmodel.proj_for_simulation,
                                                          operational_pipeIndex,
                                                          en.SETTING)
                    if x[j] == 0:
                        new_prv_setting = 0
                    if x[j] == 1:
                        new_prv_setting = 0.5
                    if x[j] == 3:
                        new_prv_setting = 1.5
                    if x[j] == 4:
                        new_prv_setting = 2

                    operate_prv_topen = awareness_sec + ((x[j + 1] - 1) * 60 * 60)
                    opreate_prv_tclose = awareness_sec + ((x[j + 2] - 1) * 60 * 60)
                    if report_step == int(operate_prv_topen / stepDuration):  # adjust PRV Setting
                        en.setlinkvalue(self.epanetmodel.proj_for_simulation, operational_pipeIndex,
                                        en.SETTING, round(initial_prv_setting * (new_prv_setting)))
                    if report_step == int(opreate_prv_tclose / stepDuration):
                        en.setlinkvalue(self.epanetmodel.proj_for_simulation, operational_pipeIndex,
                                        en.SETTING, initial_prv_setting)

            if report_step == int(repair_end_sec / stepDuration):  # open pipe that's been repaired
                en.setlinkvalue(self.epanetmodel.proj_for_simulation, pipeIndex, en.STATUS, 1)
            # calc PIs
            if hyd_sim_seconds >= awareness_sec:
                PI1, PI2, PI3_demand = self.PI_step()
                PIs['PI1'] = PIs['PI1'] + PI1 * stepDuration
                PIs['PI2'] = PIs['PI2'] + PI2 * stepDuration
                leakDemand_m3 = leakDemand_m3 + (PI3_demand * stepDuration / 1000)

            # calc leakage volume while leak is running
            if (hyd_sim_seconds >= awareness_sec) & (hyd_sim_seconds <= repair_start_sec):
                leak_pressure = en.getnodevalue(self.epanetmodel.proj_for_simulation, leakIndex, en.PRESSURE)
                leakflow = self.simulationParameters['leakEmitter'] * (
                        leak_pressure ** self.simulationParameters['leakExponent'])
                leakvolume = leakvolume + (leakflow * stepDuration / 1000)

            for pipe in pipes:
                velocity = en.getlinkvalue(self.epanetmodel.proj_for_simulation, pipe['index'], en.VELOCITY)
                if velocity > pipe['max_velocity']:
                    pipe['max_velocity'] = velocity

            t = en.nextH(self.epanetmodel.proj_for_simulation)
        self.epanetmodel = None

        for pipe in pipes:
            if pipe['max_velocity'] < 0.4:
                newDRscore = newDRscore + 1
            if 0.4 <= pipe['max_velocity'] < 0.8:
                newDRscore = newDRscore + 2
            if 0.8 <= pipe['max_velocity'] < 1.2:
                newDRscore = newDRscore + 3
            if 1.2 <= pipe['max_velocity'] < 1.6:
                newDRscore = newDRscore + 4
            if pipe['max_velocity'] >= 1.6:
                newDRscore = newDRscore + 5

        PIs['PI3'] = self.baseDemand_m3 - (leakDemand_m3 - leakvolume)
        if PIs['PI3'] < 0: #this occurs when pressure increases compared to original sim due to PRV operation.
            PIs['PI3'] = 0
        PIs['PI4'] = newDRscore - self.baseDRscore

        Total_PI = PIs['PI1'] + PIs['PI2'] + PIs['PI3'] + PIs['PI4'] + leakvolume # objctive minimize total_PI
        PI_IMM = {}
        PI_IMM['Interventions'] = self.num_interventions(x)
        PI_IMM['PI1_IMM'] = PIs['PI1']
        PI_IMM['PI2_IMM'] = PIs['PI2']
        PI_IMM['PI3_IMM'] = PIs['PI3']
        PI_IMM['PI4_IMM'] = PIs['PI4']
        PI_IMM['LeakVolume_IMM'] = leakvolume
        PI_IMM['Total_PI'] = Total_PI
        return PI_IMM

    def num_interventions(self, x):
        count = 1
        if x[1] > 0:
            count = 1 + count
        num_prvs = len(self.simulationParameters['OperationalPRVIDs'])
        for i in range(num_prvs):
            j = (i + 1) * 3  # prv location within X
            if x[j] != 2:  # operate closed pipe
                count = 1+count
        return count

    def create_pipeDict(self):
        pipes = en.getcount(self.epanetmodel.proj_for_simulation, en.LINKCOUNT) - 1
        pipe_list = []
        for pipe in range(1, pipes):
            pipe_dict = {}
            pipe_dict['index'] = pipe
            pipe_dict['max_velocity'] = 0
            pipe_dict['DR_BaseScore'] = 0
            pipe_list.append(pipe_dict)
        return pipe_list

    def calc_PIs(self,
                 duration: int,
                 stepDuration: int,
                 leakID: str,
                 leakEmitter: float,
                 leakStart_step: int,
                 leakExponent: Optional[float] = 0.99
                 ):
        self.load_epanetmodel()
        start_time = datetime.datetime.now()
        leakIndex = en.getnodeindex(self.epanetmodel.proj_for_simulation, leakID)
        self.epanetmodel.set_time_param(enu.TimeParams.Duration, (duration))  # set simulation duration for 15 days
        self.epanetmodel.set_time_param(enu.TimeParams.HydStep, (stepDuration))  # set hydraulic time step to 15min
        self.epanetmodel.set_time_param(enu.TimeParams.ReportStep, (stepDuration))  # set reporting time step to 15min
        self.epanetmodel.set_epanet_mode(enu.EpanetModes.PDA, pmin=3, preq=15, pexp=0.5)  # set demand mode
        # run simulation step-by-step
        en.openH(self.epanetmodel.proj_for_simulation)
        en.initH(self.epanetmodel.proj_for_simulation, en.NOSAVE)
        en.setoption(self.epanetmodel.proj_for_simulation, en.EMITEXPON, leakExponent)
        en.setoption(self.epanetmodel.proj_for_simulation, en.TRIALS, 100)  # reduce number of trials for convergence
        en.setoption(self.epanetmodel.proj_for_simulation, en.ACCURACY, 0.01)  # reduce accuracy required for convergence

        t = en.nextH(self.epanetmodel.proj_for_simulation)

        PIs = {'PI1': 0, 'PI2': 0, 'PI3': 0, 'PI4': 0}
        leakDemand_m3 = 0
        leakvolume = 0
        newDRscore = 0
        pipes = self.create_pipeDict()

        while t > 0:
            hyd_sim_seconds = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.HTIME)
            report_step = hyd_sim_seconds / stepDuration
            if report_step == (leakStart_step):  # add orifice leak
                en.setnodevalue(self.epanetmodel.proj_for_simulation, leakIndex, en.EMITTER, leakEmitter)
            en.runH(self.epanetmodel.proj_for_simulation)
            hyd_sim_seconds = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.HTIME)
            report_step = hyd_sim_seconds / stepDuration
            # calc PIs
            PI1, PI2, PI3_demand = self.PI_step()
            PIs['PI1'] = PIs['PI1'] + PI1 * stepDuration
            PIs['PI2'] = PIs['PI2'] + PI2 * stepDuration
            leakDemand_m3 = leakDemand_m3 + (PI3_demand * stepDuration / 1000)

            # calc leakage volume
            if report_step >= (leakStart_step):  # & report_step < leakEnd_step:
                leak_pressure = en.getnodevalue(self.epanetmodel.proj_for_simulation, leakIndex, en.PRESSURE)
                leakflow = leakEmitter * (leak_pressure ** leakExponent)
                leakvolume = leakvolume + (leakflow * stepDuration / 1000)

            for pipe in pipes:
                velocity = en.getlinkvalue(self.epanetmodel.proj_for_simulation, pipe['index'], en.VELOCITY)
                if velocity > pipe['max_velocity']:
                    pipe['max_velocity'] = velocity

            t = en.nextH(self.epanetmodel.proj_for_simulation)
        for pipe in pipes:
            if pipe['max_velocity'] < 0.4:
                newDRscore = newDRscore + 1
            if 0.4 <= pipe['max_velocity'] < 0.8:
                newDRscore = newDRscore + 2
            if 0.8 <= pipe['max_velocity'] < 1.2:
                newDRscore = newDRscore + 3
            if 1.2 <= pipe['max_velocity'] < 1.6:
                newDRscore = newDRscore + 4
            if pipe['max_velocity'] >= 1.6:
                newDRscore = newDRscore + 5

        PIs['PI3'] = self.baseDemand_m3 - (leakDemand_m3 - leakvolume)
        PIs['PI4'] = newDRscore - self.baseDRscore
        self.epanetmodel = None
        return PIs  # , self.baseDemand_m3, leakDemand_m3, leakvolume

    def PI_step(self, Pmin: Optional[int] = 3, Plow: Optional[int] = 7):  # lost service time (pressure<3m)
        PI1 = 0
        PI2 = 0
        PI3_leakdemand = 0
        for node in self.node_pop:
            PI3_leakdemand = PI3_leakdemand + en.getnodevalue(self.epanetmodel.proj_for_simulation, node['index'], en.DEMAND)
            if node['pop'] > 0:
                pressure = en.getnodevalue(self.epanetmodel.proj_for_simulation, node['index'], en.PRESSURE)
                if pressure < Pmin:
                    PI1 = PI1 + node['pop']
                if pressure < Plow:
                    PI2 = PI2 + node['pop']
        return PI1, PI2, PI3_leakdemand

# import epanet_fiware.epanetmodel
# import epanet_fiware.enumerations as enu
# import epanet_fiware.epanet_outfile_handler as outfile_handler
# import epanet.toolkit as en
# import pandas as pd
# import numpy as np
# import datetime
# from typing import Optional
# import multiprocess as mp
#
#
# #%%Set-up IMM class
# np.random.seed()
#
# inp_file = 'C:/Users/bs524/OneDrive - University of Exeter/Documents/Exeter/dev/packages/anomaly-detection/data/gt/309D07_DMA_wgs84_rev4b.inp'
# network_name = 'gt_DMA'
#
# sensors_0 = {'ID': 'Moortown_SR.3092019_7230.1','Type': 'flow'}
# sensors_1 = {'ID': '3092019_2290.3092019_2348.1','Type': 'flow'}
# sensors_2 = {'ID': '3092019_7481','Type': 'pressure'}
# sensors_3 = {'ID': '3092019_2136','Type': 'pressure'}
# sensors_4 = {'ID': '3092019_2604','Type': 'pressure'}
# sensors_5 = {'ID': '3092019_3276','Type': 'pressure'}
# sensors_6 = {'ID': '3092019_2291','Type': 'pressure'}
# sensors = [sensors_0, sensors_1, sensors_2, sensors_3 ,sensors_4,sensors_5, sensors_6]
#
# closed_pipe_ids = ['TestPipe']
# test = IMM_model(inp_file=inp_file, network_name=network_name, sensors=sensors)
# #%% Declare leaknodeID, LeakPipeID, awarenesstime, etc.
# test.set_simulation_Parameters(leakNodeID = '3092019_10352',
#                                leakPipeID='3092019_2256.3092019_2258.1',
#                                OperationalPipeIDs = closed_pipe_ids)
# #%% calc pop per node
# test.get_pop_per_node(total_population = 6053)
# #%% calc base demand and base velocity scores 48 hours after awarenesstime
# test.base_scenario_sim()
#
# #%%calc PIs for default pipe repair-leak scenario (i.e. repair pipe at time of awareness)
# test.default_repair_scenario() #need to double check this
#
# #%%Calc Objective function
# #input: only the X vector
# #run and calc PIS by compairing to PIS from default repair scenario
# #x array:
# # x0: repair start time (0-48)
# # x1: closed pipe 1: opening time (0-48)
# # x2: closed pipe 1: closing time (0-48)
#
# x=np.array([0,1,47])
# test.assess_IMM(x)
#
# #%% GA Set-up
# import numpy as np
# from pymoo.factory import get_algorithm, get_crossover, get_mutation, get_sampling
# from pymoo.optimize import minimize
# from pymoo.core.problem import ElementwiseProblem
# #from pymoo.core.problem import Problem
#
# NUM_closed_pipes = 1
# NUM_closed_pipe_constraints = 2*NUM_closed_pipes
# NUM_PipeRepair_constraints = 1
# repairDuration = 4 #pipe repair duration assumed to be 4hrs
#
# class MyProblem(ElementwiseProblem):
#     # Definition of a custom Knapsack problem
#     def __init__(self):
#         super().__init__(n_var = 1+NUM_closed_pipes*2,
#                          n_obj = 1,
#                          n_constr = NUM_PipeRepair_constraints + NUM_closed_pipe_constraints,
#                          xl = 0,
#                          xu = 48,
#                          type_var = int
#                          )
#
#     def _evaluate(self, X, out, *args, **kwargs):
#         # Objective and Constraint functions
#         out["F"] = -test.assess_IMM(X)# Objective Value
#         #pipe_repair_1 = -X[0]+0.5 #<= 0 #pipe repair time must be greater than 0
#         pipe_repair_2 = X[0]+repairDuration-48 #<= 0 #pipe must be repaired within 48 hrs
#         closedPipe1_1 = -X[1]*100 + X[2] #<=0 #if pipe 1 start time = 0, then pipe 1 endtime = 0
#         closedPipe1_2 = X[1] - X[2] #<= 0 #closing time must occur > opening time
#         out["G"] = np.column_stack([pipe_repair_2, closedPipe1_1, closedPipe1_2])
#
#
# #%% Solution
# start_time = datetime.datetime.now()
#
# method = get_algorithm("ga",
#                        pop_size=6,
#                        sampling=get_sampling("int_random"),
#                        crossover=get_crossover("int_sbx", prob=1.0, eta=3.0),
#                        mutation=get_mutation("int_pm", eta=3.0),
#                        eliminate_duplicates=True,
#                        )
#
# res = minimize(MyProblem(),
#                method,
#                termination=('n_gen', 11),
#                seed=1,
#                save_history=True
#                )
#
# print("Best solution found: %s" % res.X)
# print("Function value: %s" % res.F)
# print("Constraint violation: %s" % res.CV)
#
# simulationTime = datetime.datetime.now() - start_time
# print("Total training time: " + str(simulationTime))
#
#
# #%%Parallelized - doesn't work
# # from pymoo.factory import get_algorithm, get_crossover, get_mutation, get_sampling
# # from pymoo.optimize import minimize
# # from pymoo.core.problem import ElementwiseProblem
# # from pymoo.core.problem import starmap_parallelized_eval
# # from multiprocessing.pool import ThreadPool
# # import multiprocessing
# #
# #
# #
# # NUM_closed_pipes = 1
# # NUM_closed_pipe_constraints = 2*NUM_closed_pipes
# # NUM_PipeRepair_constraints = 2
# # repairDuration = 4 #pipe repair duration assumed to be 4hrs
# #
# #
# #
# # # the number of processes to be used
# # n_proccess = 4
# # pool = multiprocessing.Pool(n_proccess)
# #
# #
# # class MyProblem(ElementwiseProblem):
# #     def __init__(self):
# #         super().__init__(n_var = 1+NUM_closed_pipes*2,
# #                          n_obj = 1,
# #                          n_constr = NUM_PipeRepair_constraints + NUM_closed_pipe_constraints,
# #                          xl = 0,
# #                          xu = 48,
# #                          type_var = int,
# #                          runner=pool.starmap,
# #                          func_eval = starmap_parallelized_eval
# #                          )
# #
# #     def _evaluate(self, X, out, *args, **kwargs):
# #         # Objective and Constraint functions
# #         out["F"] = -test.assess_IMM(X)# Objective Value
# #         pipe_repair_1 = -X[0]+0.5 #<= 0 #pipe repair time must be greater than 0
# #         pipe_repair_2 = X[0]+repairDuration-48 #<= 0 #pipe must be repaired within 48 hrs
# #         closedPipe1_1 = -X[1]*100 + X[2] #<=0 #if pipe 1 start time = 0, then pipe 1 endtime = 0
# #         closedPipe1_2 = X[1] - X[2] #<= 0 #closing time must occur > opening time
# #         out["G"] = np.column_stack([pipe_repair_1, pipe_repair_2, closedPipe1_1, closedPipe1_2])
# #
# #
# # #%%
# #
# # #solve solution
# # method = get_algorithm("ga",
# #                        pop_size=5,
# #                        sampling=get_sampling("int_random"),
# #                        crossover=get_crossover("int_sbx", prob=1.0, eta=3.0),
# #                        mutation=get_mutation("int_pm", eta=3.0),
# #                        eliminate_duplicates=True,
# #                        )
# #
# # res = minimize(MyProblem(),
# #                method,
# #                termination=('n_gen', 5),
# #                seed=1,
# #                save_history=True
# #                )
# #
# # pool.close()
# # print("Best solution found: %s" % res.X)
# # print("Function value: %s" % res.F)
# # print("Constraint violation: %s" % res.CV)
# #%% Visualization of Convergence
#
# import matplotlib.pyplot as plt
# # number of evaluations in each generation
# n_evals = np.array([e.evaluator.n_eval for e in res.history])
# # optimum value in each generation
# opt = np.array([e.opt[0].F for e in res.history])
#
# plt.title("Convergence")
# plt.plot(n_evals, opt, "--")
# plt.show()


#--------------------------------------------------------------------------------------------------------------------------
# GARETH -I've moved the testbed code into here to make it easier to work with

import os
import inspect
import unexefiware.fiwarewrapper
import unexeaqua3s.immwrapper_mo

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
    resource_manager.init(url=os.environ['DEVICE_BROKER'], file_root=os.environ['FILE_PATH']+'/visualiser', fiware_service_list=fiware_service_list)
    resource_manager.has_loaded_content = True

    try:
        water_network = resource_manager.resources[fiware_service]['epanet']
        inp_file = water_network.epanetmodel.inp_file
        return inp_file
    except Exception as e:
        print('Pilot has no water network!')
        return

    #simulation_model = unexeaqua3s.epanet_data_generator.simulation_model(epanet_model, sensors)


def testbed(fiware_service):

    quitApp = False
    imm = unexeaqua3s.immwrapper_mo.IMM_Wrapper()

    if 'new_solutions' in imm.results and imm.results['new_solutions'] is not None:
        for result in imm.results['new_solutions']:
            print(str(result))

    while quitApp is False:
        print('aqua3s:' + '\n')

        print('\nIMM Testbed')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])

        if imm.results['found_solution'] == True:
            if 'new_solutions' in imm.results and imm.results['new_solutions'] is not None:
                for result in imm.results['new_solutions']:
                    print(str(result))

            print()
            print(str(imm.results))
            print()
        else:
            for step in imm.results['diagnostics']:
                print(step)

        print('\n')
        print('1..Calculate IMM Solution')
        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            try:
                #collect epanet model from contextbroker - could rewrite this hardcoded?
                #GARETH - make this on the AAA testbed
                #fiware_service = 'P2B'
                #inp_file = '/docker/aqua3s-brett-test//visualiser/data/' + fiware_service + '/waternetwork/epanet.inp'
                inp_file = os.environ['FILE_PATH'] + '/visualiser/data/' + fiware_service + '/waternetwork/epanet.inp'
                #inp_file = inp_file_location(fiware_wrapper, fiware_service)

                imm.do_it(fiware_service= fiware_service, #self.pilot_name,
                          leakPipeID='14',
                          repair_duration_hours= 12,
                          n_solutions = 5,
                          logger=unexefiware.base_logger.BaseLogger())

                if True:
                    if imm.results['found_solution'] == True:
                        if 'new_solutions' in imm.results and imm.results['new_solutions'] is not None:
                            for result in imm.results['new_solutions']:
                                print(str(result))

                    else:
                        for step in imm.results['diagnostics']:
                            print(step)

                    if 'solutions' in imm.results:
                        for solution in imm.results['solutions']:
                            for step in solution:
                                print(step)

                            print()
                    else:

                        for step in imm.results['diagnostics']:
                            print(step)

                    print()

                print()

            except Exception as e:
                logger = unexefiware.base_logger.BaseLogger()
                logger.exception(inspect.currentframe(),e)

        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    logger = unexefiware.base_logger.BaseLogger()

    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    fiware_wrapper.init(logger=logger)
    fiware_service = 'AAA'

    testbed(fiware_wrapper, fiware_service)
