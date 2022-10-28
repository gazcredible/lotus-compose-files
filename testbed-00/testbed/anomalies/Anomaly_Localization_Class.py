#The purpose of this script is to develop an anomaly localization model
#Inputs: hydraulic model, X number of historic sensor readings corresponding to anomaly, desired search area info
#Output: anomaly localization search area
import epanet_fiware.epanetmodel
import epanet_fiware.enumerations as enu
import epanet_fiware.epanet_outfile_handler as outfile_handler
import epanet.toolkit as en #no function written in epanetmodel for pattern creation
import pandas as pd
import numpy as np
from typing import Optional
from scipy.stats import truncnorm
from sklearn.ensemble import RandomForestClassifier
from sklearn import metrics
import datetime
import random
import matplotlib.pyplot as plt
import shapely.geometry
from shapely.ops import transform
import pyproj
from allagash import Coverage, Problem
import pulp
import geopandas

#%%
class AnomalyLocalization():
    def __init__(self,
                 inp_file: str,
                 network_name: str,
                 sensors: list
                 ):
        self.network_name = network_name
        self.inp_file = inp_file
        self.epanetmodel = None
        self.sensors = sensors
        self.simulationData = {}
        self.MLmodel = {}
        self.currentAnomaly = None
        self.proj = pyproj.Transformer.from_crs('epsg:4326', 'epsg:27700', always_xy=True)
        self.load_epanetmodel()
        self.node_coordinates = None

        self.coord_system = None

    def load_epanetmodel(self):
        self.epanetmodel = epanet_fiware.epanetmodel.EPAnetModel(self.network_name, self.inp_file)

    def get_sensor_indices(self):
        for i in range(len(self.sensors)):
            if self.sensors[i]['Type'] == 'pressure':
                self.sensors[i]['Index'] = en.getnodeindex(self.epanetmodel.proj_for_simulation, self.sensors[i]['ID'])
            if self.sensors[i]['Type'] == 'flow':
                self.sensors[i]['Index'] = en.getlinkindex(self.epanetmodel.proj_for_simulation, self.sensors[i]['ID'])

    def build_datasets(self,
                      leak_nodes=None,
                      noleak_dataset: Optional[bool] = True,
                      training_dataset: Optional[bool] = True,
                      testing_dataset: Optional[bool] = True,
                      noise_sensor: Optional[float] = 0.5,
                      stepDuration: Optional[int] = 15 * 60,
                      simulation_date: Optional[datetime.datetime] = datetime.datetime(2022, 5, 6),
                      testleaks: Optional[int] = 100
                      ):
        if noleak_dataset == True:
            print("building no leak dataset")
            noleakDB = self.sim_no_leak(stepDuration=stepDuration,
                                        simulation_date=simulation_date,
                                        sigma=noise_sensor)
            self.simulationData['train_noleak'] = noleakDB

        if training_dataset == True:
            print("building leak training dataset")
            self.sim_leak_all_nodes(stepDuration = stepDuration,
                                    simulation_date = simulation_date,
                                    sigma = noise_sensor,
                                    leak_nodes = leak_nodes)
        if testing_dataset == True:
            print("building leak testing dataset")
            self.sim_random_leaks(nodes=testleaks,
                                  simulation_date = simulation_date,
                                  stepDuration=stepDuration,
                                  sigma=noise_sensor,
                                  leak_nodes = leak_nodes)

    def sim_no_leak(self,
                    stepDuration: Optional[int] = 15 * 60,
                    simulation_date: Optional[datetime.datetime] = datetime.datetime(2022, 5, 6),
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

                if sensor['Type'] == 'flow':
                    read = en.getlinkvalue(self.epanetmodel.proj_for_simulation, sensor['Index'], en.FLOW)
                    rows.append([report_step, report_time, sensor['ID'], sensor['Type'], read])
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

    def sim_leak(self,
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
        t = en.nextH(self.epanetmodel.proj_for_simulation)
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

                if sensor['Type'] == 'flow':
                    read = en.getlinkvalue(self.epanetmodel.proj_for_simulation, sensor['Index'], en.FLOW)
                    rows.append([report_step, report_time, sensor['ID'], sensor['Type'], read])

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

    def sim_leak_all_nodes(self,
                   leak_nodes=None,
                   duration: Optional[int]=11*24*60*60,
                   stepDuration: Optional[int] = 15 * 60,
                   simulation_date: Optional[datetime.datetime] = datetime.datetime(2021, 1, 1),
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
            print("node sim " + str(i) + " of "+ str(len(leak_nodes)))
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
                    leakDB = self.sim_leak(duration = duration, stepDuration = stepDuration, simulation_date = simulation_date, leakID= nodeID,
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
                except:
                    print("error simulating leak at Junction: " +nodeID)

        leakDB = pd.concat(leaks)
        self.simulationData['train_leaks'] = leakDB
        self.simulationData['train_leaks']['timeseries_id'] = self.simulationData['train_leaks']['leakNode'] + "_" + \
                                                              self.simulationData['train_leaks']['repeat'].astype(str)

    def sim_random_leaks(self,
                         leak_nodes=None,
                         duration: Optional[int] = 11 * 24 * 60 * 60,
                         stepDuration: Optional[int] = 15 * 60,
                         simulation_date: Optional[datetime.datetime] = datetime.datetime(2022, 5, 6),
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
            print("node sim " + str(i) + " of " + str(len(nodeIDs)))
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
                    leakDB = self.sim_leak(duration=duration, stepDuration=stepDuration,
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

    def add_demand_noise(self,
                         scale: Optional[float] = 0.25, #sets std
                         bounds: Optional[float] = 0.6  #sets max deviation
                         ):
        #noise = truncnorm(a=-bounds / scale, b=+bounds / scale, scale=scale).rvs(size=1) #truncated normal distribution
        noise = 0
        junctIDs = self.epanetmodel.get_node_ids(enu.NodeTypes.Junction)
        for junctID in junctIDs:
            demand = self.epanetmodel.get_node_property(junctID, enu.JunctionProperties.BaseDemand) #this method only works for base demand takes to long to set up for all demands
            demand_value = float(demand * (1 + noise))
            self.epanetmodel.set_node_property(junctID, enu.JunctionProperties.BaseDemand, demand_value)

    def ML_buildModel(self):
        self.ML_createDatasets() #1. Create X/Y datasets
        self.ML_trainModel() #2. Train & Save Model
        self.ML_testModel() #3. Test Model

    def ML_createDatasets(self):
        (self.MLmodel['X_train'], self.MLmodel['Y_train']) = self.ML_create_dataset(self.simulationData['train_leaks'])
        (self.MLmodel['X_test'], self.MLmodel['Y_test']) = self.ML_create_dataset(self.simulationData['test_leaks'])

    def ML_create_dataset(self, data):
        data = data[['ReportTime', 'Sensor_ID', 'z', 'leakNode', 'leakflow', 'leakEmitter', 'X-coord', 'Y-coord',
             'timeseries_id']]
        data = data.pivot_table(
            index=['ReportTime', 'leakNode', 'X-coord', 'Y-coord', 'leakflow', 'leakEmitter', 'timeseries_id'],
            columns='Sensor_ID', values='z').reset_index()
        data['seq'] = data.groupby(['timeseries_id']).cumcount()
        data = data.pivot_table(index=['leakNode', 'X-coord', 'Y-coord', 'leakflow', 'leakEmitter', 'timeseries_id'],
                                columns='seq').reset_index()
        Y = data.leakNode
        Y = Y.to_numpy()
        X = data.copy()
        X = X.drop(columns=['leakNode', 'leakflow', 'leakEmitter', 'X-coord', 'Y-coord', 'timeseries_id'])
        X = X.to_numpy()
        # set max as float 32 and replace neg and pos inifinity and NAs
        X = np.float32(X)
        X = np.nan_to_num(X, nan=-9999, posinf=33333333, neginf=33333333)
        return (X,Y)

    def ML_trainModel(self):
        print("training RF Classifier")
        self.MLmodel['Model'] = RandomForestClassifier(n_estimators=400,max_depth=300, n_jobs=-1)
        self.MLmodel['Model'].fit(self.MLmodel['X_train'], self.MLmodel['Y_train']) # fit model
        self.MLmodel['Training Accuracy'] = self.MLmodel['Model'].score(self.MLmodel['X_train'], self.MLmodel['Y_train'])
        print("Random Forest Classification Training Accuracy (% Correct) = ", str(self.MLmodel['Training Accuracy']))
        # Save Model
        #filename = 'rf_classifier.sav'
        # joblib.dump(model,  self.MLmodel['Model']) #save model
        # model = joblib.load(filename)  # load model

    def ML_testModel(self):
        self.MLmodel['Test Accuracy'] = self.MLmodel['Model'].score(self.MLmodel['X_test'], self.MLmodel['Y_test'])
        print("Random Forest Classification Testing Accuracy (% Correct) = ", str(self.MLmodel['Test Accuracy']))

    def ML_predict_prob(self,sample):
        probs = self.MLmodel['Model'].predict_proba(sample.reshape(1, -1))
        a = np.concatenate((self.MLmodel['Model'].classes_[None, :], probs))
        prob_matrix = pd.DataFrame(data=a.transpose(), columns=["Node", "Probability"])
        if self.node_coordinates is None:
            self.get_all_coordinates()

        result = pd.merge(prob_matrix, self.node_coordinates[['Node_ID', 'Long', 'Lat', 'Long_meters', 'Lat_meters']], how='inner', left_on='Node',
                          right_on='Node_ID')  # join df
        result["Probability"] = pd.to_numeric(result["Probability"], downcast="float")
        return result

    def get_all_coordinates(self):
        nodeIDs = self.epanetmodel.get_node_ids(enu.NodeTypes.Junction)
        self.node_coordinates = pd.DataFrame(nodeIDs, columns=['Node_ID'])
        self.node_coordinates['Long'], self.node_coordinates['Lat'] = zip(*self.node_coordinates['Node_ID'].apply(self.get_coordinates))
        self.node_coordinates = self.transform_coordinates(self.node_coordinates)
        return self.node_coordinates

    def get_coordinates(self,nodeID):
        coordinates = self.epanetmodel.get_node_property(nodeID, enu.JunctionProperties.Position)
        return coordinates[0], coordinates[1]

    def transform_coordinates(self, df):
        #GARETH, this only works for cases where coords are in meters, not WGS84
        df['Long_meters'] = df['Long']
        df['Lat_meters'] = df['Lat']

        return df

        if self.network_name == 'TTT' or self.network_name == 'GUW': #TTT already in meters
            df['Long_meters'] = df['Long']
            df['Lat_meters'] = df['Lat']
            #proj = pyproj.Transformer.from_crs(crs_from = 'epsg:32632', crs_to = 'epsg:4326', always_xy=True)  # TTT is 32632
            #df['Long_meters'], df['Lat_meters'] = proj.transform(df['Long'].tolist(), df['Lat'].tolist())
        else:
            #GARETH - break code here ;)
            #proj = pyproj.Transformer.from_crs('epsg:4326', 'epsg:27700', always_xy=True) #GT is 4326
            df['Long_meters'], df['Lat_meters'] = self.proj.transform(df['Long'].tolist(), df['Lat'].tolist())
        return df

    def MCLP(self,sample, grid_spacing, search_radius, num_SA):
        #predict probabilities for sample
        prob_df = self.ML_predict_prob(sample)
        #prob_df = prob_df[prob_df.Probability >0.0001]
        #create grid
        grid = self.MCLP_create_grid(prob_df, grid_spacing, search_radius)

        #solve MCLP
        start_time = datetime.datetime.now()
        selected_areas = self.MCLP_solve(prob_df, grid, num_SA)
        simulationTime = datetime.datetime.now() - start_time
        print("MCLP Solver Time: " + str(simulationTime))
        return selected_areas

    def MCLP_create_grid(self, prob_df, grid_spacing, search_radius):
        sw = shapely.geometry.Point((min(prob_df.Long_meters), min(prob_df.Lat_meters)))
        ne = shapely.geometry.Point((max(prob_df.Long_meters), max(prob_df.Lat_meters)))

        print(str(ne.x - sw.x) +':' + str(sw.y - ne.y))
        gridpoints = []
        x = sw.x
        while x < ne.x:
            y = sw.y
            while y < ne.y:
                p = shapely.geometry.Point(x, y).buffer(search_radius)
                gridpoints.append(p)
                y += grid_spacing
            x += grid_spacing

        grid = geopandas.GeoDataFrame(gridpoints)
        grid['ID'] = (grid.index).astype(int)
        grid = grid.rename(columns={0: "geometry"})
        grid = grid[['ID', 'geometry']]

        #GARETH !
        grid = grid.set_crs(crs='epsg:32646')  # TTT coordinates in m
        """
        if self.network_name == 'TTT':
            grid = grid.set_crs(crs='epsg:32632') #TTT coordinates in m
        else:
            grid = grid.set_crs(crs='epsg:27700') #Britiain coordinates in m
            
        """
        return grid

    def MCLP_solve(self, prob_df, grid, num_SA):
        #create prob_geopandas
        if self.network_name == "TTT":
            prob_gpd = geopandas.GeoDataFrame(prob_df,
                                          geometry=geopandas.points_from_xy(prob_df['Long_meters'], prob_df['Lat_meters']),
                                          crs='epsg:32632')
        else:
            prob_gpd = geopandas.GeoDataFrame(prob_df,
                                              geometry=geopandas.points_from_xy(prob_df['Long_meters'],
                                                                                prob_df['Lat_meters']),
                                              crs='epsg:32632')

        prob_gpd = prob_gpd[['Node', 'Probability', 'geometry']]
        #solve problem
        coverage = Coverage.from_geodataframes(prob_gpd, grid, "Node", "ID", demand_col="Probability",
                                                demand_name="demand")
        problem = Problem.mclp([coverage], max_supply={coverage: num_SA})
        problem.solve(pulp.PULP_CBC_CMD())
        #output results
        selected_areas = problem.selected_supply(coverage)
        selected_areas = list(map(int, selected_areas))  # convert values in list to int
        selected_areas_df = grid[grid['ID'].isin(selected_areas)]
        covered_demand = prob_gpd.query(f"Node in ({[f'{j}' for j in problem.selected_demand(coverage)]})")
        total_demand = covered_demand['Probability'].sum()
        selected_areas_df['Total_Probability'] = total_demand
        return selected_areas_df

# #%%
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
# sensors_7 = {'ID': '3092019_3276.3092019_3143.1','Type': 'flow'}
# sensors_8 = {'ID': '3092019_11921.3092019_2773.1','Type': 'flow'}
# sensors_9 = {'ID': '3092019_2612.3092019_2608.1','Type': 'flow'}
# sensors_10 = {'ID': '3092019_10509.3092019_2356.1','Type': 'flow'}
# sensors_11 = {'ID': '3092019_12016.3092019_2136.1','Type': 'flow'}
# sensors_12 = {'ID': '3092019_12045.3092019_1869.1','Type': 'flow'}
#
#
# sensors = [sensors_0, sensors_1, sensors_2, sensors_3 ,sensors_4,sensors_5, sensors_6, sensors_7, sensors_8, sensors_9, sensors_10, sensors_11, sensors_12]
#
# test = AnomalyLocalization(inp_file=inp_file, network_name=network_name, sensors=sensors)
# test.get_sensor_indices()
# #%% Build Simulation Data
# # start_time = datetime.datetime.now()
# # test.build_datasets(testing_dataset = False)
# # #simulationTime = datetime.datetime.now() - start_time
# # #print("Total Simulation Time: " + str(simulationTime))
# # #save datasets
# # path = "C:/Users/bs524/OneDrive - University of Exeter/Documents/Exeter/dev/packages/anomaly-detection/data/"
# # #test.simulationData['train_noleak'].to_pickle(path+"GT_train_noleak")
# # test.simulationData['train_leaks'].to_pickle(path+"GT_train_leaks_2")
# # #test.simulationData['test_leaks'].to_pickle(path+"GT_test_leaks")
# #%%
# #load sim data
# path = "C:/Users/bs524/OneDrive - University of Exeter/Documents/Exeter/dev/packages/anomaly-detection/data/"
# test.simulationData['train_noleak'] = pd.read_pickle(path+"GT_train_noleak")
# test.simulationData['train_leaks'] = pd.read_pickle(path+"GT_train_leaks")
# test.simulationData['test_leaks'] = pd.read_pickle(path+"GT_test_leaks")
# #%% Build ML Model
# test.ML_buildModel()
#
# #%% Hyper Parameter Tuning 2: Takes too much memory
# # from numpy import mean
# # from numpy import std
# # from sklearn.datasets import make_classification
# # from sklearn.model_selection import cross_val_score
# # from sklearn.model_selection import RepeatedStratifiedKFold
# # from sklearn.ensemble import RandomForestClassifier
# # from matplotlib import pyplot
# #
# # test.ML_createDatasets()
# # X = test.MLmodel['X_train']
# # y = test.MLmodel['Y_train']
# # models = dict()
# # # define number of trees to consider
# # n_trees = [100,200,300]
# # n_depth = [50,150,250]
# # for n in n_trees:
# #     for i in n_depth:
# #         models["tree depth:"+str(i) + "Number of trees:"+str(n)] = RandomForestClassifier(n_estimators=n, max_depth=i, n_jobs=-1)
# #
# # def evaluate_model(model, X, y):
# #     # define the evaluation procedure
# #     cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=2, random_state=1)
# #     # evaluate the model and collect the results
# #     scores = cross_val_score(model, X, y, scoring='accuracy', cv=cv, n_jobs=-1)
# #     return scores
# #
# # results, names = list(), list()
# # for name, model in models.items():
# #     # evaluate the model
# #     scores = evaluate_model(model, X, y)
# #     # store the results
# #     results.append(scores)
# #     names.append(name)
# #     # summarize the performance along the way
# #     print('>%s %.3f (%.3f)' % (name, mean(scores), std(scores)))
# # # plot model performance for comparison
# # pyplot.boxplot(results, labels=names, showmeans=True)
# # pyplot.show()
#
# #%% Hyper Parameter Tuning 3:
# test.ML_createDatasets()
# #max depth
# start_time = datetime.datetime.now()
# path = "C:/Users/bs524/OneDrive - University of Exeter/Documents/Aqua3S/ML Results/HyperTuning/"
# accuracy_rate = []
# training_acc = []
# trees=[10,25,50,100,150,200,250,300]
# depths=[100,200,300,400,500,600]
# for i in trees:
#     for j in depths:
#         start_time = datetime.datetime.now()
#         test.MLmodel['Model'] = RandomForestClassifier(n_estimators=j, max_depth=i, n_jobs=-1)
#         test.MLmodel['Model'].fit(test.MLmodel['X_train'], test.MLmodel['Y_train'])  # fit model
#         simulationTime = datetime.datetime.now() - start_time
#         print("ML Model Training Time: " + str(simulationTime))
#         accuracy_rate.append(test.MLmodel['Model'].score(test.MLmodel['X_test'], test.MLmodel['Y_test']))
#         training_acc.append(test.MLmodel['Model'].score(test.MLmodel['X_train'], test.MLmodel['Y_train']))
#
# #%%
# plt.figure(figsize=(12,8))
# plt.plot(params, accuracy_rate,color='red', linestyle='dashed', marker='o',
#          markerfacecolor='red', markersize=10)
# # plt.plot(params, training_acc,color='blue', linestyle='dashed', marker='o',
# #           markerfacecolor='blue', markersize=10)
# plt.title('Accuracy Rate vs. Tree Depth @ 150 trees')
# plt.xlabel('Tree Depth')
# plt.ylabel('Accuracy Rate')
# plt.savefig(path+str('RF_TreeDepth.png'))
# plt.show()
#
# # of trees
# path = "C:/Users/bs524/OneDrive - University of Exeter/Documents/Aqua3S/ML Results/HyperTuning/"
# accuracy_rate = []
# training_acc = []
# params=[100,200,300,400,500,600]
# for i in params:
#     start_time = datetime.datetime.now()
#     test.MLmodel['Model'] = RandomForestClassifier(n_estimators=i, max_depth=75, n_jobs=-1)
#     test.MLmodel['Model'].fit(test.MLmodel['X_train'], test.MLmodel['Y_train'])  # fit model
#     print("ML Model Training Time: " + str(simulationTime))
#     accuracy_rate.append(test.MLmodel['Model'].score(test.MLmodel['X_test'], test.MLmodel['Y_test']))
#     training_acc.append(test.MLmodel['Model'].score(test.MLmodel['X_train'], test.MLmodel['Y_train']))
#
#
#
#
#
# #%% Hyper Parameter Tuning:
# test.ML_createDatasets()
# #max depth
# start_time = datetime.datetime.now()
# path = "C:/Users/bs524/OneDrive - University of Exeter/Documents/Aqua3S/ML Results/HyperTuning/"
# accuracy_rate = []
# training_acc = []
# params=[10,25,50,100,150,200,250,300]
# for i in params:
#     start_time = datetime.datetime.now()
#     test.MLmodel['Model'] = RandomForestClassifier(n_estimators=150, max_depth=i, n_jobs=-1)
#     test.MLmodel['Model'].fit(test.MLmodel['X_train'], test.MLmodel['Y_train'])  # fit model
#     simulationTime = datetime.datetime.now() - start_time
#     print("ML Model Training Time: " + str(simulationTime))
#     accuracy_rate.append(test.MLmodel['Model'].score(test.MLmodel['X_test'], test.MLmodel['Y_test']))
#     training_acc.append(test.MLmodel['Model'].score(test.MLmodel['X_train'], test.MLmodel['Y_train']))
#
# print("Total training time: " + str(simulationTime))
# plt.figure(figsize=(12,8))
# plt.plot(params, accuracy_rate,color='red', linestyle='dashed', marker='o',
#          markerfacecolor='red', markersize=10)
# # plt.plot(params, training_acc,color='blue', linestyle='dashed', marker='o',
# #           markerfacecolor='blue', markersize=10)
# plt.title('Accuracy Rate vs. Tree Depth @ 150 trees')
# plt.xlabel('Tree Depth')
# plt.ylabel('Accuracy Rate')
# plt.savefig(path+str('RF_TreeDepth.png'))
# plt.show()
#
# # of trees
# path = "C:/Users/bs524/OneDrive - University of Exeter/Documents/Aqua3S/ML Results/HyperTuning/"
# accuracy_rate = []
# training_acc = []
# params=[100,200,300,400,500,600]
# for i in params:
#     start_time = datetime.datetime.now()
#     test.MLmodel['Model'] = RandomForestClassifier(n_estimators=i, max_depth=75, n_jobs=-1)
#     test.MLmodel['Model'].fit(test.MLmodel['X_train'], test.MLmodel['Y_train'])  # fit model
#     print("ML Model Training Time: " + str(simulationTime))
#     accuracy_rate.append(test.MLmodel['Model'].score(test.MLmodel['X_test'], test.MLmodel['Y_test']))
#     training_acc.append(test.MLmodel['Model'].score(test.MLmodel['X_train'], test.MLmodel['Y_train']))
#
# #%% MCLP - Script
# sample = test.MLmodel['X_test'][1]
# #%%
# search_areas = test.MCLP(sample = sample, grid_spacing = 20, search_radius = 50, num_SA = 2)
#
# #%% Calculate accuracy with test set
# #impact of grid spacing, search radius, on time+accuracy
# gridspaces = [10,15,25,40,60,80]
# searchareas = [1,2,3,4]
# searchradius = [10,20,30,40,50,60,70,80,90,100]
# num_SA = 2
# search_radius = 50
# rows = []
# for grid_spacing in gridspaces:
#     print("gridspacing " + str(grid_spacing))
#     for i in range(0,100,2):# skip by two to grab only high leakage -  range(np.shape(test.MLmodel['X_test'])[0]):
#         print("solving " + str(i) + ' of ' + str(np.shape(test.MLmodel['X_test'])[0]))
#         sample = test.MLmodel['X_test'][i]
#         prob_df = test.ML_predict_prob(sample)
#         # prob_df = prob_df[prob_df.Probability >0.0001]
#         # create grid
#         grid = test.MCLP_create_grid(prob_df, grid_spacing=grid_spacing, search_radius=search_radius)
#         # solve MCLP
#         start_time = datetime.datetime.now()
#         selected_areas = test.MCLP_solve(prob_df, grid, num_SA=num_SA)
#         simulationTime = datetime.datetime.now() - start_time
#         #Leak Point
#         leak_point = test.MLmodel['Y_test'][i]
#         leak_point_coords = test.get_coordinates(leak_point)
#         leak_point = {'NodeID': leak_point, 'Lat': leak_point_coords[1], 'Long': leak_point_coords[0]}
#         leak_point = pd.DataFrame(data=leak_point, index=[0])
#         leak_point = test.transform_coordinates(leak_point)
#         leak_gpd = geopandas.GeoDataFrame(leak_point, geometry=geopandas.points_from_xy(leak_point['Long_meters'],
#                                                                                         leak_point['Lat_meters']),
#                                           crs='epsg:27700')
#         leak_gpd = leak_gpd[['NodeID', 'geometry']]
#         contains_leak = len(geopandas.sjoin(selected_areas, leak_gpd, op='contains'))
#         if contains_leak >1:
#             contains_leak = 1 # both circles can overlap and then contain both leaks (unlikely)
#         rows.append([leak_gpd.NodeID.iloc[0], leak_gpd.geometry.iloc[0], selected_areas['Total_Probability'].iloc[0], grid_spacing, search_radius, num_SA, simulationTime.total_seconds(), contains_leak])
# df = pd.DataFrame(rows, columns=["Leak_node", "geometry", "probability_covered", 'grid_spacing', 'search_radius', 'num_SA', 'simulationTime_sec', 'detected'])
# #%% Analyzing results of MCLP
# df['detected'] = pd.to_numeric(df['detected'])
# mclp_results = df.groupby(by="grid_spacing").mean().reset_index()
# mclp_results.to_clipboard()
# #%% Search Radius
# gridspaces = [10,15,25,40,60,80]
# searchareas = [1,2,3,4]
# searchradiuses = [10,20,30,40,50,60,70,80,90,100]
# num_SA = 2
# grid_spacing = 25
# rows = []
# for searchradius in searchradiuses:
#     print("searchradius " + str(searchradius))
#     for i in range(1,99,2):# skip by two to grab only high leakage -  range(np.shape(test.MLmodel['X_test'])[0]):
#         print("solving " + str(i) + ' of ' + str(np.shape(test.MLmodel['X_test'])[0]))
#         sample = test.MLmodel['X_test'][i]
#         prob_df = test.ML_predict_prob(sample)
#         # prob_df = prob_df[prob_df.Probability >0.0001]
#         # create grid
#         grid = test.MCLP_create_grid(prob_df, grid_spacing=grid_spacing, search_radius=searchradius)
#         # solve MCLP
#         start_time = datetime.datetime.now()
#         selected_areas = test.MCLP_solve(prob_df, grid, num_SA=num_SA)
#         simulationTime = datetime.datetime.now() - start_time
#         #Leak Point
#         leak_point = test.MLmodel['Y_test'][i]
#         leak_point_coords = test.get_coordinates(leak_point)
#         leak_point = {'NodeID': leak_point, 'Lat': leak_point_coords[1], 'Long': leak_point_coords[0]}
#         leak_point = pd.DataFrame(data=leak_point, index=[0])
#         leak_point = test.transform_coordinates(leak_point)
#         leak_gpd = geopandas.GeoDataFrame(leak_point, geometry=geopandas.points_from_xy(leak_point['Long_meters'],
#                                                                                         leak_point['Lat_meters']),
#                                           crs='epsg:27700')
#         leak_gpd = leak_gpd[['NodeID', 'geometry']]
#         contains_leak = len(geopandas.sjoin(selected_areas, leak_gpd, op='contains'))
#         if contains_leak >1:
#             contains_leak = 1 # both circles can overlap and then contain both leaks (unlikely)
#         rows.append([leak_gpd.NodeID.iloc[0], leak_gpd.geometry.iloc[0], selected_areas['Total_Probability'].iloc[0], grid_spacing, searchradius, num_SA, simulationTime.total_seconds(), contains_leak])
# df = pd.DataFrame(rows, columns=["Leak_node", "geometry", "probability_covered", 'grid_spacing', 'search_radius', 'num_SA', 'simulationTime_sec', 'detected'])
# #%% Impact of # SA:
# #%% Search Radius
# num_SAs = [1,2,3,4]
# grid_spacing = 25
# search_radius = 40
# rows = []
# for num_SA in num_SAs:
#     print("Search Areas " + str(num_SA))
#     for i in range(1,99,2):# skip by two to grab only high leakage -  range(np.shape(test.MLmodel['X_test'])[0]):
#         print("solving " + str(i) + ' of ' + str(np.shape(test.MLmodel['X_test'])[0]))
#         sample = test.MLmodel['X_test'][i]
#         prob_df = test.ML_predict_prob(sample)
#         # prob_df = prob_df[prob_df.Probability >0.0001]
#         # create grid
#         grid = test.MCLP_create_grid(prob_df, grid_spacing=grid_spacing, search_radius=search_radius)
#         # solve MCLP
#         start_time = datetime.datetime.now()
#         selected_areas = test.MCLP_solve(prob_df, grid, num_SA=num_SA)
#         simulationTime = datetime.datetime.now() - start_time
#         #Leak Point
#         leak_point = test.MLmodel['Y_test'][i]
#         leak_point_coords = test.get_coordinates(leak_point)
#         leak_point = {'NodeID': leak_point, 'Lat': leak_point_coords[1], 'Long': leak_point_coords[0]}
#         leak_point = pd.DataFrame(data=leak_point, index=[0])
#         leak_point = test.transform_coordinates(leak_point)
#         leak_gpd = geopandas.GeoDataFrame(leak_point, geometry=geopandas.points_from_xy(leak_point['Long_meters'],
#                                                                                         leak_point['Lat_meters']),
#                                           crs='epsg:27700')
#         leak_gpd = leak_gpd[['NodeID', 'geometry']]
#         contains_leak = len(geopandas.sjoin(selected_areas, leak_gpd, op='contains'))
#         if contains_leak >1:
#             contains_leak = 1 # both circles can overlap and then contain both leaks (unlikely)
#         rows.append([leak_gpd.NodeID.iloc[0], leak_gpd.geometry.iloc[0], selected_areas['Total_Probability'].iloc[0], grid_spacing, search_radius, num_SA, simulationTime.total_seconds(), contains_leak])
# df = pd.DataFrame(rows, columns=["Leak_node", "geometry", "probability_covered", 'grid_spacing', 'search_radius', 'num_SA', 'simulationTime_sec', 'detected'])
# #%%
# df['detected'] = pd.to_numeric(df['detected'])
# mclp_results = df.groupby(by="num_SA").mean().reset_index()
# mclp_results.to_clipboard()
#
#
# #%%
# #Accuracy - is leak within circles?
# leak_point = test.MLmodel['Y_test'][1]
# leak_point_coords = test.get_coordinates(leak_point)
# leak_point = {'NodeID':leak_point, 'Lat':leak_point_coords[1], 'Long':leak_point_coords[0]}
# leak_point = pd.DataFrame(data=leak_point, index=[0])
# #%%
# leak_point = test.transform_coordinates(leak_point)
# #%%
# leak_gpd = geopandas.GeoDataFrame(leak_point, geometry=geopandas.points_from_xy(leak_point['Long_meters'], leak_point['Lat_meters']),
#                              crs='epsg:27700')
# leak_gpd = leak_gpd[['NodeID', 'geometry']]
#
# #%%
# polygons_contains = geopandas.sjoin(grid_select, leak_gpd,
#                                     op='contains')  # returns polygons that contain the leak
# #if len(polygons_contains) > 0:
# #    total_detect = total_detect + 1
# #%%
# #Accuracy - Correlation between prob within circles and accurate prediction
# covered_demand = prob_gpd.query(f"Node in ({[f'{j}' for j in problem.selected_demand(coverage1)]})")
# #covered_demand = result_gpd.query(f"Node in ({[f'{j}' for j in problem.selected_demand(coverage)]})")
# covered_demand['Probability'].sum()
# #%%
# rows.append([covered_demand['Probability'].sum() / 1000, len(polygons_contains)])
# print("completed "+str(i+1)+ " of " + str(len(y_test)))
