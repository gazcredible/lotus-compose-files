import copy

import numpy

import anomalies.Anomaly_Localization_Class
import unexe_epanet.epanet_fiware
import datetime
import epanet_fiware.enumerations as enu
import pandas
import pandas as pd
import unexefiware.base_logger
import geopandas
import inspect
import json
import shapely
from allagash import Coverage, Problem
import pulp
from scipy.stats import truncnorm

import numpy as np
from typing import Optional
import matplotlib.pyplot as plt
import matplotlib.collections
import epanet.toolkit as en #no function written in epanetmodel for pattern creation

import math
import warnings
warnings.filterwarnings("ignore")

import sys
import os

class AnomalyLocalisation(anomalies.Anomaly_Localization_Class.AnomalyLocalization):
    def __init__(self,
                 inp_file: str,
                 network_name: str,
                 sensors: list,
                 proj_auth_code: str,
                 ):
        super().__init__(inp_file,network_name,sensors)

        self.proj_auth_code = proj_auth_code

        self.logger = unexefiware.base_logger.BaseLogger()

    def save_datafiles(self):
        self.simulationData['train_noleak'].to_pickle(self.network_name + "_train_noleak.pickle")
        self.simulationData['train_leaks'].to_pickle(self.network_name + "_train_leaks.pickle")
        self.simulationData['test_leaks'].to_pickle(self.network_name + "_test_leaks.pickle")

    def save_datafiles_json(self):
        self.save_to_json(self.simulationData['train_noleak'].to_json(), self.network_name + "_train_noleak.json")
        self.save_to_json(self.simulationData['train_leaks'].to_json(), self.network_name + "_train_leaks.json")
        self.save_to_json(self.simulationData['test_leaks'].to_json(), self.network_name + "_test_leaks.json")

    def load_datafiles(self):
        self.simulationData['train_noleak'] = pd.read_pickle(self.network_name + "_train_noleak.pickle")
        self.simulationData['train_leaks'] = pd.read_pickle(self.network_name + "_train_leaks.pickle")
        self.simulationData['test_leaks'] = pd.read_pickle(self.network_name + "_test_leaks.pickle")

    def save_to_json(self, json_data, filename):
        with open(filename, 'w') as f:
            f.write(json.dumps(json_data))

    def load_from_datafiles(self) ->  bool:
        return True

    def transform_coordinates(self, df):
        df['Long_meters'] = df['Long']
        df['Lat_meters'] = df['Lat']

        return df

    def MCLP(self, sample, number_of_cells, num_SA):
        # predict probabilities for sample
        prob_df = self.ML_predict_prob(sample)
        # prob_df = prob_df[prob_df.Probability >0.0001]
        # create grid
        grid = self.MCLP_create_grid(prob_df, number_of_cells)

        if isinstance(grid, geopandas.GeoDataFrame):
            # solve MCLP
            start_time = datetime.datetime.now()
            selected_areas = self.MCLP_solve(prob_df, grid, num_SA)
            simulationTime = datetime.datetime.now() - start_time
            print("MCLP Solver Time: " + str(simulationTime))
            return selected_areas

        return None

    def MCLP_create_grid(self, prob_df, number_of_cells:int=10):
        try:
            sw = shapely.geometry.Point((min(prob_df.Long_meters), min(prob_df.Lat_meters)))
            ne = shapely.geometry.Point((max(prob_df.Long_meters), max(prob_df.Lat_meters)))

            x_space = math.fabs(ne.x - sw.x)
            y_space = math.fabs(ne.y - sw.y)

            grid_spacing = max(x_space,y_space)
            grid_spacing /= number_of_cells
            search_radius = grid_spacing/2

            if ne.x == sw.x:
                ne = shapely.geometry.Point(ne.x + 2* search_radius, ne.y)

            if ne.y == sw.y:
                ne = shapely.geometry.Point(ne.x, ne.y + 2* search_radius)

            print(str(int((ne.x - sw.x)/grid_spacing)) + ':' + str(int((ne.y - sw.y)/grid_spacing)))
            gridpoints = []
            x = sw.x
            while x < ne.x:
                y = sw.y
                while y < ne.y:
                    p = shapely.geometry.Point(x, y).buffer(search_radius)
                    gridpoints.append(p)
                    y += grid_spacing
                x += grid_spacing

            if len(gridpoints) == 0:
                raise Exception('Empty grid!')

            grid = geopandas.GeoDataFrame(gridpoints)
            grid['ID'] = (grid.index).astype(int)
            grid = grid.rename(columns={0: "geometry"})
            grid = grid[['ID', 'geometry']]

            grid = grid.set_crs(crs=self.proj_auth_code)  # TTT coordinates in m

            return grid
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

        return None

    def MCLP_solve(self, prob_df, grid, num_SA):

        prob_gpd = geopandas.GeoDataFrame(prob_df,
                                      geometry=geopandas.points_from_xy(prob_df['Long_meters'], prob_df['Lat_meters']),
                                      crs=self.proj_auth_code)

        prob_gpd = prob_gpd[['Node', 'Probability', 'geometry']]
        #solve problem
        coverage = Coverage.from_geodataframes(prob_gpd, grid, "Node", "ID", demand_col="Probability",
                                                demand_name="demand")
        problem = Problem.mclp([coverage], max_supply={coverage: num_SA})

        problem.solve(pulp.PULP_CBC_CMD(msg=False)) #https://stackoverflow.com/questions/64215540/how-to-do-model-solve-not-show-any-message-in-python-using-pulp

        #output results
        selected_areas = problem.selected_supply(coverage)
        selected_areas = list(map(int, selected_areas))  # convert values in list to int
        selected_areas_df = grid[grid['ID'].isin(selected_areas)]

        #GARETH calculate probabilities ...
        try:
            selected_areas_df['Total_Probability'] = 0

            for _,row in prob_gpd.iterrows():
                if row['Probability'] > 0.01:
                    #print(row['Node'] + ' ' + str(round(row['Probability'],2)))

                    for i,area in  selected_areas_df.iterrows():
                        if row['geometry'].within(area['geometry']):
                            selected_areas_df.at[i, 'Total_Probability'] += row['Probability']

        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

        #covered_demand = prob_gpd.query(f"Node in ({[f'{j}' for j in problem.selected_demand(coverage)]})")
        #total_demand = covered_demand['Probability'].sum()
        #selected_areas_df['Total_Probability'] = total_demand
        return selected_areas_df

    def visualise_with_matplotlib(self, leak_coords:list=None, mclp_results:pandas.DataFrame=None, title:str=None):
        x = []
        y = []

        num_nodes = en.getcount(self.epanetmodel.proj_for_simulation, object=en.NODECOUNT) + 1
        for index in range(1, num_nodes):
            nodeID = en.getnodeid(self.epanetmodel.proj_for_simulation, index)
            coordinates = self.epanetmodel.get_node_property(nodeID, enu.JunctionProperties.Position)

            x.append(coordinates[0])
            y.append(coordinates[1])

        fig = plt.figure(dpi=200)
        ax = fig.add_subplot(1, 1, 1)

        #ax.plot(x, y, linewidth=0.1, c=[0, 1, 0, 1], zorder=1)
        ax.scatter(x, y, s=5, c=[[1, 0, 0, 1]], zorder=2)


        if isinstance(mclp_results, pandas.DataFrame):

            #for row in mclp_results.iterrows():
            #    ax.plot(*row[1]['geometry'].exterior.xy, c=[0,0,1,1], zorder=3)

            for _, row in mclp_results.iterrows():
                if row['Total_Probability'] > 0.01:
                    ax.plot(*row['geometry'].exterior.xy, c=[0, 0, 1, 1], zorder=3)

        if isinstance(leak_coords,list):
            ax.scatter(leak_coords[0], leak_coords[1], s=10, c=[[1, 1, 0, 1]], zorder=4)

        if True:
            xleft, xright = ax.get_xlim()
            ybottom, ytop = ax.get_ylim()
            ratio = 0.5
            ax.set_aspect(abs((xright - xleft) / (ybottom - ytop)) * ratio)

        if title:
            plt.title(title)

        plt.show()

    def build_datasets2(self,
                      simulation_date: datetime.datetime,
                      stepDuration: int,
                      leak_nodes=None,
                      noleak_dataset: Optional[bool] = True,
                      training_dataset: Optional[bool] = True,
                      testing_dataset: Optional[bool] = True,
                      noise_sensor: Optional[float] = 0.5,

                      testleaks: Optional[int] = 100
                      ):
        if noleak_dataset == True:
            print("building no leak dataset")
            noleakDB = self.sim_no_leak2(stepDuration=stepDuration,
                                        simulation_date=simulation_date,
                                        sigma=noise_sensor)
            self.simulationData['train_noleak'] = noleakDB

        if training_dataset == True:
            print("building leak training dataset")
            repeats = 5
            self.sim_leak_all_nodes2(stepDuration = stepDuration,
                                    simulation_date = simulation_date,
                                    sigma = noise_sensor,
                                    leak_nodes = leak_nodes,
                                    repeats=repeats)
        if testing_dataset == True:
            print("building leak testing dataset")
            repeats = 5
            self.sim_random_leaks2(nodes=testleaks,
                                  simulation_date = simulation_date,
                                  stepDuration=stepDuration,
                                  sigma=noise_sensor,
                                  leak_nodes = leak_nodes,
                                  repeats=repeats)


    def sim_no_leak2(self,
                     simulation_date: datetime.datetime,
                    stepDuration: int,
                    duration: Optional[int] = 52 * 7 * 24 * 60 * 60,  # 1 year
                    sigma: Optional[float] = 0.5
                    ):
        start_time = datetime.datetime.now()
        self.epanetmodel.set_time_param(enu.TimeParams.Duration, duration)  # set simulation duration for 15 days
        self.epanetmodel.set_time_param(enu.TimeParams.HydStep, stepDuration)  # set hydraulic time step to 15min
        self.epanetmodel.set_time_param(enu.TimeParams.ReportStep, stepDuration)  # set reporting time step to 15min
        self.epanetmodel.set_epanet_mode(enu.EpanetModes.PDA, pmin=3, preq=15, pexp=0.5)  # set to pressure driven analysis
        en.openH(self.epanetmodel.proj_for_simulation)
        en.initH(self.epanetmodel.proj_for_simulation, en.NOSAVE)
        old_date = simulation_date.date()
        self.add_demand_noise()

        t = en.nextH(self.epanetmodel.proj_for_simulation)
        rows = []
        while t > 0:
            en.runH(self.epanetmodel.proj_for_simulation)
            hyd_sim_seconds = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.HTIME)
            report_time = simulation_date + datetime.timedelta(seconds=hyd_sim_seconds)
            report_date = report_time.date()
            report_step = hyd_sim_seconds / stepDuration
            t = en.nextH(self.epanetmodel.proj_for_simulation)
            # get sensor data
            for sensor in self.sensors:
                if sensor['Type'] == 'pressure':
                    read = en.getnodevalue(self.epanetmodel.proj_for_simulation, sensor['Index'], en.PRESSURE)
                    rows.append([report_step, report_time, sensor['ID'], sensor['Type'], read])
                else:
                    if sensor['Type'] == 'flow':
                        read = en.getlinkvalue(self.epanetmodel.proj_for_simulation, sensor['Index'], en.FLOW)
                        rows.append([report_step, report_time, sensor['ID'], sensor['Type'], read])
                    else:
                        raise Exception('Sensor Type undefined')

            # add noise via patterns for every 24 hours / new date
            if old_date != report_date:
                self.add_demand_noise()
                old_date = report_date
        en.close(self.epanetmodel.proj_for_simulation)
        self.load_epanetmodel()
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
        # calc standard deviation
        df = df.assign(
            Read_std=
            df.groupby(['timestamp', 'Sensor_ID'])
                .Read_noise
                .transform('std')
        )
        df['z'] = (df['Read_noise'] - df['Read_avg']) / df['Read_std']
        print("No Leak Simulation Time: " + str(datetime.datetime.now() - start_time))
        return df

    def sim_leak_all_nodes2(self,
                   stepDuration: int,
                   simulation_date: datetime.datetime,
                   leak_nodes=None,
                   duration: Optional[int]=11*24*60*60,
                   repeats: Optional[int] = 20,
                   localizationWindow_sec: Optional[float] = 4 * 60 * 60,
                   leakEmitter: Optional[float] = 1,
                   sigma: Optional[float] = 0.5
                   ):
        nodeIDs = self.epanetmodel.get_node_ids(enu.NodeTypes.Junction)
        leaks = []
        if leak_nodes is None: #no leak nodes provided
             leak_nodes = nodeIDs
        i=0
        for nodeID in leak_nodes:
            print('Node ' + str(i) + " of "+ str(len(leak_nodes)) + ' ' +nodeID)
            i=i+1
            for repeat in range(repeats):
                try:
                    #3 period start time
                    # if repeat == 0 or repeat == 3:
                    #     leakstart_day = (int(np.random.uniform(low=2, high=(11-2), size=None)))*24*60*60
                    #     leakstart_hour = int(2*60*60)
                    #     leakStart_sec = leakstart_day + leakstart_hour
                    # if repeat == 1 or repeat == 4:
                    #     leakstart_day = (int(np.random.uniform(low=2, high=(11-2), size=None)))*24*60*60
                    #     leakstart_hour = int(14*60*60)
                    #     leakStart_sec = leakstart_day + leakstart_hour
                    # if repeat == 2 or repeat == 5:
                    #     leakstart_day = (int(np.random.uniform(low=2, high=(11-2), size=None)))*24*60*60
                    #     leakstart_hour = int(18*60*60)
                    #     leakStart_sec = leakstart_day + leakstart_hour

                    #random leak start time
                    leakstart_day = (int(np.random.uniform(low=2, high=(11 - 2), size=None))) * 24 * 60 * 60
                    leakstart_hour = (int(np.random.uniform(low=0, high=(23), size=None))) * (60 * 60)
                    leakStart_sec = leakstart_day + leakstart_hour
                    # leak parameters (start and size)
                    leakStart_step = int(leakStart_sec / stepDuration)
                    leakStart_date = simulation_date + datetime.timedelta(0, leakStart_step * stepDuration)

                    if repeat < (repeats/2):
                        leakEmitter = np.random.uniform(low = 1, high=4)
                    else:
                        leakEmitter = np.random.uniform(low = 5, high=8)

                    coordinates = self.epanetmodel.get_node_property(nodeID, enu.JunctionProperties.Position)
                    # simulate leak and create database
                    leakDB = self.sim_leak2(duration = duration, stepDuration = stepDuration, simulation_date = simulation_date, leakID= nodeID,
                                      leakEmitter= leakEmitter, leakStart_step = leakStart_step, sigma = sigma)
                    leakDB['leakNode'] = nodeID
                    leakDB['repeat'] = repeat
                    leakDB['leakEmitter'] = leakEmitter
                    leakDB['X-coord'] = coordinates[0]
                    leakDB['Y-coord'] = coordinates[1]

                    LeakDetectionTime_sec = np.random.uniform(low = 60*60, high=6*60*60)
                    leakDB = leakDB[leakDB['ReportTime'] > (leakStart_date + datetime.timedelta(0,LeakDetectionTime_sec-localizationWindow_sec))]
                    leakDB = leakDB[leakDB['ReportTime'] < (leakStart_date + datetime.timedelta(0,LeakDetectionTime_sec))]

                    leaks.append(leakDB)
                    #print("repeat "+ str(repeat) + " of" + str(repeats))
                except Exception as e:
                    self.logger.exception(inspect.currentframe(),e)
                    print("error simulating leak at Junction: " +nodeID)

        leakDB = pd.concat(leaks)
        self.simulationData['train_leaks'] = leakDB
        self.simulationData['train_leaks']['timeseries_id'] = self.simulationData['train_leaks']['leakNode'] + "_" + \
                                                              self.simulationData['train_leaks']['repeat'].astype(str)

    def sim_random_leaks2(self,
                         simulation_date: datetime.datetime,
                         stepDuration: int,
                         leak_nodes=None,
                         duration: Optional[int] = 11 * 24 * 60 * 60,


                         repeats: Optional[int] = 2,
                         nodes: Optional[int] = 100,
                         localizationWindow_sec: Optional[float] = 4 * 60 * 60,
                         sigma: Optional[float] = 0.5):
        nodeIDs = self.epanetmodel.get_node_ids(enu.NodeTypes.Junction)
        if leak_nodes is None: #no leak nodes provided
             leak_nodes = nodeIDs
        nodeIDs = leak_nodes
        #nodeIDs = random.sample(leak_nodes, nodes)
        leaks = []
        i = 0
        for nodeID in nodeIDs:
            print("node unexe_epanet " + str(i) + " of " + str(len(nodeIDs)))
            i = i + 1
            for repeat in range(repeats):
                try:
                    leakstart_day = (int(np.random.uniform(low=2, high=(11 - 2), size=None))) * 24 * 60 * 60
                    leakstart_hour = (int(np.random.uniform(low=0, high=(23), size=None)))*(60 * 60)
                    leakStart_sec = leakstart_day + leakstart_hour
                    # leak parameters (start and size)
                    leakStart_step = int(leakStart_sec / stepDuration)
                    leakStart_date = simulation_date + datetime.timedelta(0, leakStart_step * stepDuration)

                    if repeat == 0:
                        leakEmitter = np.random.uniform(low=1, high=4)
                    else:
                        leakEmitter = np.random.uniform(low=5, high=8)

                    coordinates = self.epanetmodel.get_node_property(nodeID, enu.JunctionProperties.Position)
                    # simulate leak and create database
                    leakDB = self.sim_leak2(duration=duration, stepDuration=stepDuration,
                                           simulation_date=simulation_date, leakID=nodeID,
                                           leakEmitter=leakEmitter, leakStart_step=leakStart_step, sigma=sigma)
                    leakDB['leakNode'] = nodeID
                    leakDB['repeat'] = repeat
                    leakDB['leakEmitter'] = leakEmitter
                    leakDB['X-coord'] = coordinates[0]
                    leakDB['Y-coord'] = coordinates[1]

                    LeakDetectionTime_sec = np.random.uniform(low=60 * 60, high=6 * 60 * 60)
                    leakDB = leakDB[leakDB['ReportTime'] > (leakStart_date + datetime.timedelta(0, LeakDetectionTime_sec - localizationWindow_sec))]
                    leakDB = leakDB[leakDB['ReportTime'] < (leakStart_date + datetime.timedelta(0, LeakDetectionTime_sec))]

                    leaks.append(leakDB)
                    #print("repeat " + str(repeat) + " of" + str(repeats))
                except:
                    print("error simulating leak at Junction: " + nodeID)

        leakDB = pd.concat(leaks)
        self.simulationData['test_leaks'] = leakDB
        self.simulationData['test_leaks']['timeseries_id'] = self.simulationData['test_leaks']['leakNode'] + "_" + \
                                                             self.simulationData['test_leaks']['repeat'].astype(str)

    def sim_leak2(self,
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
        leakIndex = en.getnodeindex(self.epanetmodel.proj_for_simulation, leakID)
        self.epanetmodel.set_time_param(enu.TimeParams.Duration, (duration))  # set simulation duration for 15 days
        self.epanetmodel.set_time_param(enu.TimeParams.HydStep, (stepDuration))  # set hydraulic time step to 15min
        self.epanetmodel.set_time_param(enu.TimeParams.ReportStep, (stepDuration))  # set reporting time step to 15min
        self.epanetmodel.set_epanet_mode(enu.EpanetModes.PDA, pmin=3, preq=15, pexp=0.5)  # set demand mode
        # run simulation step-by-step
        en.openH(self.epanetmodel.proj_for_simulation)
        en.initH(self.epanetmodel.proj_for_simulation, en.NOSAVE)
        en.setoption(self.epanetmodel.proj_for_simulation, en.EMITEXPON, leakExponent)
        en.setoption(self.epanetmodel.proj_for_simulation, en.TRIALS, 10) #reduce number of trials for convergence
        en.setoption(self.epanetmodel.proj_for_simulation, en.ACCURACY, 0.01) #reduce accuracy required for convergence

        old_date = simulation_date.date()
        self.add_demand_noise()
        #GARETH - this is ticking the sim by one step, so it's out by one all the time
        #t = en.nextH(self.epanetmodel.proj_for_simulation)
        t = 1
        rows = []
        while t > 0:
            en.runH(self.epanetmodel.proj_for_simulation)
            hyd_sim_seconds = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.HTIME)
            report_time = simulation_date + datetime.timedelta(seconds=hyd_sim_seconds)
            report_date = report_time.date()
            report_step = hyd_sim_seconds / stepDuration
            # get sensor data
            for sensor in self.sensors:
                if sensor['Type'] == 'pressure':
                    read = en.getnodevalue(self.epanetmodel.proj_for_simulation, sensor['Index'], en.PRESSURE)
                    rows.append([report_step, report_time, sensor['ID'], sensor['Type'], read])
                else:
                    if sensor['Type'] == 'flow':
                        read = en.getlinkvalue(self.epanetmodel.proj_for_simulation, sensor['Index'], en.FLOW)
                        rows.append([report_step, report_time, sensor['ID'], sensor['Type'], read])
                    else:
                        raise Exception
            # add noise via patterns for every 24 hours / new date
            if old_date != report_date:
                self.add_demand_noise()
                old_date = report_date

            # add orifice leak
            if report_step == (leakStart_step - 1):
                en.setnodevalue(self.epanetmodel.proj_for_simulation, leakIndex, en.EMITTER, leakEmitter)

            # get leak flow rate 1 hr after start
            if report_step == (leakStart_step + 4):
                pressure = en.getnodevalue(self.epanetmodel.proj_for_simulation,leakIndex,en.PRESSURE)
                if pressure < 0:
                        pressure == 0
                leakflow = leakEmitter*(pressure**leakExponent)

            t = en.nextH(self.epanetmodel.proj_for_simulation)
        en.close(self.epanetmodel.proj_for_simulation)
        self.load_epanetmodel()
        leak_df = pd.DataFrame(rows, columns=['ReportStep', 'ReportTime', 'Sensor_ID', 'Sensor_type', 'Read'])

        # add sensor noise
        bounds = 2
        noise = truncnorm(a=-bounds / sigma, b=+bounds / sigma, scale=sigma).rvs(leak_df.shape[0])
        leak_df['Read_noise'] = noise + leak_df['Read']
        leak_df['timestamp'] = leak_df['ReportTime'].dt.strftime("%A-%H:%M")
        leak_df['leakflow'] = leakflow

        # merge with no leak db to get avg and standard pressures for sensors
        try:
            leak_df = pd.merge(leak_df, self.simulationData['train_noleak'][
                ['timestamp', 'Sensor_ID', 'Read_avg', 'Read_std']], on=['timestamp', 'Sensor_ID'],
                               how='left').drop_duplicates()
            leak_df['z'] = (leak_df['Read_noise'] - leak_df['Read_avg']) / leak_df['Read_std']
            #print("Leak Simulation Time: " + str(datetime.datetime.now() - start_time))
            return leak_df
        except:
            print("Error: Simulate no leak training dateset first to develop avg sensor readings")



class epanet_anomaly_localisation:
    #GARETH -   this class is going to wrap Brett's original class as AnomalyLocalisation
    #           all the calls will go through it so we can isolate & understand what's going on
    def __init__(self):
        self.anomaly_localisation = None
        self.coord_system = None
        self.sim_inst = None

        self.logger = unexefiware.base_logger.BaseLogger()

    def init(self,sim_inst:unexe_epanet.epanet_fiware.epanet_fiware, sensor_list:list):
        self.anomaly_localisation = AnomalyLocalisation(inp_file=sim_inst.inp_file, network_name=sim_inst.fiware_service, sensors=sensor_list,proj_auth_code=sim_inst.coord_system)
        self.anomaly_localisation.get_sensor_indices()

        self.coord_system = sim_inst.coord_system
        self.sim_inst = sim_inst
    def build_datasets(self, simulation_date:datetime.datetime, stepDuration_as_seconds:float):
        start_time = datetime.datetime.now()
        self.anomaly_localisation.build_datasets2(simulation_date=simulation_date,
                                                 stepDuration = stepDuration_as_seconds,
                                                 leak_nodes=None,
                                                 noleak_dataset=True,
                                                 training_dataset=True,
                                                 testing_dataset=True,
                                                 testleaks= 20
                                                )

        simulationTime = datetime.datetime.now() - start_time

        self.anomaly_localisation.save_datafiles()
        #self.anomaly_localisation.save_datafiles_json()

    def load_datasets(self):
        self.anomaly_localisation.load_datafiles()


    def localise_leak(self, epanet_sensor_name:str, leak_df:pandas.DataFrame, leakwindow_start_date:datetime.datetime,leakwindow_end_date:datetime.datetime, number_of_cells:int):

        try:
            leakEmitter = 5

            leak_df['leakNode'] = epanet_sensor_name
            leak_df['leakEmitter'] = leakEmitter
            leak_df['X-coord'] = 'X'
            leak_df['Y-coord'] = 'Y'
            leak_df['timeseries_id'] = 'Test'
            # %%
            leak_df = leak_df[leak_df.ReportTime >= (leakwindow_start_date)]
            leak_df = leak_df[leak_df.ReportTime < (leakwindow_end_date)]

            leak_df2 = copy.deepcopy(leak_df)
            # %%
            sample, sample_answer = self.anomaly_localisation.ML_create_dataset(leak_df.copy())

            search_areas = self.anomaly_localisation.MCLP(sample=sample, number_of_cells=number_of_cells, num_SA=5)

            print(search_areas)

            self.visualise_with_matplotlib(mclp_results=search_areas, likelihood_cutoff=0.05, title='Sensor:'+str(epanet_sensor_name))

        except Exception as e:
            logger = unexefiware.base_logger.BaseLogger()
            logger.exception(inspect.currentframe(), e)
            logger.log(inspect.currentframe(), epanet_sensor_name)


    def run_leak_localisation_test(self, simulation_date:datetime.datetime, step_duration_in_min:int, leak_id:str):
        try:
            nodeIDs = self.anomaly_localisation.epanetmodel.get_node_ids(enu.NodeTypes.Junction)
            print('Leak: ' + leak_id)

            simulationstart_date = simulation_date
            leakstart_date = simulation_date + datetime.timedelta(weeks=1)
            leakwindow_start_date = leakstart_date + datetime.timedelta(hours=10)
            leakwindow_end_date = leakwindow_start_date + datetime.timedelta(hours=4.25)

            stepDuration = step_duration_in_min * 60
            leakstart_seconds = int((leakstart_date - simulationstart_date).total_seconds())
            leakStart_step = int(leakstart_seconds / stepDuration)

            # level of leak
            leakEmitter = 5

            # build leak data
            leak_df = self.anomaly_localisation.sim_leak2(duration=leakstart_seconds + (48 * 60 * 60),
                                    stepDuration=stepDuration,
                                    simulation_date=simulationstart_date,
                                    leakID=leak_id,
                                    leakEmitter=leakEmitter,
                                    leakStart_step=leakStart_step,
                                    sigma=0.5,
                                    leakExponent=0.99)

            leak_df['leakNode'] = leak_id
            leak_df['leakEmitter'] = leakEmitter
            leak_df['X-coord'] = 'X'
            leak_df['Y-coord'] = 'Y'
            leak_df['timeseries_id'] = 'Test'
            # %%
            leak_df = leak_df[leak_df.ReportTime >= (leakwindow_start_date)]
            leak_df = leak_df[leak_df.ReportTime < (leakwindow_end_date)]

            leak_df2 = copy.deepcopy(leak_df)
            # %%
            sample, sample_answer = self.anomaly_localisation.ML_create_dataset(leak_df.copy())




            coordinates = self.anomaly_localisation.epanetmodel.get_node_property(sample_answer[0], enu.JunctionProperties.Position)
            sample_answer = pd.DataFrame(sample_answer, columns=['Node_ID'], index=[0])
            sample_answer['Long'] = coordinates[0]
            sample_answer['Lat'] = coordinates[1]
            sample_answer = geopandas.GeoDataFrame(sample_answer,
                                                   geometry=geopandas.points_from_xy(sample_answer['Long'], sample_answer['Lat']),
                                                   crs=self.coord_system)

            r= 1000
            search_areas = self.anomaly_localisation.MCLP(sample=sample, grid_spacing=r*2, search_radius=r, num_SA=5)
            #search_areas = self.anomaly_localisation.MCLP(sample=sample, grid_spacing=100*10, search_radius=500*100, num_SA=1)

            self.visualise_with_matplotlib(mclp_results=search_areas, likelihood_cutoff=0.05)

            print(str(search_areas))
        except Exception as e:
            logger = unexefiware.base_logger.BaseLogger()
            logger.exception(inspect.currentframe(), e)


    def visualise_with_matplotlib(self, mclp_results:pandas.DataFrame, likelihood_cutoff:float=0, title:str=None):

        fig = plt.figure(dpi=200)
        ax = fig.add_subplot(1, 1, 1)

        # do links
        try:
            lines = []
            col = []
            num_links = self.sim_inst.getcount(object=en.LINKCOUNT) + 1

            for link_index in range(1, num_links):
                link_node_indices = self.sim_inst.getlinknodes(link_index)

                coords = []
                coords.append(self.sim_inst.getcoord(link_node_indices[0]))

                num_vertices = self.sim_inst.getvertexcount(link_index)

                if num_vertices:
                    for vertex in range(1, num_vertices + 1):
                        coords.append(self.sim_inst.getvertex(link_index, vertex))

                coords.append(self.sim_inst.getcoord(link_node_indices[1]))

                for i in range(0, len(coords) - 1):
                    line = [(coords[i][0], coords[i][1]), (coords[i + 1][0], coords[i + 1][1])]
                    lines.append(line)
                    col.append((0, 0, 1, 1))

            lc = matplotlib.collections.LineCollection(lines, colors=col, linewidths=2)
            ax.add_collection(lc)

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)


        # do nodes
        try:
            x = []
            y = []

            num_nodes = self.sim_inst.getcount(object=en.NODECOUNT) + 1
            for node_index in range(1, num_nodes):
                nodeID = self.sim_inst.getnodeid(node_index)

                coordinates = self.sim_inst.getcoord(node_index)

                coords = list(coordinates)

                #coords = self.sim_inst.transformer.transform(coords[0], coords[1])

                x.append(coords[0])
                y.append(coords[1])

                ax.scatter(x, y, s=10, c=[[1, 0, 0, 1]], zorder=2)
        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)


        try:
            if isinstance(mclp_results, pandas.DataFrame):

                for index, row in mclp_results.iterrows():
                    if row['Total_Probability'] >= likelihood_cutoff:
                        col = row['Total_Probability']
                        ax.plot(*row['geometry'].exterior.xy, c=[col, 0, col, 1], zorder=3)

                        ax.text(self.average(row['geometry'].exterior.xy[0]),self.average(row['geometry'].exterior.xy[1]),str(index) + '\n' + str(round(row['Total_Probability'] * 100,0)))

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

        plt.show()
    
    def average(self, val_list:list):
        
        if len(val_list) > 0:
            return sum(val_list) / len(val_list)
        
        return 0

