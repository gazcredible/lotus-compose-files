import epanet_fiware.epanetmodel
import epanet_fiware.enumerations as enu
import epanet_fiware.epanet_outfile_handler as outfile_handler
import epanet.toolkit as en #no function written in epanetmodel for pattern creation
import datetime
import pandas as pd
import numpy as np
from scipy.stats import truncnorm
from typing import Optional
#create functions to generate dataframes for testbed analysis
#create leak scenarios
#create non-leak scenario
class simulation_model:
    def __init__(self,
                 epanetmodel,
                 sensors: list
                 ):
        self.sensors = sensors
        self.model = epanetmodel
        self.get_sensor_indices()

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

    def normal_scenario(self,
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
        #self.add_demand_noise()  #not adding demand noise for TTT casestudy

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
                self.add_demand_noise2()
                old_date = report_date
        # en.close(self.model.proj_for_simulation)
        # self._epanetmodel()
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

    def simulate_leak(self,
                       stepDuration: int,
                       leakID: str,
                       leakEmitter: float,
                       sigma: Optional[float]= 0.5,
                       leakExponent: Optional[float] = 0.99,
                       start_date: Optional[datetime.datetime] = datetime.datetime(2022, 2, 25),
                       end_date: Optional[datetime.datetime] = datetime.datetime(2022, 4, 1),
                       leakdate: Optional[datetime.datetime] = datetime.datetime(2022, 3, 1, 14,0,0)
                       ):
        comp_time = datetime.datetime.now()
        leakStart_step = int((leakdate - start_date).total_seconds()//stepDuration)
        duration = int((end_date - start_date).total_seconds())
        leakIndex = en.getnodeindex(self.model.proj_for_simulation, leakID)

        self.model.set_time_param(enu.TimeParams.Duration, duration)  # set simulation duration for 15 days
        self.model.set_time_param(enu.TimeParams.HydStep, stepDuration)  # set hydraulic time step to 15min
        self.model.set_time_param(enu.TimeParams.ReportStep, stepDuration)  # set reporting time step to 15min
        self.model.set_epanet_mode(enu.EpanetModes.PDA, pmin=3, preq=15, pexp=0.5)  # set demand mode
        en.openH(self.model.proj_for_simulation)
        en.initH(self.model.proj_for_simulation, en.NOSAVE)
        en.setoption(self.model.proj_for_simulation, en.EMITEXPON, leakExponent)
        en.setoption(self.model.proj_for_simulation, en.TRIALS, 10)  # reduce number of trials for convergence
        en.setoption(self.model.proj_for_simulation, en.ACCURACY, 0.01)  # reduce accuracy required for convergence

        old_date = start_date.date() #Simulation starts on Jan 1
        #self.add_demand_noise()  #not adding demand noise for TTT casestudy

        t = en.nextH(self.model.proj_for_simulation)
        rows = []
        while t > 0:
            en.runH(self.model.proj_for_simulation)
            hyd_sim_seconds = en.gettimeparam(self.model.proj_for_simulation, en.HTIME)
            report_time = start_date + datetime.timedelta(seconds=hyd_sim_seconds)
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
                #self.add_demand_noise2()
                old_date = report_date

            # add orifice leak
            if report_step == (leakStart_step - 1):
                en.setnodevalue(self.model.proj_for_simulation, leakIndex, en.EMITTER, leakEmitter)

            # get leak flow rate 1 hr after start
            if report_step == (leakStart_step + 4):
                pressure = en.getnodevalue(self.model.proj_for_simulation, leakIndex, en.PRESSURE)
                if pressure < 0:
                    pressure == 0
                leakflow = leakEmitter * (pressure ** leakExponent)

        # en.close(self.model.proj_for_simulation)
        # self._epanetmodel()
        df = pd.DataFrame(rows, columns=['ReportStep', 'ReportTime', 'Sensor_ID', 'Sensor_type', 'Read'])
        # add sensor noise
        bounds = 2
        noise = truncnorm(a=-bounds / sigma, b=+bounds / sigma, scale=sigma).rvs(df.shape[0])
        df['Read_noise'] = noise + df['Read']

        print("Simulation Time: " + str(datetime.datetime.now() - comp_time))
        print("Leak Start Time: " + str(leakdate))
        print("Leak Flow Rate: " + str(leakflow) + " LPS")
        return df

    def add_demand_noise2(self):
        scale = 0.25
        bounds = 0.6
        #noise = truncnorm(a=-bounds / scale, b=+bounds / scale, scale=scale).rvs(size=1)
        noise = 0
        junctIDs = self.model.get_node_ids(enu.NodeTypes.Junction)
        for junctID in junctIDs:
            demand = self.model.get_node_property(junctID,enu.JunctionProperties.BaseDemand)
            demand_value = float(demand * (1 + noise))
            self.model.set_node_property(junctID,enu.JunctionProperties.BaseDemand, demand_value)




