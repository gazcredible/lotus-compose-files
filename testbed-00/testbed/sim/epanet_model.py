#GARETH - this is going to hold everythng for working with epanet-based networks
# 1. define sensors for node/link data
# 2. do simulation time-steps to update fiware
# 3. create anomaly data, as it's useful for visualising network operations
import inspect
import json

import unexefiware.base_logger
import unexefiware.file
import unexefiware.time
import anomalies.Anomaly_Detection_Class
import epanet_fiware.waternetwork
import datetime

import matplotlib.pyplot as plt
import pandas
import epanet.toolkit as en

import sim.epanet_model


class epanet_model:
    def __init__(self):
        self.logger = unexefiware.base_logger.BaseLogger()
        self.inp_file = None
        self.epanetmodel = None

    def init(self,inp_file:str):
        self.inp_file = inp_file
        self.load_file(self.inp_file)

    def load_file(self,inp_file):
        try:
            self.epanetmodel = epanet_fiware.epanetmodel.EPAnetModel('temp', inp_file)
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

    def set_hyd_step(self, time_in_seconds):
        en.settimeparam(self.epanetmodel.proj_for_simulation, en.HYDSTEP, time_in_seconds)

    def get_hyd_step(self):
        return en.gettimeparam(self.epanetmodel.proj_for_simulation, en.HYDSTEP)

    def getcount(self,object):
        return en.getcount(self.epanetmodel.proj_for_simulation, object=object)

    def getnodeid(self, index):
        return en.getnodeid(self.epanetmodel.proj_for_simulation, index)

    def getnodetype(self, index):
        return en.getnodetype(self.epanetmodel.proj_for_simulation, index)


    def getnodevalue(self, index, prop):
        return en.getnodevalue(self.epanetmodel.proj_for_simulation, index, prop)

    def setnodevalue(self, index, prop, value):
        en.setnodevalue(self.epanetmodel.proj_for_simulation, index, prop, value)

    def getcoord(self,index:int):
        return en.getcoord(self.epanetmodel.proj_for_simulation,index)

    def getlinkid(self, index:int):
        return en.getlinkid(self.epanetmodel.proj_for_simulation, index)

    def getlinkindex(self, epanet_id:str):
        return en.getlinkindex(self.epanetmodel.proj_for_simulation, epanet_id)

    def getnodeindex(self, epanet_id:str):
        return en.getnodeindex(self.epanetmodel.proj_for_simulation, epanet_id)

    def getlinknodes(self, index:int):
        return en.getlinknodes(self.epanetmodel.proj_for_simulation, index)

    def getlinkvalue(self, index:int, prop:int):
        return en.getlinkvalue(self.epanetmodel.proj_for_simulation, index, prop)

    def getcoord(self, link_node_index:int):
        return en.getcoord(self.epanetmodel.proj_for_simulation, link_node_index)

    def getvertexcount(self, index):
        return en.getvertexcount(self.epanetmodel.proj_for_simulation, index)

    def getvertex(self, index, vertex):
        return en.getvertex(self.epanetmodel.proj_for_simulation, index, vertex)

    def get_sensors(self):
        sensors = []
        # sensors.append({'ID': node, 'Type': 'pressure'})
        # sensors.append({'ID': link, 'Type': 'flow'})

        if self.epanetmodel:
            num_nodes = self.getcount(object=en.NODECOUNT) + 1
            for index in range(1, num_nodes):
                nodeID = self.getnodeid(index)
                sensors.append({'ID':nodeID, 'Type': 'pressure'})

            num_links = self.getcount(object=en.LINKCOUNT) + 1
            for index in range(1, num_links):
                linkID = self.getlinkid(index)
                sensors.append({'ID': linkID, 'Type': 'flow'})

        return sensors

    def get_leak_nodes(self):
        links = []

        if self.epanetmodel:
            num_links = self.getcount(object=en.LINKCOUNT) + 1
            for index in range(1, num_links):
                linkID = self.getlinkid(index)
                links.append(linkID)

        return links

class AnomalyModel:
    def __init__(self):
        self.model_data = {}
        self.fiware_service = 'N/A'
        self.anomaly_detection = None
        self.model_data = None

        self.logger = unexefiware.base_logger.BaseLogger()

    def build_anomaly_data_from_epanet(self, epanet_model:epanet_model):
        sensors = epanet_model.get_sensors()
        leakNodeIDs = epanet_model.get_leak_nodes()

        self.build_anomaly_data(sensors, leakNodeIDs)

    def build_anomaly_data(self, fiware_service:str, sensors:list, leak_node_ids:list):
            self.sensors = sensors
            self.leak_nodes = leak_node_ids
            self.anomaly_detection = anomalies.Anomaly_Detection_Class.AnomalyDetection_Model(inp_file=self.inp_file, network_name=fiware_service, sensors=sensors)

            self.anomaly_detection.get_sensor_indices()

            self.anomaly_detection.build_dataset(leakEmitter=5,
                               testing_dataset=False,
                               leaks_simulated=2,
                               noise_sensor=0.0000001,
                               leak_nodes=leak_node_ids)

            self.model_data = self.anomaly_detection.dataSimulation['train_noleak']['noleakDB']
            self.model_data = self.model_data[['timestamp', 'Sensor_ID', 'Read_avg', 'Read_std']]
            self.model_data = self.model_data.groupby(['timestamp', 'Sensor_ID'], as_index=False).last()

    def save_anomaly_data(self, path_root):
        try:
            unexefiware.file.buildfilepath(path_root)
            self.model_data.to_pickle(path_root+"avg_values.pickle")

            with open(path_root+'avg_values' + '.json', 'w') as f:
                f.write(json.dumps(self.model_data.to_json()))

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

    def load(self,path_root):
        self.model_data = pandas.read_pickle(path_root + "avg_values.pickle")


    def graph(self):
        sensors = self.model_data['Sensor_ID'].unique()

        for device in sensors:
            src_data = self.model_data[self.model_data['Sensor_ID'] == device]
            values = []
            x = []
            date = datetime.datetime(2022,8,7)
            in_range = True
            while in_range:
                week_time = date.strftime("%A-%H:%M")
                avg_value = src_data.Read_avg[src_data.timestamp == week_time].iloc[0]

                x.append(week_time)
                values.append(avg_value)

                date += datetime.timedelta(minutes=15)

                in_range = not (date.day > 13)

            fig, ax = plt.subplots()
            ax.axes.xaxis.set_ticks([])
            ax.plot(x, values)
            temp = ax.xaxis.get_ticklabels()
            temp = list(set(temp) - set(temp[::96]))
            for label in temp:
                label.set_visible(False)
            fig.autofmt_xdate()

            plt.title(self.fiware_service + ' ' + str(device))

            plt.show()
