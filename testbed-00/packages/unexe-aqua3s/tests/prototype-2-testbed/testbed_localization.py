#Testbed Localization
#predicts ideal search area(s) to locate leak based on the last 6 hours of epanet device readings

#Steps: test
#inputs: MCLP values:
 # of search areas
 #search area size
 #search grid (optional)

#1. loads data: (completed)
    #a) prev 6 hour reads from epanet devices - context broker
    #b) avg. / std deviations for weekly reads database (in webdav)
    #c) RF classification model (in webdav)

#2. Convert / rearrange data:
    #a) convert sensor reads into residuals
    #b) rearrange into vector for RF model

#3. Prediction
    #a) predict leak node probability from RF model
    #b) predict leak search area & sum of leak probability within each area

#4. Store leak location in context broker? - need to json data?
    #leak_location_1: time, probability, location
    #leak_location_2: time, probability, location


import unexeaqua3s.service_alert
import unexeaqua3s.deviceinfo
import unexeaqua3s.service
import os
import unexefiware.base_logger
import unexefiware.time
from unexeaqua3s import support
import datetime
import unexefiware.workertask
import time
import pandas as pd
import numpy as np
import epanet_fiware.epanetmodel
import epanet_fiware.enumerations as enu

import shapely.geometry
from allagash import Coverage, Problem
import pulp
import geopandas


import unexeaqua3s.service_chart
import unexeaqua3s.service_anomaly
import unexeaqua3s.service_anomaly_epanet
import unexeaqua3s.resourcebuilder

import pickle
import unexeaqua3s.json


class HistoricData(unexefiware.workertask.WorkerTask):
    def __init__(self):
        super().__init__()
        self.debug_mode = False
        self.collect_data_results = []
        self.location_modelData = {}
        self.model_input={}

    def collect_location_webdavData(self,fiware_service):
        path_root = os.environ['FILE_PATH'] + os.sep + os.environ['FILE_VISUALISER_FOLDER'] +os.sep + 'data' +os.sep + fiware_service + os.sep + 'epanet_anomaly'
        #load avg value pd database
        self.location_modelData['avg_values_DB'] = pd.read_pickle(path_root + os.sep + "avg_values")
        # load RF model
        with open(path_root + os.sep + "rf_model", 'rb') as file:
            self.location_modelData['rf_model'] = pickle.load(file)
        # load waternetwork
        self.location_modelData['waterNetwork'] = epanet_fiware.epanetmodel.EPAnetModel(fiware_service, (os.environ['FILE_PATH'] + os.sep + os.environ['FILE_VISUALISER_FOLDER'] +os.sep + 'data' +
                                                   os.sep + fiware_service + os.sep + 'waternetwork' + os.sep+'epanet.inp'))


    def collect_device_reads(self, deviceInfo, fiware_time,fiware_leakWindow_start, fiware_service):
        t0 = time.perf_counter()
        key_list = list(deviceInfo.deviceInfoList.keys())
        if fiware_service == 'P2B':  # these sensors use epanet anomaly detection
            epanet_device_ids = deviceInfo.get_EPANET_sensors()
            # epanet_device_ids = {'urn:ngsi-ld:Device:UNEXE_TEST_103', 'urn:ngsi-ld:Device:2', 'urn:ngsi-ld:Device:76',
            #                      'urn:ngsi-ld:Device:87','urn:ngsi-ld:Device:94', 'urn:ngsi-ld:Device:97',
            #                      'urn:ngsi-ld:Device:103','urn:ngsi-ld:Device:32','urn:ngsi-ld:Device:9',
            #                      'urn:ngsi-ld:Device:28'}
            key_list = [x for x in key_list if x in epanet_device_ids]  # keep keys only within list of epanet devices

        key_list = sorted(key_list)

        self.raw_device_reads = {}

        for device_id in key_list:
            historic_device_reads = deviceInfo.brokers[unexeaqua3s.deviceinfo.device_label].get_temporal_orion(
                deviceInfo.service, device_id,
                fiware_leakWindow_start,
                fiware_time)
            #historic_device_reads.pop()
            self.raw_device_reads[device_id] = historic_device_reads
        print('Took: ' + str(time.perf_counter() - t0))

    def collect_node_coordinates(self):
        nodeIDs = self.location_modelData['waterNetwork'].get_node_ids(enu.NodeTypes.Junction)
        self.nodeCoordinates = pd.DataFrame(nodeIDs, columns=['Node_ID'])
        self.nodeCoordinates['Long'], self.nodeCoordinates['Lat'] = zip(
            *self.nodeCoordinates['Node_ID'].apply(self.get_coordinates))

    def get_coordinates(self,nodeID):
        coordinates = self.location_modelData['waterNetwork'].get_node_property(nodeID, enu.JunctionProperties.Position)
        return coordinates[0], coordinates[1]



    def transform_data(self, deviceInfo):
        # GARETH FIX ME - I'm doing this elsewhere
        if True: #GARETH
            sensors = deviceInfo.get_EPANET_sensors() #This is not the right order - need to adjust in ML Model
            #proper_order = [0,2,5,6,8,9,1,4,7,3]
            #sensor_order = [sensors[i] for i in proper_order]
            sensor_order = sensors

            rows = []
            for step in range(16):  # for first
                for device_id in sensor_order:
                    device_id_simple = deviceInfo.device_EPANET_id(device_id)
                    rows.append([device_id_simple, self.raw_device_reads[device_id][step]['observedAt'], self.raw_device_reads[device_id][step]['value']])
            df = pd.DataFrame(rows, columns=['SensorID', 'ObservedAt', 'Value'])
            df = self.calc_z_values(df)
            self.model_input['ML_Input'] = self.create_ML_modelInput(df)
        else:
            sensor_order = deviceInfo.get_EPANET_sensors()
            #create Dataframe in correct order:
            sensor_order = ['urn:ngsi-ld:Device:1','urn:ngsi-ld:Device:2','urn:ngsi-ld:Device:76','urn:ngsi-ld:Device:87',
                            'urn:ngsi-ld:Device:94','urn:ngsi-ld:Device:97','urn:ngsi-ld:Device:103','urn:ngsi-ld:Device:32',
                            'urn:ngsi-ld:Device:9','urn:ngsi-ld:Device:28']

            rows = []
            for step in range(24): # for first
                for sensor in sensor_order:
                    #GARETH FIX ME - I'm doing this elsewhere
                    sensor_id_simple = sensor.replace("urn:ngsi-ld:Device:", "")
                    rows.append([sensor_id_simple,self.raw_device_reads[sensor][step]['observedAt'],self.raw_device_reads[sensor][step]['value']])
            df = pd.DataFrame(rows, columns =['SensorID', 'ObservedAt', 'Value'])
            df = self.calc_z_values(df)
            self.model_input['ML_Input'] = self.create_ML_modelInput(df)

        print('drop_columns')
        print("a")

    def calc_z_values(self,df):
        df['week_time'] = df['ObservedAt'].map(lambda x: unexefiware.time.fiware_to_datetime(x).strftime("%A-%H:%M"))
        df = pd.merge(df, self.location_modelData['avg_values_DB'], how='inner', left_on=['SensorID','week_time'],
                 right_on =['Sensor_ID', 'timestamp'])
        df['z'] = (df['Value'].astype(float) - df['Read_avg'])/df['Read_std']
        return df

    def create_ML_modelInput(self, df):

        df = df.pivot_table(index=['Sensor_ID'],columns='ObservedAt', values='z').reset_index()
        df = df.drop(columns =['Sensor_ID'])
        df.index = df.index + 1
        df_out = df.stack()
        df_out.index = df_out.index.map('{0[1]}_{0[0]}'.format)
        df = df_out.to_frame().T
        X = df.to_numpy()
        # set max as float 32 and replace neg and pos inifinity and NAs
        X = np.float32(X)
        X = np.nan_to_num(X, nan=-9999, posinf=33333333, neginf=33333333)
        return(X)

def predict_ML_output(input, model, coordinates):
    probs = model.predict_proba(input.reshape(1, -1))
    a = np.concatenate((model.classes_[None, :], probs))
    prob_matrix = pd.DataFrame(data=a.transpose(), columns=["Node", "Probability"])
    result = pd.merge(prob_matrix, coordinates[['Node_ID', 'Long', 'Lat']],
                      how='inner', left_on='Node',
                      right_on='Node_ID')  # join df
    result["Probability"] = pd.to_numeric(result["Probability"], downcast="float")
    return result


#### MCLP Solver #####
class MCLP():
    def solve(self,prob_df, grid_spacing, search_radius, num_SA):
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
        sw = shapely.geometry.Point((min(prob_df.Long), min(prob_df.Lat)))
        ne = shapely.geometry.Point((max(prob_df.Long), max(prob_df.Lat)))
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
        if 'TTT' == 'TTT':
            grid = grid.set_crs(crs='epsg:32632') #TTT coordinates in m
        else:
            grid = grid.set_crs(crs='epsg:27700') #Britiain coordinates in m
        return grid

    def MCLP_solve(self, prob_df, grid, num_SA):
        #create prob_geopandas
        if 'TTT' == "TTT":
            prob_gpd = geopandas.GeoDataFrame(prob_df,
                                          geometry=geopandas.points_from_xy(prob_df['Long'], prob_df['Lat']),
                                          crs='epsg:32632')
        else:
            prob_gpd = geopandas.GeoDataFrame(prob_df,
                                              geometry=geopandas.points_from_xy(prob_df['Long'],
                                                                                prob_df['Lat']),
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


def testbed(fiware_service):
    quitApp = False

    logger = unexefiware.base_logger.BaseLogger()

    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    fiware_wrapper.init(logger=logger)

    my_broker = unexeaqua3s.brokerdefinition.BrokerDefinition()
    my_broker.init(fiware_wrapper)


    while quitApp is False:
        print('\nEPANET Anomaly Testbed')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])
        print('ALERT_BROKER:  ' + os.environ['ALERT_BROKER'])

        print('\n')
        print('0..Run EPANET Leak Localization Process')

        print('X..Back')
        print('\n')

        key = input('>')


        if key == '0':

            now = datetime.datetime.utcnow()
            #now = now - datetime.timedelta(hours=1)
            #now = datetime.datetime(2022, 5, 8, 16, 0, 0) #simulated leak at 6 AM May 8.
            leakWindow_start = now - datetime.timedelta(hours=4)
            fiware_time = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))
            fiware_leakWindow_start = unexefiware.time.datetime_to_fiware(leakWindow_start.replace(microsecond=0))
            pilots = os.environ['PILOTS'].split(',')
            #pilots = ['TTT']

            for fiware_service in pilots:
                print(fiware_service)
                deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=support.device_wrapper, other_wrapper=support.alert_wrapper)
                deviceInfo.run()
                historic_data = HistoricData()
                historic_data.collect_location_webdavData(fiware_service) #load up z value db
                historic_data.collect_node_coordinates()
                historic_data.collect_device_reads(deviceInfo, fiware_time,fiware_leakWindow_start, fiware_service)
                historic_data.transform_data(deviceInfo)
                result = predict_ML_output(historic_data.model_input['ML_Input'],
                                  historic_data.location_modelData['rf_model'],
                                  historic_data.nodeCoordinates)
                mclp = MCLP()
                selected_areas = mclp.solve(prob_df=result,grid_spacing=50,search_radius = 100, num_SA=2)
                selected_areas = selected_areas.to_crs(4326) #convert selected areas to wgs84
                print(str(selected_areas))
                #output seleted_areas in context broker?
                data = unexeaqua3s.json.loads(selected_areas.to_json())
                print(unexeaqua3s.json.dumps(data,indent=5))

        if key == 'x':
            quitApp = True


if __name__ == '__main__':
    testbed()