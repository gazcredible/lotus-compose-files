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


def load_epanet_model(fiware_service):
    sim_model = unexe_epanet.epanet_fiware.epanet_fiware()

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

            start_date = '1971-01-02T00:00:00Z'

            nodeID = ''
            property = 'flow'

            result = []
            if fiware_service == 'AAA':
                nodeID = 'urn:ngsi-ld:Device:BP600.1500.BP2600.15.1'
                property = 'flow'

                nodeID = 'urn:ngsi-ld:Device:R.M.'
                property = 'pressure'
                result = fiware_wrapper.get_temporal(fiware_service, nodeID, [property], start_date,current_datetime_fiware)
            else:
                nodeID = 'urn:ngsi-ld:Device:GP1'
                property = 'flow'
                result = fiware_wrapper.get_temporal(fiware_service, nodeID, [property], start_date,current_datetime_fiware)

            if result[0] == 200:
                #print(json.dumps(result[1], indent=3))

                fig = plt.figure(dpi=200)
                ax = fig.add_subplot(1, 1, 1)
                x = []
                y = []

                try:
                    step = 0
                    for entry in result[1][property]['values']:
                        x.append(step)
                        step += 1
                        y.append(float(entry[0]))

                except Exception as e:
                    logger = unexefiware.base_logger.BaseLogger()
                    logger.exception(inspect.currentframe(), e)

                fig = plt.figure(dpi=200)

                ax = fig.add_subplot(1, 1, 1)
                ax.plot(x, y)

                title = nodeID
                title += ' '
                title += property
                title += '\n'
                title += str(step) + ' steps, date time:' + str(current_datetime_fiware)

                plt.title(title)
                plt.xlabel('')
                plt.ylabel('')

                plt.show()


def testbed_epanet_graph(sim_inst, logger):
    fig = plt.figure(dpi=200)
    ax = fig.add_subplot(1, 1, 1)

    # do links
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
            for i in range(0, len(coords)):
                coords[i] = sim_inst.transformer.transform(coords[i][0], coords[i][1])

                if sim_inst.flip_coordinates:
                    coords[i] = [coords[i][1], coords[i][0]]

            for i in range(0, len(coords) - 1):
                line = [(coords[i][0], coords[i][1]), (coords[i + 1][0], coords[i + 1][1])]
                lines.append(line)
                col.append((1, 0, 0, 1))

        lc = matplotlib.collections.LineCollection(lines, colors=col, linewidths=2)

        ax.add_collection(lc)
        ax.autoscale()
        ax.margins(0.1)

    except Exception as e:
        logger.exception(inspect.currentframe(), e)

    # do nodes
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


def testbed_sim_management(fiware_wrapper:unexewrapper, fiware_service:str, logger:unexefiware.base_logger.BaseLogger):
    quitApp = False

    sensor_list = []
    start_datetime = datetime.datetime(year=2023, month=1, day=1, hour=0,minute=0,second=0)

    if fiware_service == 'GUW':
        sensor_list=[{'ID': 'GJ409', 'Type': 'pressure'}, {'ID': 'GP1', 'Type': 'flow'}]

    if fiware_service == 'AAA':
        sensor_list=[{'ID': 'R.M.', 'Type': 'pressure'}, {'ID': 'BP600.1500.BP2600.15.1', 'Type': 'flow'}]

    sim_inst = load_epanet_model(fiware_service)
    sim_inst.set_hyd_step(MIN_TO_SEC(60))
    sim_inst.reset(sensor_list, start_datetime)

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
        print('8..WDN graph')
        print('9..FIWARE')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == 'x':
            quitApp = True

        if key == '1':
            print('Reset')
            sim_inst.reset(sensor_list, start_datetime)

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

        if key =='8':
            testbed_epanet_graph(sim_inst, logger)

        if key == '9':
            testbed_fiware(fiware_wrapper, fiware_service, logger, unexefiware.time.datetime_to_fiware(sim_inst.elapsed_datetime()) )

if __name__ == '__main__':
    #testbed()
    logger = unexefiware.base_logger.BaseLogger()

    fiware_wrapper = unexewrapper.unexewrapper(url=os.environ['DEVICE_BROKER'])
    fiware_wrapper.init(logger=logger)

    fiware_service = 'GUW'

    testbed_sim_management(fiware_wrapper, fiware_service, logger)
