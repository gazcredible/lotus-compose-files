import inspect

import epanet_fiware.epanetmodel
import epanet_fiware.enumerations as enu
import epanet.toolkit as en
import datetime
from typing import Optional


# %%
import unexefiware.base_logger


class IMM_model:
    def __init__(self,
                 inp_file: str,
                 network_name: str,
                 logger: unexefiware.base_logger.BaseLogger = None
                 ):
        self.inp_file = inp_file
        self.network_name = network_name
        self.epanetmodel = None
        self.simulationParameters = {}
        self.PI_results = {}
        self.baseDemand_m3 = None
        self.baseDRscore = None
        self.node_pop = None

        self.logger = logger

        if self.logger == None:
            self.logger = unexefiware.base_logger.BaseLogger()

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
        try:
            self.epanetmodel = epanet_fiware.epanetmodel.EPAnetModel(self.network_name, self.inp_file)
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

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
                self.setnodevalue(leakIndex, en.EMITTER, self.simulationParameters['leakEmitter'])
            if report_step == int(repair_start_sec / stepDuration):  # stop leak, close pipe
                self.setnodevalue(leakIndex, en.EMITTER, 0.00000000001)  # stop pipe leak - error with owa programming - 0 doesn't work.
                self.setlinkvalue(pipeIndex, en.STATUS, 0)  # 0 means closed, 1 means open
            if report_step == int(repair_end_sec / stepDuration):  # open pipe that's been repaired
                self.setlinkvalue(pipeIndex, en.STATUS, 1)
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
                self.setnodevalue(leakIndex, en.EMITTER, self.simulationParameters['leakEmitter'])
            if report_step == int(repair_start_sec / stepDuration):  # stop leak, close pipe for repair
                self.setnodevalue( leakIndex, en.EMITTER, 0.00000000001)  # stop pipe leak
                self.setlinkvalue(pipeIndex, en.STATUS, 0)  # 0 means closed, 1 means open
            if x[1] > 0:  # operate closed pipe
                operational_pipeIndex = en.getlinkindex(self.epanetmodel.proj_for_simulation,
                                                        self.simulationParameters['OperationalPipeIDs'][0])
                operate_pipe1_topen = awareness_sec + ((x[1] - 1) * 60 * 60)
                opreate_pipe1_tclose = awareness_sec + ((x[2] - 1) * 60 * 60)
                if report_step == int(operate_pipe1_topen / stepDuration):
                    self.setlinkvalue( operational_pipeIndex, en.STATUS, 1)  # 0 means closed, 1 means open
                if report_step == int(opreate_pipe1_tclose / stepDuration):
                    self.setlinkvalue( operational_pipeIndex, en.STATUS, 0)  # 0 means closed, 1 means open

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
                        self.setlinkvalue(operational_pipeIndex, en.SETTING, round(initial_prv_setting * (new_prv_setting)))

                    if report_step == int(opreate_prv_tclose / stepDuration):
                        self.setlinkvalue(operational_pipeIndex, en.SETTING, initial_prv_setting)

            if report_step == int(repair_end_sec / stepDuration):  # open pipe that's been repaired
                self.setlinkvalue( pipeIndex, en.STATUS, 1)

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
        if PIs['PI3'] < 0: #this occurs when pressure increases compared to original unexe_epanet due to PRV operation.
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

    def setnodevalue(self, leakIndex, thing, value):
        try:
            en.setnodevalue(self.epanetmodel.proj_for_simulation, leakIndex, thing, value)
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)
            self.logger.fail(inspect.currentframe(), 'leakindex:' + str(leakIndex))

    def setlinkvalue(self, pipeIndex, thing, value):
        try:
            en.setlinkvalue(self.epanetmodel.proj_for_simulation, pipeIndex, thing,value)  # 0 means closed, 1 means open
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)
            self.logger.fail(inspect.currentframe(), 'pipeIndex:' + str(pipeIndex))

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
                self.setnodevalue(leakIndex, en.EMITTER, self.simulationParameters['leakEmitter'])
            if report_step == int(repair_start_sec / stepDuration):  # stop leak, close pipe for repair
                self.setnodevalue(leakIndex, en.EMITTER, 0.00000000001)  # stop pipe leak
                self.setlinkvalue(pipeIndex, en.STATUS, 0)  # 0 means closed, 1 means open
            if x[1] > 0:  # operate closed pipe
                operational_pipeIndex = en.getlinkindex(self.epanetmodel.proj_for_simulation,
                                                        self.simulationParameters['OperationalPipeIDs'][0])
                operate_pipe1_topen = awareness_sec + ((x[1] - 1) * 60 * 60)
                opreate_pipe1_tclose = awareness_sec + ((x[2] - 1) * 60 * 60)
                if report_step == int(operate_pipe1_topen / stepDuration):
                    self.setlinkvalue(operational_pipeIndex, en.STATUS, 1)  # 0 means closed, 1 means open
                if report_step == int(opreate_pipe1_tclose / stepDuration):
                    self.setlinkvalue(operational_pipeIndex, en.STATUS, 0)  # 0 means closed, 1 means open

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
                        self.setlinkvalue( operational_pipeIndex, en.SETTING, round(initial_prv_setting * (new_prv_setting)))
                    if report_step == int(opreate_prv_tclose / stepDuration):
                        self.setlinkvalue( operational_pipeIndex, en.SETTING, initial_prv_setting)

            if report_step == int(repair_end_sec / stepDuration):  # open pipe that's been repaired
                self.setlinkvalue(pipeIndex, en.STATUS, 1)
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
        if PIs['PI3'] < 0: #this occurs when pressure increases compared to original unexe_epanet due to PRV operation.
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
                self.setnodevalue(leakIndex, en.EMITTER, leakEmitter)
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