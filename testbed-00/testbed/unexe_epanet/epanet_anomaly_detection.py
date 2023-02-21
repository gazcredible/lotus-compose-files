import unexefiware.base_logger
import unexe_epanet.epanet_model
import anomalies.Anomaly_Detection_Class

import json
import inspect
import datetime
import matplotlib.pyplot as plt
import pandas

class epanet_anomaly_detection:
    def __init__(self):
        self.model_data = {}
        self.fiware_service = 'N/A'
        self.anomaly_detection = None
        self.model_data = None

        self.logger = unexefiware.base_logger.BaseLogger()
        self.inp_file = None

    def build_anomaly_data_from_epanet(self, epanet_model:unexe_epanet.epanet_model):
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
                           leaks_simulated=100, #max value
                           noise_sensor=0.0000001,
                           leak_nodes=self.leak_nodes)

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