from textwrap import indent
import local_environment_settings
import os

import inspect
import json

import matplotlib.collections
import unexefiware.base_logger
import unexefiware.fiwarewrapper
import unexefiware.time
import unexeaqua3s.resourcebuilder
import support
import datetime
import pyproj
import unexe_epanet.epanet_fiware
import unexewrapper


import epanet.toolkit as en
import matplotlib.pyplot as plt
import numpy as np


class epanet_localdata(unexe_epanet.epanet_model.epanet_model):
    def __init__(self):
        super().__init__()
        self.reset()

    def init(self, epanet_file:str, coord_system:pyproj.CRS, fiware_service:str, flip_coordindates:bool=False):

        self.flip_coordinates = flip_coordindates
        self.coord_system = coord_system
        self.transformer = pyproj.Transformer.from_crs(self.coord_system, pyproj.CRS.from_epsg(4326))

        super().init(epanet_file)

    def reset(self):
        super().reset()
        self.local_data = {}

        if self.epanetmodel:
            super().step()

            self.post()
            self.patch()

    def step(self):
        super().step()
        self.patch()

    def patch(self):
        #fudge fiware-like behaviour
        try:
            dp = 4

            num_nodes = self.getcount(object=en.NODECOUNT) + 1
            for index in range(1, num_nodes):
                nodeID = self.getnodeid(index)

                data = {}
                data['observedAt'] = unexefiware.time.datetime_to_fiware(self.elapsed_datetime() )
                self.local_data[nodeID].append(data)

                # unexe_epanet.c 2079
                # frame[nodeID]['supply'] = getnodevalue(index, en.SUPPLY)

                if nodeID == 'R.M.':
                    val =self.getnodevalue(index, en.PRESSURE)

                data['head'] = str(round(self.getnodevalue(index, en.HEAD),dp))
                data['pressure'] = str(round(self.getnodevalue(index, en.PRESSURE),dp))
                data['quality'] = str(round(self.getnodevalue(index, en.QUALITY),dp))

            num_links = self.getcount(object=en.LINKCOUNT) + 1

            for index in range(1, num_links):
                linkID = self.getlinkid(index)

                data = {}
                data['observedAt'] = unexefiware.time.datetime_to_fiware(self.elapsed_datetime() )
                self.local_data[linkID].append(data)

                # unexe_epanet.c 3580
                # frame[linkID]['reaction rate'] = getlinkvalue(index, en.REACTIONRATE)
                # frame[linkID]['friction'] = getlinkvalue(index, en.FRICTION)

                data['flow'] =  str(round(self.getlinkvalue(index, en.FLOW),dp))
                data['velocity'] = str(round(self.getlinkvalue(index, en.VELOCITY),dp))
                data['headloss'] = str(round(self.getlinkvalue(index, en.HEADLOSS),dp))
                data['quality'] = str(round(self.getlinkvalue(index, en.QUALITY),dp))
                data['status'] = str(round(self.getlinkvalue(index, en.STATUS),dp))
                data['setting'] = str(round(self.getlinkvalue(index, en.SETTING),dp))
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

    def post(self):
        # fudge fiware-like behaviour
        try:
            self.local_data = {}

            num_nodes = self.getcount(object=en.NODECOUNT) + 1
            for index in range(1, num_nodes):
                nodeID = self.getnodeid(index)

                self.local_data[nodeID] = []

            num_links = self.getcount(object=en.LINKCOUNT) + 1
            for index in range(1, num_links):
                linkID = self.getlinkid(index)

                self.local_data[linkID] = []
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)


def load_epanet_model(fiware_service):
    sim_model = unexe_epanet.epanet_fiware.epanet_fiware()
    #sim_model = epanet_localdata()

    print('GARETH - I have changed file loading !')
    #inp_file = os.environ['FILE_PATH'] + os.sep + os.environ['FILE_VISUALISER_FOLDER'] + os.sep + 'data' + os.sep + fiware_service + os.sep + 'waternetwork' + os.sep + 'unexe_epanet.inp'

    if fiware_service == 'AAA':
        inp_file = 'local_data' + os.sep+'TS network.inp'
        coord_system = pyproj.CRS.from_epsg(32632)
        sim_model.init(epanet_file=inp_file, coord_system=coord_system, fiware_service=fiware_service, flip_coordindates=True)

    if fiware_service == 'GUW':
        coord_system = pyproj.CRS.from_epsg(32646)
        inp_file = 'local_data' + os.sep+'KMKHYA_GHY_WDN.inp'

        sim_model.init(epanet_file=inp_file, coord_system=coord_system, fiware_service=fiware_service, flip_coordindates=True)

    sim_model.fiware_service = fiware_service

    return sim_model

sim_lookup = {}

def MIN_TO_SEC(x):
    return x*60

def SEC_TO_MIN(x):
    return int(x/60)

def testbed_sim_leak_management(sim:unexe_epanet.epanet_fiware, fiware_wrapper:unexefiware, logger:unexefiware.base_logger.BaseLogger):
    quitApp = False

    while quitApp is False:
        print('\n')
        
        num_nodes = sim.getcount(object=en.NODECOUNT) + 1
        for index in range(1, num_nodes):
            nodeID = sim.getnodeid(index)
            emitter = sim.getnodevalue(index, en.EMITTER)

            if sim.getnodetype(index) == en.JUNCTION:
                #GARETH - can only set emitter on junctions, not reservoirs or tanks
                print(str(index).ljust(3,' ') + ' ' + nodeID.ljust(30,' ') + ' ' + str(round(emitter,2)).rjust(10,' '))

        print('\n')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == 'x':
            quitApp = True
        else:
            try:
                index = int(key)

                if (index > 0) and (index < sim.getcount(object=en.NODECOUNT) + 1) and (sim.getnodetype(index) == en.JUNCTION):
                    emitter = sim.getnodevalue(index, en.EMITTER)

                    if emitter < 1:
                        #create a nice leak
                        emitter = 9999
                    else:
                        # stop a nice leak
                        emitter = 0

                    sim.setnodevalue(index, en.EMITTER, emitter)
                    emitter = sim.getnodevalue(index, en.EMITTER)
                    print(str(emitter))

            except Exception as e:
                logger.exception(inspect.currentframe(),e)

def chart_nodes(sim:unexe_epanet.epanet_fiware, fiware_wrapper:unexefiware, logger:unexefiware.base_logger.BaseLogger):
    quitApp = False

    while quitApp is False:
        print('\n')
        
        num_nodes = sim.getcount(object=en.NODECOUNT) + 1
        for index in range(1, num_nodes):
            nodeID = sim.getnodeid(index)
            emitter = sim.getnodevalue(index, en.EMITTER)

            print(str(index).ljust(3, ' ') + ' ' + nodeID.ljust(30, ' ') + ' ' + str(round(emitter, 2)).rjust(10, ' '))

        print('\n')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == 'x':
            quitApp = True
        else:
            try:
                #get the ID from the entry
                #grind data out of 'fiware'
                #make a nice graph
                node_index = int(key)

                if (node_index > 0) and (node_index < sim.getcount(object=en.NODECOUNT) + 1):
                    nodeID = sim.getnodeid(node_index)

                    attribute = 'pressure'

                    y = []
                    x = []
                    try:
                        step = 1
                        for entry in sim.local_data[nodeID]:
                            x.append(step)
                            step += 1
                            y.append( float(entry[attribute]))

                    except Exception as e:
                        logger = unexefiware.base_logger.BaseLogger()
                        logger.exception(inspect.currentframe(), e)

                    fig = plt.figure(dpi=200)

                    ax = fig.add_subplot(1, 1, 1)
                    ax.plot(x, y)

                    title = nodeID
                    title += ' '
                    title += attribute
                    title += '\n'
                    title += str(int(sim.get_sim_time()/sim.get_hyd_step())) + ' steps, date time:' + str(sim.elapsed_datetime())

                    plt.title(title)
                    plt.xlabel('')
                    plt.ylabel('')

                    plt.show()

            except Exception as e:
                logger.exception(inspect.currentframe(), e)

def chart_links(sim:unexe_epanet.epanet_fiware, fiware_wrapper:unexefiware, logger:unexefiware.base_logger.BaseLogger):
    quitApp = False

    while quitApp is False:
        print('\n')        

        num_links = sim.getcount(object=en.LINKCOUNT) + 1
        for index in range(1, num_links):
            linkID = sim.getlinkid(index)

            print(str(index).ljust(3, ' ') + ' ' + linkID.ljust(30, ' '))

        print('\n')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == 'x':
            quitApp = True
        else:
            try:
                node_index = int(key)

                if (node_index > 0) and (node_index < sim.getcount(object=en.LINKCOUNT) + 1):
                    nodeID = sim.getlinkid(node_index)

                    attribute = 'flow'

                    y = []
                    x = []
                    try:
                        step = 1
                        for entry in sim.local_data[nodeID]:
                            x.append(step)
                            step += 1
                            y.append( float(entry[attribute]))

                    except Exception as e:
                        logger = unexefiware.base_logger.BaseLogger()
                        logger.exception(inspect.currentframe(), e)

                    fig = plt.figure(dpi=200)

                    ax = fig.add_subplot(1, 1, 1)
                    ax.plot(x, y)

                    title = nodeID
                    title += ' '
                    title += attribute
                    title += '\n'
                    title += str(int(sim.get_sim_time()/sim.get_hyd_step())) + ' steps, date time:' + str(sim.elapsed_datetime())

                    plt.title(title)
                    plt.xlabel('')
                    plt.ylabel('')

                    plt.show()

            except Exception as e:
                logger.exception(inspect.currentframe(), e)

def testbed_fiware(fiware_wrapper:unexefiware,fiware_service:str, logger:unexefiware.base_logger.BaseLogger, current_datetime_fiware:str):
    quitApp = False

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + fiware_service)

        print('\n')
        print('1..Current Devices')
        print('2..Historic Devices')
        print('X..Back')
        print('\n')

        key = input('>')

        if key == 'x':
            quitApp = True

        if key == '1':
            print('Devices')
            result = fiware_wrapper.get_all_type(fiware_service, 'Device')

            if result[0] == 200:
                for entity in result[1]:
                    print(entity['id'])

            print()

        if key == '2':
            print('Historic Devices')

            start_date = '1971-01-01T00:00:00Z'

            result = []
            if fiware_service == 'AAA':
                result = fiware_wrapper.get_temporal(fiware_service, 'urn:ngsi-ld:Device:FLOW:BP600.1500.BP2600.15.1', ['flow'], start_date,current_datetime_fiware)
            else:
                result = fiware_wrapper.get_temporal(fiware_service, 'urn:ngsi-ld:Device:FLOW:GP1', ['flow'], start_date,current_datetime_fiware)

            if result[0] == 200:
                print(json.dumps(result[1], indent=3))



def testbed_sim_management(fiware_wrapper:unexewrapper, fiware_service:str, logger:unexefiware.base_logger.BaseLogger):
    quitApp = False

    sim_inst = load_epanet_model(fiware_service)
    sim_inst.set_hyd_step(MIN_TO_SEC(60))
    sim_inst.reset(datetime.datetime(year=2023, month=1, day=1, hour=0,minute=0,second=0))

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + fiware_service)
        print('Sim time: ' + str(sim_inst.get_sim_time()) + ' ' + str(sim_inst.elapsed_datetime() ))
        print('Sim step: ' + str(SEC_TO_MIN(sim_inst.get_hyd_step())) +'min' )

        print('\n')
        print('1..Reset Sim')
        print('2..Run a step: ' + str( int(SEC_TO_MIN(sim_inst.get_hyd_step()))) + ' min' )
        print('3..Run 12 hours: ' + str( int(12*60 / SEC_TO_MIN(sim_inst.get_hyd_step()))) + ' steps')
        print('4..Run a day: '  + str( int(24*60 / SEC_TO_MIN(sim_inst.get_hyd_step()))) + ' steps')
        print('5..Leak Management')
        print('6..Node charts')
        print('7..Link charts')
        print('8..WDN graph')
        print('9..FIWARE')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == 'x':
            quitApp = True

        if key == '1':
            print('Reset')
            sim_inst.reset()

        if key == '2':
            print('Run a step')
            sim_inst.step()

        if key == '3':
            print('Run 12 steps')
            time_steps = int(12*60 / SEC_TO_MIN(sim_inst.get_hyd_step()))

            for i in range(0, time_steps):
                sim_inst.step()

        if key == '4':
            print('Run a day')
            time_steps = int(24*60 / SEC_TO_MIN(sim_inst.get_hyd_step()))

            for i in range(0, time_steps):
                sim_inst.step()

        if key == '5':
            testbed_sim_leak_management(sim_inst, fiware_wrapper, logger)

        if key == '6':
            chart_nodes(sim_inst, fiware_wrapper, logger)

        if key == '7':
            chart_links(sim_inst, fiware_wrapper, logger)

        if key =='8':
            fig = plt.figure(dpi=200)
            ax = fig.add_subplot(1, 1, 1)

            #do links
            try:
                lines = []
                col = []
                num_links = sim_inst.getcount(object=en.LINKCOUNT) + 1

                for link_index in range(1, num_links):
                    link_node_indices = sim_inst.getlinknodes(link_index)

                    coords = []
                    coords.append(sim_inst.getcoord(link_node_indices[0]))

                    num_vertices = sim_inst.getvertexcount(link_index)

                    if num_vertices:
                        for vertex in range(1, num_vertices + 1):
                            coords.append(sim_inst.getvertex(link_index, vertex))

                    coords.append(sim_inst.getcoord(link_node_indices[1]))

                    segment = []
                    for i in range(0,len(coords)):
                        coords[i] = sim_inst.transformer.transform(coords[i][0], coords[i][1])

                        if sim_inst.flip_coordinates:
                            coords[i] = [coords[i][1], coords[i][0]]

                    for i in range(0,len(coords)-1):
                        line = [(coords[i][0], coords[i][1]), (coords[i+1][0], coords[i+1][1])]
                        lines.append(line)
                        col.append((1, 0, 0, 1))

                lc = matplotlib.collections.LineCollection(lines, colors=col, linewidths=2)

                ax.add_collection(lc)
                ax.autoscale()
                ax.margins(0.1)

            except Exception as e:
                logger.exception(inspect.currentframe(), e)

            #do nodes
            x = []
            y = []

            num_nodes = sim_inst.getcount(object=en.NODECOUNT) + 1
            for node_index in range(1, num_nodes):
                nodeID = sim_inst.getnodeid(node_index)

                coordinates = sim_inst.getcoord(node_index)

                coords = list(coordinates)

                coords = sim_inst.transformer.transform(coords[0], coords[1])

                if sim_inst.flip_coordinates:
                    coords = [coords[1], coords[0]]

                x.append(coords[0])
                y.append(coords[1])

                ax.scatter(x, y, s=10, c=[[0, 0, 1, 1]], zorder=2)

            plt.show()

        if key == '9':
            testbed_fiware(fiware_wrapper, fiware_service, logger, unexefiware.time.datetime_to_fiware(sim_inst.elapsed_datetime()) )

if __name__ == '__main__':
    #testbed()
    logger = unexefiware.base_logger.BaseLogger()

    fiware_wrapper = unexewrapper.unexewrapper(url=os.environ['DEVICE_BROKER'])
    fiware_wrapper.init(logger=logger)

    fiware_service = 'GUW'

    testbed_sim_management(fiware_wrapper, fiware_service, logger)
