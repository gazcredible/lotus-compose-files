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
import unexe_epanet.epanet_model
import unexewrapper


import epanet.toolkit as en
import matplotlib.pyplot as plt
import numpy as np

def testbed(fiware_wrapper:unexefiware,sim_inst:unexe_epanet.epanet_fiware.epanet_fiware):#fiware_service:str, logger:unexefiware.base_logger.BaseLogger, current_datetime_fiware:str):
    quitApp = False

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + sim_inst.fiware_service)

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
            result = fiware_wrapper.get_all_type(sim_inst.fiware_service, 'Device')

            if result[0] == 200:
                for entity in result[1]:
                    print(entity['id'])
                    print(str(entity['controlledProperty']['value']))

            print()

        if key == '2':
            print('Historic Devices')

            start_date = '1971-01-02T00:00:00Z'
            current_datetime_fiware = unexefiware.time.datetime_to_fiware(sim_inst.elapsed_datetime())

            device_list = fiware_wrapper.get_all_type(sim_inst.fiware_service, 'Device')

            if device_list[0] == 200:
                for entity in device_list[1]:

                    for controlled_property in entity['controlledProperty']['value']:
                        result = fiware_wrapper.get_temporal(sim_inst.fiware_service, entity['id'], [controlled_property], start_date,current_datetime_fiware)

                        if result[0] == 200:
                            x = []
                            y = []

                            try:
                                step = 0
                                for entry in result[1][controlled_property]['values']:
                                    x.append( unexe_epanet.epanet_model.SEC_TO_HOUR(step) )
                                    step += sim_inst.get_hyd_step()
                                    y.append(float(entry[0]))

                            except Exception as e:
                                logger = unexefiware.base_logger.BaseLogger()
                                logger.exception(inspect.currentframe(), e)

                            fig = plt.figure(dpi=200)

                            ax = fig.add_subplot(1, 1, 1)
                            ax.plot(x, y)

                            title = entity['id']
                            title += ' '
                            title += controlled_property
                            title += '\n'
                            title += str(round(unexe_epanet.epanet_model.SEC_TO_HOUR(step),2)) + ' hours, date time:' + str(current_datetime_fiware)

                            plt.title(title)
                            plt.xlabel('')
                            plt.ylabel('')

                            plt.show()


def sim_leak_management(sim: unexe_epanet.epanet_fiware, logger=None):
    quitApp = False

    while quitApp is False:
        print('\n')

        num_nodes = sim.getcount(object=en.NODECOUNT) + 1
        for index in range(1, num_nodes):
            nodeID = sim.getnodeid(index)
            emitter = sim.getnodevalue(index, en.EMITTER)

            if sim.getnodetype(index) == en.JUNCTION:
                # GARETH - can only set emitter on junctions, not reservoirs or tanks
                print(str(index).ljust(3, ' ') + ' ' + nodeID.ljust(30, ' ') + ' ' + str(round(emitter, 6)).rjust(10, ' '))

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
                        # create a nice leak
                        emitter = 9999
                        emitter = 5 * 1
                    else:
                        # stop a nice leak
                        emitter = 0

                    sim.setnodevalue(index, en.EMITTER, emitter)
                    emitter = sim.getnodevalue(index, en.EMITTER)
                    print(str(emitter))

            except Exception as e:
                sim.logger.exception(inspect.currentframe(), e)


def epanet_graph(sim_inst, logger):
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
