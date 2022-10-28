import epanet_fiware.epanetmodel
import epanet_fiware.enumerations as enu
import epanet_fiware.epanet_outfile_handler as outfile_handler
import epanet.toolkit as en #no function written in epanetmodel for pattern creation
import datetime
import pandas as pd
import numpy as np
from scipy.stats import truncnorm
from typing import Optional
import time
from scipy.optimize import minimize, dual_annealing, basinhopping
from epanet_fiware.epanetmodel import EPAnetModel

#%%
class AnomalyDetection_Model:
    def __init__(self,
                 inp_file: str,
                 network_name: str,
                 sensors: list
                 ):
        self.inp_file = inp_file
        self.network_name = network_name
        self.model = None
        self.sensors = sensors
        self.dataSimulation = {}
        self.detectionParameters ={}
        self.detectionSimulationResults ={}
        self.dataReal = None
        self._epanetmodel()

    def _epanetmodel(self):
        self.model = epanet_fiware.epanetmodel.EPAnetModel(self.network_name, self.inp_file)

    def get_sensor_indices(self):
        for i in range(len(self.sensors)):
            if self.sensors[i]['Type'] == 'pressure':
                self.sensors[i]['Index'] = en.getnodeindex(self.model.proj_for_simulation, self.sensors[i]['ID'])
            if self.sensors[i]['Type'] == 'flow':
                self.sensors[i]['Index'] = en.getlinkindex(self.model.proj_for_simulation, self.sensors[i]['ID'])

    def get_sensor_data(self, report_steps, stepDuration, simulation_date):
        rows = []
        for sensor in self.sensors:
            if sensor['Type'] == 'pressure':
                for report_step in range(report_steps):
                    sensor_type = sensor['Type']
                    read = self.model.get_node_result(report_step, outfile_handler.NodeResultLabels.Pressure,
                                                      node_id=sensor['ID'])
                    report_time = simulation_date + datetime.timedelta(0, report_step * stepDuration)
                    rows.append([report_step, report_time, sensor['ID'], sensor_type, read])
            if sensor['Type'] == 'flow':
                for report_step in range(report_steps):
                    sensor_type = sensor['Type']
                    read = self.model.get_link_result(report_step, outfile_handler.LinkResultLabels.Flow,
                                                      link_id=sensor['ID'])
                    report_time = simulation_date + datetime.timedelta(0, report_step * stepDuration)
                    rows.append([report_step, report_time, sensor['ID'], sensor_type, read])

        df = pd.DataFrame(rows, columns=['ReportStep', 'ReportTime', 'Sensor_ID', 'Sensor_type', 'Read'])
        return df

    def sim_noleak_steps(self,
                    stepDuration: Optional[int] = 15*60,
                    simulation_date: Optional[datetime.datetime] = datetime.datetime(2021,1,1),
                    duration: Optional[int] = 26*7 * 24 * 60 * 60,  # 1 year
                    sigma: Optional[float] = 0.5
                    ):
        start_time = datetime.datetime.now()
        self.model.set_time_param(enu.TimeParams.Duration, duration)  # set simulation duration for 15 days
        self.model.set_time_param(enu.TimeParams.HydStep, stepDuration)  # set hydraulic time step to 15min
        self.model.set_time_param(enu.TimeParams.ReportStep, stepDuration)  # set reporting time step to 15min
        self.model.set_epanet_mode(enu.EpanetModes.PDA)  # set demand mode
        en.openH(self.model.proj_for_simulation)
        en.initH(self.model.proj_for_simulation, en.NOSAVE)
        old_date = simulation_date.date()
        if self.network_name != "TTT":
            self.add_demand_noise2()
        #en.saveinpfile(self.model.proj_for_simulation, "testinp")

        t = en.nextH(self.model.proj_for_simulation)
        rows = []
        while t > 0:
            en.runH(self.model.proj_for_simulation)
            hyd_sim_seconds = en.gettimeparam(self.model.proj_for_simulation, en.HTIME)
            report_time = simulation_date + datetime.timedelta(seconds=hyd_sim_seconds)
            report_date = report_time.date()
            report_step = hyd_sim_seconds / stepDuration
            t = en.nextH(self.model.proj_for_simulation)
            # get sensor data
            for sensor in self.sensors:
                if sensor['Type'] == 'pressure':
                    read = en.getnodevalue(self.model.proj_for_simulation, sensor['Index'], en.PRESSURE)
                    rows.append([report_step, report_time, sensor['ID'], sensor['Type'], read])

                if sensor['Type'] == 'flow':
                    read = en.getlinkvalue(self.model.proj_for_simulation, sensor['Index'], en.FLOW)
                    rows.append([report_step, report_time, sensor['ID'], sensor['Type'], read])
            # add noise via patterns for every 24 hours / new date
            if old_date != report_date:
                if self.network_name != "TTT":
                    self.add_demand_noise2()
                old_date = report_date
        en.close(self.model.proj_for_simulation)
        self._epanetmodel()
        df = pd.DataFrame(rows, columns=['ReportStep', 'ReportTime', 'Sensor_ID', 'Sensor_type', 'Read'])
        # add sensor noise
        bounds = 2
        noise = truncnorm(a=-bounds / sigma, b=+bounds / sigma, scale=sigma).rvs(df.shape[0])
        df['Read_noise'] = noise + df['Read']

        # group by every timestamp (day of week, hour and minute) and sensor ID, calc avg. Pressure
        df['timestamp'] = df['ReportTime'].dt.strftime("%A-%H:%M")
        df = df.assign(
            Read_avg=
            df.groupby(['timestamp', 'Sensor_ID'])
                .Read_noise
                .transform('mean')
        )
        # calc std. Pressure
        df = df.assign(
            Read_std=
            df.groupby(['timestamp', 'Sensor_ID'])
                .Read_noise
                .transform('std')
        )
        df['z'] = (df['Read_noise'] - df['Read_avg']) / df['Read_std']
        print("No Leak Simulation Time: " + str(datetime.datetime.now() - start_time))
        return df


    def sim_noleaks(self,
                    stepDuration: Optional[int] = 15*60,
                    simulation_date: Optional[datetime.datetime] = datetime.datetime(2021,1,1),
                    duration: Optional[int] = 7 * 24 * 60 * 60,  # 1 year
                    sigma: Optional[float] = 0.5
                    ):
        report_steps = int(duration / stepDuration)
        self.model.set_time_param(enu.TimeParams.Duration, duration)  # set simulation duration for 15 days
        self.model.set_time_param(enu.TimeParams.HydStep, stepDuration)  # set hydraulic time step to 15min
        self.model.set_time_param(enu.TimeParams.ReportStep, stepDuration)  # set reporting time step to 15min
        self.model.set_epanet_mode(enu.EpanetModes.DDA)  # set demand mode
        simulation_date = simulation_date - datetime.timedelta(days=7)
        #run 52 - 1 week simulations
        for i in range(5):
            simulation_date = simulation_date + datetime.timedelta(days=7)
            self.add_demand_noise()
            self.model.simulate_full()  # run simulation
            df_i = self.get_sensor_data(report_steps, stepDuration, simulation_date) #get sensor data
            # add sensor noise
            bounds = 2
            noise = truncnorm(a=-bounds / sigma, b=+bounds / sigma, scale=sigma).rvs(df_i.shape[0])
            df_i['Read_noise'] = noise + df_i['Read']
            if i == 0:
                df = df_i.copy()
            else:
                df = pd.concat([df,df_i], ignore_index=True)

        # group by every timestamp (day of week, hour and minute) and sensor ID, calc avg. Pressure
        df['timestamp'] = df['ReportTime'].dt.strftime("%A-%H:%M")
        df = df.assign(
            Read_avg=
            df.groupby(['timestamp', 'Sensor_ID'])
                .Read_noise
                .transform('mean')
        )
        # calc std. Pressure
        df = df.assign(
            Read_std=
            df.groupby(['timestamp', 'Sensor_ID'])
                .Read_noise
                .transform('std')
        )
        df['z'] = (df['Read_noise'] - df['Read_avg']) / df['Read_std']
        return df

    def _generate_leakstart(self, duration: int):
        leakStart_sec = int(np.random.uniform(low=2 * 24 * 60 * 60, high=(duration - 2 * 24 * 60 * 60), size=None))
        return leakStart_sec

    def _generate_leaksize(self,
                           min: Optional[float] = 0.5,
                           max: Optional[float] = 1.25):
        leakDemand = np.random.uniform(low=min, high=max, size=None)
        return leakDemand

    def add_demand_noise(self):
        num_patterns = en.getcount(self.model.proj_for_simulation, en.PATCOUNT)
        scale = 0.25
        bounds = 0.6
        for pattern_index in range(1,(num_patterns+1)):
            pattern_length = en.getpatternlen(self.model.proj_for_simulation, pattern_index)
            new_pattern = []
            for pattern_step in range(1,(pattern_length+1)):
                pattern_value = en.getpatternvalue(self.model.proj_for_simulation, pattern_index, pattern_step)
                noise = truncnorm(a=-bounds/scale, b=+bounds/scale, scale=scale).rvs(size=1)
                pattern_value = float(pattern_value * (1+noise))
                new_pattern.append(pattern_value)
                en.setpatternvalue(self.model.proj_for_simulation,pattern_index,pattern_step,pattern_value)
            #en.setpattern(self.model.proj_for_simulation, pattern_index, new_pattern, len(new_pattern))

    def add_demand_noise2(self):
        scale = 0.001 #0.25
        bounds = 0.001#0.6
        noise = truncnorm(a=-bounds / scale, b=+bounds / scale, scale=scale).rvs(size=1)
        noise = 0
        junctIDs = self.model.get_node_ids(enu.NodeTypes.Junction)
        for junctID in junctIDs:
        #for i in range(200):
        #    junctID = np.random.choice(junctIDs)
            demand = self.model.get_node_property(junctID,enu.JunctionProperties.BaseDemand)
            demand_value = float(demand * (1 + noise))
            self.model.set_node_property(junctID,enu.JunctionProperties.BaseDemand, demand_value)

    def sim_leak_steps(self,
                       duration: int,
                       stepDuration: int,
                       simulation_date: datetime,
                       leakID: str,
                       leakEmitter: float,
                       leakStart_step: int,
                       sigma: float,
                       leakExponent: Optional[float] = 0.99
                       ):
        start_time = datetime.datetime.now()
        leakIndex = en.getnodeindex(self.model.proj_for_simulation, leakID)
        self.model.set_time_param(enu.TimeParams.Duration, (duration))  # set simulation duration for 15 days
        self.model.set_time_param(enu.TimeParams.HydStep, (stepDuration))  # set hydraulic time step to 15min
        self.model.set_time_param(enu.TimeParams.ReportStep, (stepDuration))  # set reporting time step to 15min
        self.model.set_epanet_mode(enu.EpanetModes.PDA)  # set demand mode
        #run simulation step-by-step
        en.openH(self.model.proj_for_simulation)
        en.initH(self.model.proj_for_simulation, en.NOSAVE)
        en.setoption(self.model.proj_for_simulation, en.EMITEXPON, leakExponent)
        old_date = simulation_date.date()
        self.add_demand_noise2()
        t = en.nextH(self.model.proj_for_simulation)
        rows = []
        while t > 0:
            en.runH(self.model.proj_for_simulation)
            hyd_sim_seconds = en.gettimeparam(self.model.proj_for_simulation, en.HTIME)
            report_time = simulation_date + datetime.timedelta(seconds=hyd_sim_seconds)
            report_date = report_time.date()
            report_step = hyd_sim_seconds / stepDuration
            #get sensor data
            for sensor in self.sensors:
                if sensor['Type'] == 'pressure':
                    read = en.getnodevalue(self.model.proj_for_simulation, sensor['Index'], en.PRESSURE)
                    rows.append([report_step, report_time, sensor['ID'], sensor['Type'], read])

                if sensor['Type'] == 'flow':
                    read = en.getlinkvalue(self.model.proj_for_simulation, sensor['Index'], en.FLOW)
                    rows.append([report_step, report_time, sensor['ID'], sensor['Type'], read])

            # add noise via patterns for every 24 hours / new date
            if old_date != report_date:
                self.add_demand_noise2()
                old_date = report_date

            #add orifice leak
            if report_step == (leakStart_step-1):
                en.setnodevalue(self.model.proj_for_simulation, leakIndex, en.EMITTER, leakEmitter)

            #get leak flow @ 1hr after start
            if report_step == (leakStart_step + 4):
                pressure = en.getnodevalue(self.model.proj_for_simulation,leakIndex,en.PRESSURE)
                if pressure < 0:
                        pressure = 0
                leakflow = leakEmitter*(pressure**leakExponent)

            t = en.nextH(self.model.proj_for_simulation)
        en.close(self.model.proj_for_simulation)
        self._epanetmodel()
        leak_df = pd.DataFrame(rows, columns=['ReportStep', 'ReportTime', 'Sensor_ID', 'Sensor_type', 'Read'])

        # add sensor noise
        bounds = 2
        noise = truncnorm(a=-bounds / sigma, b=+bounds / sigma, scale=sigma).rvs(leak_df.shape[0])
        leak_df['Read_noise'] = noise + leak_df['Read']

        # calc ewma
        leak_df['timestamp'] = leak_df['ReportTime'].dt.strftime("%A-%H:%M")
        # merge with no leak db to get avg and standard pressures for sensors
        try:
            leak_df = pd.merge(leak_df, self.dataSimulation['train_noleak']['noleakDB'][
                ['timestamp', 'Sensor_ID', 'Read_avg', 'Read_std']], on=['timestamp', 'Sensor_ID'],
                               how='left').drop_duplicates()
            leak_df['z'] = (leak_df['Read_noise'] - leak_df['Read_avg']) / leak_df['Read_std']
        except:
            print("Error: Simulate no leak training dateset first to develop avg sensor readings")
        print("Leak Simulation Time: " + str(datetime.datetime.now() - start_time))
        return leak_df, leakflow

    def sim_leak(self,
                 duration: int,
                 stepDuration: int,
                 simulation_date: datetime,
                 nodeID: str,
                 leakDemand: float,
                 leakStart_step: int,
                 sigma: float
                 ):
        report_steps = int(duration / stepDuration)
        nodeIndex = en.getnodeindex(self.model.proj_for_simulation, nodeID)

        # create leak pattern
        leakPattern = en.doubleArray(report_steps)
        for i in range(report_steps):
            if i < leakStart_step:
                leakPattern[i] = 0.0
            else:
                leakPattern[i] = 1.0

        try:
            patternIndex = en.getpatternindex(self.model.proj_for_simulation, "leaksim")
        except:
            en.addpattern(self.model.proj_for_simulation, "leaksim")
            patternIndex = en.getpatternindex(self.model.proj_for_simulation, "leaksim")

        en.setpattern(ph=self.model.proj_for_simulation, index=patternIndex, values=leakPattern, len=report_steps)

        # apply pattern to node
        en.adddemand(self.model.proj_for_simulation, nodeIndex, leakDemand, "leaksim", "leak")

        # run simulation
        self.model.set_time_param(enu.TimeParams.Duration, (duration))  # set simulation duration for 15 days
        self.model.set_time_param(enu.TimeParams.HydStep, (stepDuration))  # set hydraulic time step to 15min
        self.model.set_time_param(enu.TimeParams.ReportStep, (stepDuration))  # set reporting time step to 15min
        self.model.set_epanet_mode(enu.EpanetModes.DDA)  # set demand mode
        self.model.simulate_full()  # run simulation

        leak_df = self.get_sensor_data(report_steps, stepDuration, simulation_date) #get sensor data

        # add noise to sensor readings
        noise = np.random.normal(0, sigma, leak_df.shape[0])
        leak_df['Read_noise'] = noise + leak_df['Read']
        # calc ewma
        leak_df['timestamp'] = leak_df['ReportTime'].dt.strftime("%A-%H:%M")
        # merge with no leak db to get avg and standard pressures for sensors
        try:
            leak_df = pd.merge(leak_df, self.dataSimulation['train_noleak']['noleakDB'][['timestamp', 'Sensor_ID', 'Read_avg', 'Read_std']], on=['timestamp', 'Sensor_ID'],
                               how='left').drop_duplicates()
            leak_df['z'] = (leak_df['Read_noise'] - leak_df['Read_avg']) / leak_df['Read_std']
        except:
            print("Error: Simulate no leak training dateset first to develop avg sensor readings")
        return leak_df

    def sim_leaks(self,
                   leaks_simulated: int,
                   leak_nodes = None,
                   leakEmitter: Optional[float] = 0,
                   duration: Optional[int]=11*24*60*60,
                   stepDuration: Optional[int] = 15 * 60,
                   simulation_date: Optional[datetime.datetime] = datetime.datetime(2021, 1, 1),
                   sigma: Optional[float] = 0.5,
                   min_leak_lps: Optional[float] = 0.5,
                   max_leak_lps: Optional[float] = 1.25,
                   ):
        nodeIDs = self.model.get_node_ids(enu.NodeTypes.Junction)
        leaks = []
        if leak_nodes is None: #no leak nodes provided
             leak_nodes = np.random.choice(nodeIDs, leaks_simulated).tolist()

        for leak_id in leak_nodes:
            try:
                leakStart_sec = self._generate_leakstart(duration)
                leakStart_step = int(leakStart_sec / stepDuration)
                leakStart_date = simulation_date + datetime.timedelta(0, leakStart_step * stepDuration)

                # simulate leak and create database
                if leakEmitter > 0:
                    leakDB, leakflow = self.sim_leak_steps(duration, stepDuration, simulation_date, leak_id, leakEmitter, leakStart_step, sigma)
                if leakEmitter == 0: #run using min leak demand
                    leakDemand = self._generate_leaksize(min=min_leak_lps, max=max_leak_lps)
                    leakDB = self.sim_leak(duration, stepDuration, simulation_date, leak_id,
                                      leakDemand, leakStart_step, sigma)
                    leakflow = leakDemand
                leakDict = {
                    'nodeID': leak_id,
                    'leakStart': leakStart_date,
                    'leakDemand': leakflow,
                    'leakDB': leakDB
                }
                leaks.append(leakDict)
            except:
                print("error")
        return leaks

    def falsePositive(self,
                      df: pd.DataFrame,
                      cl: float):
        df['leakAlarm'] = np.where(abs(df['ewm']) > cl, 1, 0)
        df['date'] = df.ReportTime.apply(pd.datetime.date)
        df = df.groupby(['date'])['leakAlarm'].sum()  # false positives per day
        df[df >= 1] = 1
        fp = df.mean()  # fp = Avg. number of days with 1 or more false positives
        return fp

    # detect leaks
    def detect_leaks(self,
                     df: pd.DataFrame,
                     cl: float,
                     leakStartDate: datetime,
                     leakEndDate: datetime):
        df['leakAlarm'] = 0
        df['leakAlarm'] = np.where(abs(df['ewm']) > cl, 1, 0)
        df = df[(df.ReportTime > leakStartDate) & (df.ReportTime < leakEndDate)]
        df = df[(df.leakAlarm == 1)]
        if df.shape[0] > 0:
            leakDetect = 1
        else:
            leakDetect = 0
        return leakDetect

    # avg. detection time
    def get_detectionTime(self,
                          df: pd.DataFrame,
                          cl: float,
                          leakStartDate: datetime,
                          leakEndDate: datetime):
        df['leakAlarm'] = 0
        df['leakAlarm'] = np.where(abs(df['ewm']) > cl, 1, 0)
        df = df[(df.ReportTime > leakStartDate) & (df.ReportTime < leakEndDate)]
        df = df[(df.leakAlarm == 1)]
        if df.shape[0] > 0:
            detectTime = df['ReportTime'].min() - leakStartDate
        return detectTime.total_seconds()

    def calc_ewm(self,df: pd.DataFrame, alpha):
        df.sort_values('ReportTime')
        df['ewm'] = df.groupby(['Sensor_ID'])['z'].transform(lambda x: x.ewm(alpha=alpha, min_periods = 190).mean())
        return df

    def optimize_thresholds(self, x: list):  # output 1-balanced accuracy
        L = x[0]
        alpha = x[1]
        CL = L * ((alpha / (2 - alpha)) ** 0.5)
        self.dataSimulation['train_noleak']['noleakDB'] = self.calc_ewm(self.dataSimulation['train_noleak']['noleakDB'], alpha)
        fp = self.falsePositive(self.dataSimulation['train_noleak']['noleakDB'], CL)
        # calc detection-rate for leak scenarios:
        detection = []
        for leak in self.dataSimulation['train_leaks']:
            leak['leakDB'] = self.calc_ewm(leak['leakDB'], alpha)
            leakEndDate = leak['leakStart'] + datetime.timedelta(0, 2 * 24 * 60 * 60)
            ld = self.detect_leaks(leak['leakDB'], CL, leak['leakStart'], leakEndDate)
            detection.append(ld)
        dr = sum(detection) / float(len(detection))
        balancedAccuracy = (dr + (10*(1 - fp))) / 2
        return 1 - balancedAccuracy

    def optimize_gridsearch(self,
                            stepL: Optional[float] = 0.2,
                            stepA: Optional[float] = 0.1,
                            minL: Optional[float] = 2,
                            maxL: Optional[float] = 6,
                            minA: Optional[float] = 0.2,
                            maxA: Optional[float] = 0.9
                            ):
        sample = list()
        for L in np.arange(minL, maxL + stepL, stepL):
            for a in np.arange(minA, maxA + stepA, stepA):
                sample.append([L, a])

        sample_eval = [self.optimize_thresholds(x) for x in sample]

        best_ix = 0
        for i in range(len(sample)):
            if sample_eval[i] < sample_eval[best_ix]:
                best_ix = i
        # summarize best solution
        print('Best: f(%.5f,%.5f) = %.5f' % (sample[best_ix][0], sample[best_ix][1], sample_eval[best_ix]))
        self.detectionParameters['L'] = sample[best_ix][0]
        self.detectionParameters['alpha'] = sample[best_ix][1]
        self.detectionParameters['CL'] =  self.detectionParameters['L'] * ((self.detectionParameters['alpha'] / (2 - self.detectionParameters['alpha'])) ** 0.5)

    def training_accuracy(self):
        self.dataSimulation['train_noleak']['noleakDB'] = self.calc_ewm(self.dataSimulation['train_noleak']['noleakDB'], self.detectionParameters['alpha'])
        self.dataSimulation['train_noleak']['noleakDB']['leakAlarm'] = np.where(abs(self.dataSimulation['train_noleak']['noleakDB']['ewm']) > self.detectionParameters['CL'], 1, 0)
        fp = self.falsePositive(self.dataSimulation['train_noleak']['noleakDB'], self.detectionParameters['CL'])
        self.detectionSimulationResults['train'] = {}
        self.detectionSimulationResults['train']['false_positive'] = fp

        detection = []
        detectionTime = []
        for leak in self.dataSimulation['train_leaks']:
            leak['leakDB'] = leak['leakDB'].drop(['leakAlarm', 'ewm'], 1)
            leak['leakDB'] = self.calc_ewm(leak['leakDB'], self.detectionParameters['alpha'])
            leak['leakDB']['leakAlarm'] = np.where(abs(leak['leakDB']['ewm']) > self.detectionParameters['CL'], 1, 0)

            leakEndDate = leak['leakStart'] + datetime.timedelta(0, 2 * 24 * 60 * 60)
            ld = self.detect_leaks(leak['leakDB'], self.detectionParameters['CL'], leak['leakStart'], leakEndDate)
            detection.append(ld)
            try:
                dt = self.get_detectionTime(leak['leakDB'], self.detectionParameters['CL'], leak['leakStart'], leakEndDate)
                detectionTime.append(dt)
            except:
                print("detection time NA -  leak not detected")

        avg_detectionTime = sum(detectionTime) / len(detectionTime)
        dr = sum(detection) / float(len(detection))
        self.detectionSimulationResults['train']['Detection_Rate'] = dr
        self.detectionSimulationResults['train']['Avg_detectionTime'] = avg_detectionTime
        print("The percent of days with false positive leaks detected (during no-leak scenario) = ", fp)
        print("The percent of leaks detected within 2 days of leak start = ", dr)
        print("The average detection time in seconds is: ", avg_detectionTime)

    def testing_accuracy(self):
        self.dataSimulation['test_noleak']['noleakDB'] = self.calc_ewm(self.dataSimulation['test_noleak']['noleakDB'],
                                                                        self.detectionParameters['alpha'])
        self.dataSimulation['test_noleak']['noleakDB']['leakAlarm'] = np.where(
            abs(self.dataSimulation['test_noleak']['noleakDB']['ewm']) > self.detectionParameters['CL'], 1, 0)
        fp = self.falsePositive(self.dataSimulation['test_noleak']['noleakDB'], self.detectionParameters['CL'])
        self.detectionSimulationResults['test'] = {}
        self.detectionSimulationResults['test']['false_positive'] = fp

        detection = []
        detectionTime = []
        for leak in self.dataSimulation['test_leaks']:
            try:
                leak['leakDB'] = leak['leakDB'].drop(['leakAlarm', 'ewm'], 1)
            except:
                print("cant drop")
            leak['leakDB'] = self.calc_ewm(leak['leakDB'], self.detectionParameters['alpha'])
            leak['leakDB']['leakAlarm'] = np.where(abs(leak['leakDB']['ewm']) > self.detectionParameters['CL'], 1, 0)

            leakEndDate = leak['leakStart'] + datetime.timedelta(0, 2 * 24 * 60 * 60)
            ld = self.detect_leaks(leak['leakDB'], self.detectionParameters['CL'], leak['leakStart'], leakEndDate)
            detection.append(ld)
            try:
                dt = self.get_detectionTime(leak['leakDB'], self.detectionParameters['CL'], leak['leakStart'],
                                            leakEndDate)
                detectionTime.append(dt)
            except:
                print("detection time NA -  leak not detected")

        avg_detectionTime = sum(detectionTime) / len(detectionTime)
        dr = sum(detection) / float(len(detection))
        self.detectionSimulationResults['test']['Detection_Rate'] = dr
        self.detectionSimulationResults['test']['Avg_detectionTime'] = avg_detectionTime
        print("The percent of days with false positive leaks detected (during no-leak scenario) = ", fp)
        print("The percent of leaks detected within 2 days of leak start = ", dr)
        print("The average detection time in seconds is: ", avg_detectionTime)

    def build_dataset(self,
                      leak_nodes = None,
                      training_dataset: Optional[bool] =True,
                      testing_dataset: Optional[bool] = True,
                      leaks_simulated: Optional[int] = 100,
                      noise_sensor: Optional[float] = 0.5,
                      leakEmitter: Optional[float] = 0,
                      min_leak_lps: Optional[float] = 0.75,
                      max_leak_lps: Optional[float] = 2,
                      stepDuration: Optional[int] = 15 * 60,
                      simulation_date: Optional[datetime.datetime] = datetime.datetime(2021, 1, 1)
                      ):
        if training_dataset == True:
            #no leak data
            print("building no leak dataset")
            noleakDB = self.sim_noleak_steps(stepDuration=stepDuration,
                                        simulation_date=simulation_date,
                                        sigma=noise_sensor)
            noleakDict = {
                'noleakDB': noleakDB,
                'duration': '1 year',
                'reportStep': stepDuration
            }
            self.dataSimulation['train_noleak'] = noleakDict
            #leak data
            print("building leak dataset")

            self.dataSimulation['train_leaks'] = self.sim_leaks(leaks_simulated=leaks_simulated,
                                                               leakEmitter = leakEmitter,
                                                                stepDuration = stepDuration,
                                                                sigma= noise_sensor,
                                                                min_leak_lps = min_leak_lps,
                                                                max_leak_lps = max_leak_lps,
                                                                leak_nodes = leak_nodes)

        if testing_dataset == True:
            #no leak data
            noleakDB = self.sim_noleak_steps(stepDuration=stepDuration,
                                             simulation_date=simulation_date,
                                             sigma=noise_sensor)
            noleakDict = {
                'noleakDB': noleakDB,
                'duration': '1 year',
                'reportStep': stepDuration
            }
            self.dataSimulation['test_noleak'] = noleakDict
            # leak data
            self.dataSimulation['test_leaks'] = self.sim_leaks(leaks_simulated=leaks_simulated,
                                                                leakEmitter=leakEmitter,
                                                                stepDuration=stepDuration,
                                                                sigma=noise_sensor,
                                                                min_leak_lps=min_leak_lps,
                                                                max_leak_lps=max_leak_lps,
                                                                leak_nodes = leak_nodes)

# #%%
# np.random.seed()
#
# inp_file = 'C:/Users/bs524/OneDrive - University of Exeter/Documents/Exeter/dev/packages/anomaly-detection/data/gt/309D07_DMA_wgs84.inp'
# network_name = 'gt_DMA'
#
# sensors_0 = {'ID': 'Moortown_SR.3092019_7230.1','Type': 'flow'}
# sensors_1 = {'ID': '3092019_2290.3092019_2348.1','Type': 'flow'}
# sensors_2 = {'ID': '3092019_7481','Type': 'pressure'}
# sensors_3 = {'ID': '3092019_2136','Type': 'pressure'}
# sensors_4 = {'ID': '3092019_2604','Type': 'pressure'}
# sensors_5 = {'ID': '3092019_3276','Type': 'pressure'}
# sensors_6 = {'ID': '3092019_2291','Type': 'pressure'}
#
#
# sensors = [sensors_0, sensors_1, sensors_2, sensors_3 ,sensors_4,sensors_5, sensors_6]
# test = AnomalyDetection_Model(inp_file=inp_file, network_name=network_name, sensors=sensors)
#
# # #%% old Sensors
# # sensor_ids =[
# #     '3092019_2980',
# #     '3092019_2916',
# #     '3092019_1926',
# #     '3092019_1972',
# #     '3092019_2358'
# # ]
# #%%training
# test.get_sensor_indices()
# test.build_dataset(leaks_simulated = 100, leakEmitter=1, testing_dataset=False)
# #%%
# test.optimize_gridsearch()
# test.training_accuracy()
# #%%testing
# test.build_dataset(leaks_simulated = 100, leakEmitter=1, training_dataset=False)
# test.dataSimulation['test_noleak']['noleakDB'] = test.calc_ewm(test.dataSimulation['test_noleak']['noleakDB'],
#                                                                         test.detectionParameters['alpha'])
#
# #%%
# test.testing_accuracy()