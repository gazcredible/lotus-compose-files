#GARETH - this is going to hold everythng for working with unexe_epanet-based networks
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
import pyproj


def MIN_TO_SEC(x):
    return x*60

def SEC_TO_MIN(x):
    return (x/60)

def MIN_TO_HOUR(x):
    return (x/60)

def SEC_TO_HOUR(x):
    return MIN_TO_HOUR(SEC_TO_MIN(x))


class epanet_model:
    def __init__(self):
        self.logger = unexefiware.base_logger.BaseLogger()
        self.inp_file = None
        self.epanetmodel = None

        #this is for managing the time of simualtions
        self.elapsed_time_in_sec = 0
        self.next_time_step_in_sec = 0
        self.start_datetime = datetime.datetime.now()
        self.current_datetime = self.start_datetime

        #this is for visualising models
        self.flip_coordinates = False
        self.coord_system = pyproj.CRS.from_epsg(4326)
        self.transformer = pyproj.Transformer.from_crs(self.coord_system, pyproj.CRS.from_epsg(4326))

    def init(self,inp_file:str):
        self.inp_file = inp_file
        self.load_file(self.inp_file)

    def get_sim_time(self):
        return self.elapsed_time_in_sec

    def elapsed_datetime(self):
        return self.start_datetime + datetime.timedelta(seconds=self.get_sim_time() )

    def set_datetime(self, start_datetime:datetime.datetime=None):
        try:
            if start_datetime == None:
                self.start_datetime = datetime.datetime.now()
            else:
                self.start_datetime = start_datetime

            self.current_datetime = self.start_datetime
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

    def reset(self, start_datetime:datetime.datetime=None):
        try:
            if self.epanetmodel is not None:
                timestep = self.get_hyd_step()
                self.load_file(self.inp_file)
                self.set_hyd_step(timestep)
            else:
                self.load_file(self.inp_file)


            if self.epanetmodel is not None:
                en.openH(self.epanetmodel.proj_for_simulation)
                en.initH(self.epanetmodel.proj_for_simulation, en.NOSAVE)

            self.elapsed_time_in_sec = 0
            self.set_datetime(start_datetime)

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

    def step(self):
        try:
            if self.epanetmodel is not None:
                self.elapsed_time_in_sec = self.next_time_step_in_sec

                en.runH(self.epanetmodel.proj_for_simulation)
                t = en.nextH(self.epanetmodel.proj_for_simulation)

                self.next_time_step_in_sec += t

                dur = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.DURATION)
                en.settimeparam(self.epanetmodel.proj_for_simulation, en.DURATION, dur + t)

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

    def load_file(self,inp_file):
        try:
            self.epanetmodel = epanet_fiware.epanetmodel.EPAnetModel('temp', inp_file)
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

    def get_pattern_step(self) -> float:
        return en.gettimeparam(self.epanetmodel.proj_for_simulation, en.PATTERNSTEP)

    def set_hyd_step(self, time_in_seconds):
        #GARETH -   this appears to be limited to a max of PATTERN TIMESTEP in the inp file
        #           changing pattern timestep just slows down/speeds up the simulation, it still
        #           has the same values but over a longer/shorter timeframe
        en.settimeparam(self.epanetmodel.proj_for_simulation, en.HYDSTEP, time_in_seconds)

    def get_hyd_step(self) -> float:
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

