import inspect

import pandas
import pandas as pd
import unexefiware.base_logger
import epanet_fiware.enumerations as enu
import epanet.toolkit as en #no function written in epanetmodel for pattern creation

import local_environment_settings
import os
import pyproj

import anomalies.Anomaly_Localization_Class as AL
import sim.epanet_model
import datetime

import geopandas
import matplotlib.pyplot as plt
import shapely
from allagash import Coverage, Problem
import pulp
import json

import numpy as np
from typing import Optional

import guw_device_info
import matplotlib.pyplot as plt


"""
steps:
1. create AnomalyLocalization object with epanet model, and list of sensors
2. build datasets()
3. save data
"""

class AnomalyLocalisation(AL.AnomalyLocalization):
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

    def MCLP(self, sample, grid_spacing, search_radius, num_SA):
        # predict probabilities for sample
        prob_df = self.ML_predict_prob(sample)
        # prob_df = prob_df[prob_df.Probability >0.0001]
        # create grid
        grid = self.MCLP_create_grid(prob_df, grid_spacing, search_radius)

        if isinstance(grid, geopandas.GeoDataFrame):
            # solve MCLP
            start_time = datetime.datetime.now()
            selected_areas = self.MCLP_solve(prob_df, grid, num_SA)
            simulationTime = datetime.datetime.now() - start_time
            print("MCLP Solver Time: " + str(simulationTime))
            return selected_areas

        return None

    def MCLP_create_grid(self, prob_df, grid_spacing, search_radius):
        try:
            sw = shapely.geometry.Point((min(prob_df.Long_meters), min(prob_df.Lat_meters)))
            ne = shapely.geometry.Point((max(prob_df.Long_meters), max(prob_df.Lat_meters)))

            print(str(ne.x - sw.x) + ':' + str(ne.y - sw.y))
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
        problem.solve(pulp.PULP_CBC_CMD())
        #output results
        selected_areas = problem.selected_supply(coverage)
        selected_areas = list(map(int, selected_areas))  # convert values in list to int
        selected_areas_df = grid[grid['ID'].isin(selected_areas)]
        covered_demand = prob_gpd.query(f"Node in ({[f'{j}' for j in problem.selected_demand(coverage)]})")
        total_demand = covered_demand['Probability'].sum()
        selected_areas_df['Total_Probability'] = total_demand
        return selected_areas_df

    def sim_leak_all_nodes(self,
                   leak_nodes=None,
                   duration: Optional[int]=11*24*60*60,
                   stepDuration: Optional[int] = 15 * 60,
                   simulation_date: Optional[datetime.datetime] = datetime.datetime(2021, 1, 1),
                   repeats: Optional[int] = 1, #GARETH was 20
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
                except Exception as e:
                    self.logger.exception(inspect.currentframe(),e)
                    print("error simulating leak at Junction: " +nodeID)

        leakDB = pd.concat(leaks)
        self.simulationData['train_leaks'] = leakDB
        self.simulationData['train_leaks']['timeseries_id'] = self.simulationData['train_leaks']['leakNode'] + "_" + \
                                                              self.simulationData['train_leaks']['repeat'].astype(str)

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
            for row in mclp_results.iterrows():
                ax.plot(*row[1]['geometry'].exterior.xy, c=[0,0,1,1], zorder=3)

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




def anomaly_localisation_testbed(fiware_service):
    try:
        inp_file = '/docker/lotus-visualiser/visualiser/data/' + fiware_service + '/waternetwork/epanet.inp'

        #load inp file into EPASim so we can get the sensors out of it
        water_model = sim.epanet_model.epanet_model()

        coord_str = ''

        if fiware_service == 'AAA':
            coord_str = 'epsg:32632'
            coord_system = pyproj.CRS.from_epsg(32632)
            flip_coordindates = True

        if fiware_service == 'GUW':
            coord_str = 'epsg:32646'
            coord_system = pyproj.CRS.from_epsg(32646)
            flip_coordindates = True

        coord_system = pyproj.CRS.from_epsg(32632)

        water_model.init(fiware_service,inp_file,coord_system,flip_coordindates)

        sensors = water_model.get_anomaly_sensors()
        leakNodeIDs = water_model.get_anomaly_leaknode_ids()

        leakNodeIDs = [leakNodeIDs[0]]#,leakNodeIDs[1]]

        network_name = fiware_service
        test = AnomalyLocalisation(inp_file=inp_file, network_name=network_name, sensors=sensors, proj_auth_code=coord_str)

        test.get_sensor_indices()

        if False:
            start_time = datetime.datetime.now()
            test.build_datasets(leak_nodes=leakNodeIDs,
                                noleak_dataset=True,
                                training_dataset=True,
                                testing_dataset=True)

            simulationTime = datetime.datetime.now() - start_time

            test.save_datafiles()
        else:
            test.load_datafiles()

        #can save this data, then don't need to load the training and test data
        test.ML_buildModel()

        simulationstart_date = datetime.datetime(2022, 4, 29)
        leakstart_date = datetime.datetime(2022, 5, 8, 6, 0, 0)
        leakwindow_start_date = datetime.datetime(2022, 5, 8, 12, 0, 0)
        leakwindow_end_date = datetime.datetime(2022, 5, 8, 16, 0, 0)
        stepDuration = 15 * 60
        leakstart_seconds = int((leakstart_date - simulationstart_date).total_seconds())
        leakStart_step = int(leakstart_seconds / stepDuration)

        leak_id = leakNodeIDs[0]

        leakEmitter = 5

        leak_df = test.sim_leak(duration=leakstart_seconds + (48 * 60 * 60),
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
        # %%
        sample, sample_answer = test.ML_create_dataset(leak_df)

        coordinates = test.epanetmodel.get_node_property(sample_answer[0], enu.JunctionProperties.Position)
        sample_answer = pd.DataFrame(sample_answer, columns=['Node_ID'], index=[0])
        sample_answer['Long'] = coordinates[0]
        sample_answer['Lat'] = coordinates[1]
        sample_answer = geopandas.GeoDataFrame(sample_answer,
                                               geometry=geopandas.points_from_xy(sample_answer['Long'], sample_answer['Lat']),
                                               crs=coord_str)

        search_areas = test.MCLP(sample=sample, grid_spacing=40, search_radius=500, num_SA=2)

        test.visualise_with_matplotlib(search_areas)

        print(str(search_areas))
    except Exception as e:
        logger = unexefiware.base_logger.BaseLogger()
        logger.exception(inspect.currentframe(), e)


def testbed(fiware_service):
    quitApp = False

    while quitApp is False:
        print('\n')
        print('PILOT: '+ fiware_service)

        print('\n')
        print('1..Do anomaly localisation testbed')
        print('2..Do GUW from data')
        print('3..Visualisation Test')


        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            anomaly_localisation_testbed(fiware_service)

        if key == '2':
            try:
                coord_str = 'epsg:32632'
                inp_file = '/docker/lotus-visualiser/visualiser/data/' + fiware_service + '/waternetwork/epanet.inp'

                sensors = []
                leakNodeIDs = []

                for entry in guw_device_info.info:
                    if 'junction' in entry[6]:
                        sensors.append({'ID': entry[6]['junction'], 'Type': 'pressure'})
                        leakNodeIDs.append(entry[6]['junction'])

                    if 'pipe' in entry[6]:
                        sensors.append({'ID': entry[6]['pipe'], 'Type': 'flow'})

                #build leak list from ...

                test = AnomalyLocalisation(inp_file=inp_file, network_name=fiware_service, sensors=sensors, proj_auth_code=coord_str)

                test.get_sensor_indices()

                if False:
                    start_time = datetime.datetime.now()
                    test.build_datasets(leak_nodes=leakNodeIDs,
                                        noleak_dataset=True,
                                        training_dataset=True,
                                        testing_dataset=True)

                    simulationTime = datetime.datetime.now() - start_time

                    test.save_datafiles()
                else:
                    test.load_datafiles()

                # can save this data, then don't need to load the training and test data
                test.ML_buildModel()

                simulationstart_date = datetime.datetime(2022, 4, 29)
                leakstart_date = datetime.datetime(2022, 5, 8, 6, 0, 0)
                leakwindow_start_date = datetime.datetime(2022, 5, 8, 12, 0, 0)
                leakwindow_end_date = datetime.datetime(2022, 5, 8, 16, 0, 0)
                stepDuration = 15 * 60
                leakstart_seconds = int((leakstart_date - simulationstart_date).total_seconds())
                leakStart_step = int(leakstart_seconds / stepDuration)

                leak_id = leakNodeIDs[10]
                leak_id = 'GJ462'
                leak_id = 'GJ121'

                leakEmitter = 5

                leak_df = test.sim_leak(duration=leakstart_seconds + (48 * 60 * 60),
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
                # %%
                sample, sample_answer = test.ML_create_dataset(leak_df)

                coordinates = test.epanetmodel.get_node_property(sample_answer[0], enu.JunctionProperties.Position)
                sample_answer = pd.DataFrame(sample_answer, columns=['Node_ID'], index=[0])
                sample_answer['Long'] = coordinates[0]
                sample_answer['Lat'] = coordinates[1]
                sample_answer = geopandas.GeoDataFrame(sample_answer,
                                                       geometry=geopandas.points_from_xy(sample_answer['Long'], sample_answer['Lat']),
                                                       crs=coord_str)

                search_areas = test.MCLP(sample=sample, grid_spacing=20, search_radius=100, num_SA=5)

                print(str(search_areas))

                test.visualise_with_matplotlib(coordinates, search_areas, title = str(leak_id) )



            except Exception as e:
                logger = unexefiware.base_logger.BaseLogger()
                logger.exception(inspect.currentframe(), e)

        if key == '3':
            inp_file = '/docker/lotus-visualiser/visualiser/data/' + fiware_service + '/waternetwork/epanet.inp'
            sensors = []
            coord_str = 'epsg:32632'

            test = AnomalyLocalisation(inp_file=inp_file, network_name=fiware_service, sensors=sensors, proj_auth_code=coord_str)

            test.visualise_with_matplotlib()

        if key == 'x':
                quitApp = True

if __name__ == '__main__':
    testbed()
