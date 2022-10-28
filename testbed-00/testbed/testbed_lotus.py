import local_environment_settings
import os

import inspect

import matplotlib.collections
import unexefiware.base_logger
import unexefiware.fiwarewrapper
import unexeaqua3s.resourcebuilder
import support
import datetime
import pyproj
import sim.epanet_model
import sim.epasim_fiware


import epanet.toolkit as en
import matplotlib.pyplot as plt
import numpy as np

#GARETH replace with env.var
pilot_list = ['AAA','GUW']

def testbed_webdav(fiware_wrapper, fiware_service, logger):
    quitApp = False

    options = {
        'webdav_hostname': os.environ['WEBDAV_URL'],
        'webdav_login': os.environ['WEBDAV_NAME'],
        'webdav_password': os.environ['WEBDAV_PASS']
    }

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + fiware_service)

        print('\n')
        print('1..View webdav content')
        print('2..Setup webdav from local files')
        print('3..View FIWARE userlayers')
        print('4..Build FIWARE userlayers')
        print('5..Delete FIWARE userlayers')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            resourcebuilder = unexeaqua3s.resourcebuilder.ResourceBuilder(options=options)
            resourcebuilder.convert_files = False
            resourcebuilder.perform_file_operations = False
            resourcebuilder.remote_root = '/data/'

            for pilot in pilot_list:
                print(pilot)
                resourcebuilder.print_remote_tree(resourcebuilder.remote_root + os.sep + pilot + os.sep)
                print()

        if key == '2':
            dav = unexeaqua3s.webdav.webdav(options)

            if dav.is_remote_available():
                dav.copy_to_dav('local_data/KMKHYA_GHY_WDN.inp', 'data/GUW/epanet/KMKHYA_GHY_WDN.inp')
                dav.copy_to_dav('local_data/KMKHYA_GHY_WDN.inp', 'data/GUW/waternetwork/epanet.inp')

                dav.copy_to_dav('local_data/TS network.inp', 'data/AAA/epanet/TS network.inp')
                dav.copy_to_dav('local_data/TS network.inp', 'data/AAA/waternetwork/epanet.inp')
            else:
                logger.fail(inspect.currentframe(), 'Webdav not available')

        if key == '3':
            for pilot in pilot_list:
                print(pilot)
                support.print_resources(os.environ['DEVICE_BROKER'], pilot.replace(' ', ''), ['WaterNetwork'] )
                print()

        if key == '4':
            force_build_files = True
            create_fiware_resources = True

            resourcebuilder = unexeaqua3s.resourcebuilder.ResourceBuilder(options=options)
            resourcebuilder.convert_files = True
            resourcebuilder.perform_file_operations = True
            # gareth -   this is the same as the path in visualiser.resourceManager
            resourcebuilder.remote_root = '/data/'
            resourcebuilder.init(path_root=os.environ['FILE_PATH'] + os.sep + 'visualiser', clone_remote=True, pilot_list=pilot_list)

            for service in pilot_list:
                resourcebuilder.clone_pilot(service)

            resources = resourcebuilder.process_kmz_resources()
            resources += resourcebuilder.process_shapefile_resources(force_build_files)
            resources += resourcebuilder.process_waternetwork_resources()

            if create_fiware_resources:
                resourcebuilder.create_fiware_assets(os.environ['DEVICE_BROKER'], resources)

        if key == '5':
            for pilot in pilot_list:
                support.delete_resources(os.environ['DEVICE_BROKER'], pilot.replace(' ', ''), ['WaterNetwork', 'SimulationResult', 'UserLayer'])

        if key == 'x':
            quitApp = True


def load_sim_data(fiware_service):
    epasim_fiware_model = sim.epasim_fiware.epasim_fiware()

    print('GARETH - I have changed file loading !')
    #inp_file = os.environ['FILE_PATH'] + os.sep + os.environ['FILE_VISUALISER_FOLDER'] + os.sep + 'data' + os.sep + fiware_service + os.sep + 'waternetwork' + os.sep + 'epanet.inp'

    if fiware_service == 'AAA':
        inp_file = 'local_data' + os.sep+'TS network.inp'
        coord_system = pyproj.CRS.from_epsg(32632)
        epasim_fiware_model.init(epanet_file=inp_file, coord_system=coord_system, fiware_service=fiware_service, flip_coordindates=True)

    if fiware_service == 'GUW':
        coord_system = pyproj.CRS.from_epsg(32646)
        inp_file = 'local_data' + os.sep+'KMKHYA_GHY_WDN.inp'

        epasim_fiware_model.init(epanet_file=inp_file, coord_system=coord_system, fiware_service=fiware_service, flip_coordindates=True)

    return epasim_fiware_model

sim_lookup = {}

def testbed_device(fiware_wrapper:unexefiware.fiwarewrapper.fiwareWrapper, fiware_service:str, logger:unexefiware.base_logger.BaseLogger):
    quitApp = False



    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + fiware_service)

        print('\n')
        print('1..View Devices')
        print('2..Create from EPANET')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=fiware_wrapper)
            deviceInfo.run()

            support.print_devices(deviceInfo)

        if key == '2':
            sensors = sim_lookup[fiware_service].get_sensors()
            fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.now())
            sim_lookup[fiware_service].create_entities(fiware_wrapper, fiware_service, fiware_time, sensors)

        if key == 'x':
            quitApp = True

def make_a_graph(fiware_service, time_steps=90, link_name:str=None, node_name:str=None, param:int=en.FLOW):
    inst = load_sim_data(fiware_service)
    inst.simulation_model.set_hyd_step(1*60*60)
    inst.simulation_model.reset()

    y = []
    x = []
    for i in range(0, time_steps):
        inst.simulation_model.step()

        x.append(i)

        try:
            if link_name is not None:
                pipeIndex = inst.simulation_model.getlinkindex(link_name)
                y.append(inst.simulation_model.getlinkvalue(pipeIndex, param))

            if node_name is not None:
                index = inst.simulation_model.getnodeindex(node_name)
                val = inst.simulation_model.getnodevalue(index, param)
                y.append(val)

                print(str(i).ljust(4,' ') + str(round(val,4)) +' ' + str(inst.simulation_model.elapsed_time_in_sec) )

                emitter = inst.simulation_model.getnodevalue(index, en.EMITTER)

        except Exception as e:
            logger = unexefiware.base_logger.BaseLogger()
            logger.exception(inspect.currentframe(), e)

    fig = plt.figure(dpi=200)

    ax = fig.add_subplot(1, 1, 1)
    ax.plot(x, y)

    title = ''

    if link_name is not None:
        title = link_name

    if node_name is not None:
        title = node_name

    title += ' '
    if param == en.FLOW:
        title +='flow'

    if param == en.PRESSURE:
        title +='pressure'

    plt.title(title)
    plt.xlabel('')
    plt.ylabel('')

    plt.show()

def MIN_TO_SEC(x):
    return x*60

def SEC_TO_MIN(x):
    return int(x/60)
class SimManagement:
    def __init__(self):
        self.fiware_data = {}

    def init(self, fiware_service):
        self.inst = load_sim_data(fiware_service)
        self.inst.simulation_model.set_hyd_step(MIN_TO_SEC(60) )

        self.reset()
    def reset(self):
        #2023-01-01 just happens to start on sunday
        self.start_datetime = datetime.datetime(year=2023, month=1, day=1, hour=0,minute=0,second=0)
        self.inst.simulation_model.reset()

        self.fiware_data = {}

        self.inst.simulation_model.step()

        self.post()
        self.patch()

    def do_step(self):
        self.inst.simulation_model.step()
        self.patch()

    def get_hyd_step(self):
        return self.inst.simulation_model.get_hyd_step()

    def get_sim_time(self):
        return self.inst.simulation_model.elapsed_time_in_sec

    def elapsed_datetime(self):
        return self.start_datetime + datetime.timedelta(seconds=self.inst.simulation_model.elapsed_time_in_sec)

    def patch(self):
        #fudge fiware-like behaviour

        dp = 4

        num_nodes = self.inst.simulation_model.getcount(object=en.NODECOUNT) + 1
        for index in range(1, num_nodes):
            nodeID = self.inst.simulation_model.getnodeid(index)

            data = {}
            data['observedAt'] = unexefiware.time.datetime_to_fiware(self.elapsed_datetime() )
            self.fiware_data[nodeID].append(data)

            # epanet.c 2079
            # frame[nodeID]['supply'] = inst.simulation_model.getnodevalue(index, en.SUPPLY)

            if nodeID == 'R.M.':
                val =self.inst.simulation_model.getnodevalue(index, en.PRESSURE)

            data['head'] = str(round(self.inst.simulation_model.getnodevalue(index, en.HEAD),dp))
            data['pressure'] = str(round(self.inst.simulation_model.getnodevalue(index, en.PRESSURE),dp))
            data['quality'] = str(round(self.inst.simulation_model.getnodevalue(index, en.QUALITY),dp))

        num_links = self.inst.simulation_model.getcount(object=en.LINKCOUNT) + 1
        for index in range(1, num_links):
            linkID = self.inst.simulation_model.getlinkid(index)

            data = {}
            data['observedAt'] = unexefiware.time.datetime_to_fiware(self.elapsed_datetime() )
            self.fiware_data[linkID].append(data)

            # epanet.c 3580
            # frame[linkID]['reaction rate'] = inst.simulation_model.getlinkvalue(index, en.REACTIONRATE)
            # frame[linkID]['friction'] = inst.simulation_model.getlinkvalue(index, en.FRICTION)

            data['flow'] =  str(round(self.inst.simulation_model.getlinkvalue(index, en.FLOW),dp))
            data['velocity'] = str(round(self.inst.simulation_model.getlinkvalue(index, en.VELOCITY),dp))
            data['headloss'] = str(round(self.inst.simulation_model.getlinkvalue(index, en.HEADLOSS),dp))
            data['quality'] = str(round(self.inst.simulation_model.getlinkvalue(index, en.QUALITY),dp))
            data['status'] = str(round(self.inst.simulation_model.getlinkvalue(index, en.STATUS),dp))
            data['setting'] = str(round(self.inst.simulation_model.getlinkvalue(index, en.SETTING),dp))
    def post(self):
        #fudge fiware-like behaviour

        self.fiware_data = {}

        num_nodes = self.inst.simulation_model.getcount(object=en.NODECOUNT) + 1
        for index in range(1, num_nodes):
            nodeID = self.inst.simulation_model.getnodeid(index)

            self.fiware_data[nodeID] = []

        num_links = self.inst.simulation_model.getcount(object=en.LINKCOUNT) + 1
        for index in range(1, num_links):
            linkID = self.inst.simulation_model.getlinkid(index)

            self.fiware_data[linkID] = []

def testbed_sim_leak_management(sim:SimManagement, fiware_wrapper:unexefiware.fiwarewrapper.fiwareWrapper, logger:unexefiware.base_logger.BaseLogger):
    quitApp = False

    while quitApp is False:
        print('\n')
        
        num_nodes = sim.inst.simulation_model.getcount(object=en.NODECOUNT) + 1
        for index in range(1, num_nodes):
            nodeID = sim.inst.simulation_model.getnodeid(index)
            emitter = sim.inst.simulation_model.getnodevalue(index, en.EMITTER)

            if sim.inst.simulation_model.getnodetype(index) == en.JUNCTION:
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

                if (index > 0) and (index < sim.inst.simulation_model.getcount(object=en.NODECOUNT) + 1) and (sim.inst.simulation_model.getnodetype(index) == en.JUNCTION):
                    emitter = sim.inst.simulation_model.getnodevalue(index, en.EMITTER)

                    if emitter < 1:
                        #create a nice leak
                        emitter = 9999
                    else:
                        # stop a nice leak
                        emitter = 0

                    sim.inst.simulation_model.setnodevalue(index, en.EMITTER, emitter)
                    emitter = sim.inst.simulation_model.getnodevalue(index, en.EMITTER)
                    print(str(emitter))

            except Exception as e:
                logger.exception(inspect.currentframe(),e)

def chart_nodes(sim:SimManagement, fiware_wrapper:unexefiware.fiwarewrapper.fiwareWrapper, logger:unexefiware.base_logger.BaseLogger):
    quitApp = False

    while quitApp is False:
        print('\n')
        
        num_nodes = sim.inst.simulation_model.getcount(object=en.NODECOUNT) + 1
        for index in range(1, num_nodes):
            nodeID = sim.inst.simulation_model.getnodeid(index)
            emitter = sim.inst.simulation_model.getnodevalue(index, en.EMITTER)

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

                if (node_index > 0) and (node_index < sim.inst.simulation_model.getcount(object=en.NODECOUNT) + 1):
                    nodeID = sim.inst.simulation_model.getnodeid(node_index)

                    attribute = 'pressure'

                    y = []
                    x = []
                    try:
                        step = 1
                        for entry in sim.fiware_data[nodeID]:
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

def chart_links(sim:SimManagement, fiware_wrapper:unexefiware.fiwarewrapper.fiwareWrapper, logger:unexefiware.base_logger.BaseLogger):
    quitApp = False

    while quitApp is False:
        print('\n')        

        num_links = sim.inst.simulation_model.getcount(object=en.LINKCOUNT) + 1
        for index in range(1, num_links):
            linkID = sim.inst.simulation_model.getlinkid(index)

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

                if (node_index > 0) and (node_index < sim.inst.simulation_model.getcount(object=en.LINKCOUNT) + 1):
                    nodeID = sim.inst.simulation_model.getlinkid(node_index)

                    attribute = 'flow'

                    y = []
                    x = []
                    try:
                        step = 1
                        for entry in sim.fiware_data[nodeID]:
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

def testbed_sim_management(fiware_wrapper:unexefiware.fiwarewrapper.fiwareWrapper, fiware_service:str, logger:unexefiware.base_logger.BaseLogger):
    quitApp = False

    sim_inst = SimManagement()
    sim_inst.init(fiware_service)

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
            sim_inst.do_step()

        if key == '3':
            print('Run 12 steps')
            time_steps = int(12*60 / SEC_TO_MIN(sim_inst.get_hyd_step()))

            for i in range(0, time_steps):
                sim_inst.do_step()

        if key == '4':
            print('Run a day')
            time_steps = int(24*60 / SEC_TO_MIN(sim_inst.get_hyd_step()))

            for i in range(0, time_steps):
                sim_inst.do_step()

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
                num_links = sim_inst.inst.getcount(object=en.LINKCOUNT) + 1

                for link_index in range(1, num_links):
                    link_node_indices = sim_inst.inst.simulation_model.getlinknodes(link_index)

                    coords = []
                    coords.append(sim_inst.inst.simulation_model.getcoord(link_node_indices[0]))

                    num_vertices = sim_inst.inst.simulation_model.getvertexcount(link_index)

                    if num_vertices:
                        for vertex in range(1, num_vertices + 1):
                            coords.append(sim_inst.inst.simulation_model.getvertex(link_index, vertex))

                    coords.append(sim_inst.inst.simulation_model.getcoord(link_node_indices[1]))

                    segment = []
                    for i in range(0,len(coords)):
                        coords[i] = sim_inst.inst.transformer.transform(coords[i][0], coords[i][1])

                        if sim_inst.inst.flip_coordinates:
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

            num_nodes = sim_inst.inst.getcount(object=en.NODECOUNT) + 1
            for node_index in range(1, num_nodes):
                nodeID = sim_inst.inst.simulation_model.getnodeid(node_index)

                coordinates = sim_inst.inst.simulation_model.getcoord(node_index)

                coords = list(coordinates)

                coords = sim_inst.inst.transformer.transform(coords[0], coords[1])

                if sim_inst.inst.flip_coordinates:
                    coords = [coords[1], coords[0]]

                x.append(coords[0])
                y.append(coords[1])

                ax.scatter(x, y, s=10, c=[[0, 0, 1, 1]], zorder=2)

            plt.show()


def testbed_sim(fiware_wrapper, logger):
    quitApp = False

    fiware_service = 'AAA'
    #fiware_service = 'GUW'

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + fiware_service)

        print('\n')
        print('1..View Current')
        print('2..Run a step')
        print('3..Graph?')
        print('4..Reset')
        print('5..Leak Management')
        print('6..Grind attributes')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            elapsed_time = sim_lookup[fiware_service].simulation_model.elapsed_time_in_sec
            elapsed_time /= (60 * 60)
            elapsed_time = int(elapsed_time)

            print(str(elapsed_time))

        if key == '2':
            sim_lookup[fiware_service].simulation_model.step()
            elapsed_time = sim_lookup[fiware_service].simulation_model.elapsed_time_in_sec

            print(fiware_service + ' ' + str(datetime.timedelta(seconds=elapsed_time) + datetime.timedelta(days=1)) + ' ' + str(elapsed_time) )

        if key == '3':
            print('Graphing stuff')

            if True:
                #make_a_graph(fiware_service, time_steps=180, link_name='POZZO_16.IN.RAD.DN600.1', node_name=None, param=en.FLOW)
                make_a_graph(fiware_service, time_steps=180, link_name=None, node_name='R.M.', param=en.PRESSURE)

        if key == '4':
            sim_lookup[fiware_service].simulation_model.reset()

        if key == '5':
            print('Leak Management')
            inst = load_sim_data(fiware_service)
            inst.simulation_model.set_hyd_step(1 * 60 * 60)
            inst.simulation_model.reset()

            node_name = 'R.M.'
            time_steps = 180

            y = []
            x = []
            emitter = 9999
            for i in range(0, time_steps):
                index = inst.simulation_model.getnodeindex(node_name)
                if i==50: #make a leak
                    inst.simulation_model.setnodevalue(index, en.EMITTER, emitter)
                    new_val = inst.simulation_model.getnodevalue(index, en.EMITTER)


                inst.simulation_model.step()

                x.append(i)

                try:
                    index = inst.simulation_model.getnodeindex(node_name)
                    y.append(inst.simulation_model.getnodevalue(index, en.PRESSURE))

                except Exception as e:
                    logger = unexefiware.base_logger.BaseLogger()
                    logger.exception(inspect.currentframe(), e)

            fig = plt.figure(dpi=200)

            ax = fig.add_subplot(1, 1, 1)
            ax.plot(x, y)

            if True:
                plt.title(node_name + ' leak @ t=50 e=' + str(emitter) + ' ' + ' pressure')

            plt.xlabel('')
            plt.ylabel('')

            plt.show()

        if key =='6':
            #node - supply, head, pressure, quality
            #link - flow, velocity, headloss, quality, status, setting, reaction rate, friction
            inst = load_sim_data(fiware_service)
            inst.simulation_model.set_hyd_step(15*60) #15min updates
            inst.simulation_model.reset()

            time_steps = int(7 * 24 * (60/15) ) #number of steps for 7 days (of 24hr * 60/15 updates per hour))

            data = []

            for i in range(0, time_steps):

                elapsed_time = inst.simulation_model.elapsed_time_in_sec
                elapsed_time /= (60 * 60)
                elapsed_time = int(elapsed_time)

                print(fiware_service + ' ' + str(datetime.timedelta(seconds=inst.simulation_model.elapsed_time_in_sec) + datetime.timedelta(days=1)) + ' ' + str(elapsed_time) )

                inst.simulation_model.step()

                frame = {}
                data.append(frame)
                try:
                    num_nodes = inst.simulation_model.getcount(object=en.NODECOUNT) + 1
                    for index in range(1, num_nodes):
                        nodeID = inst.simulation_model.getnodeid(index)

                        frame[nodeID] = {}
                        #epanet.c 2079
                        #frame[nodeID]['supply'] = inst.simulation_model.getnodevalue(index, en.SUPPLY)
                        frame[nodeID]['head'] = inst.simulation_model.getnodevalue(index, en.HEAD)
                        frame[nodeID]['pressure'] = inst.simulation_model.getnodevalue(index, en.PRESSURE)
                        frame[nodeID]['quality'] = inst.simulation_model.getnodevalue(index, en.QUALITY)

                    num_links = inst.simulation_model.getcount(object=en.LINKCOUNT) + 1
                    for index in range(1, num_links):
                        linkID = inst.simulation_model.getlinkid(index)

                        frame[linkID] = {}

                        # epanet.c 3580
                        frame[linkID]['flow'] = inst.simulation_model.getlinkvalue(index, en.FLOW)
                        frame[linkID]['velocity'] = inst.simulation_model.getlinkvalue(index, en.VELOCITY)
                        frame[linkID]['headloss'] = inst.simulation_model.getlinkvalue(index, en.HEADLOSS)
                        frame[linkID]['quality'] = inst.simulation_model.getlinkvalue(index, en.QUALITY)
                        frame[linkID]['status'] = inst.simulation_model.getlinkvalue(index, en.STATUS)
                        frame[linkID]['setting'] = inst.simulation_model.getlinkvalue(index, en.SETTING)
                        #frame[linkID]['reaction rate'] = inst.simulation_model.getlinkvalue(index, en.REACTIONRATE)
                        #frame[linkID]['friction'] = inst.simulation_model.getlinkvalue(index, en.FRICTION)


                except Exception as e:
                    logger = unexefiware.base_logger.BaseLogger()
                    logger.exception(inspect.currentframe(), e)

        print()

        if key == 'x':
            quitApp = True

def testbed():
    quitApp = False

    logger = unexefiware.base_logger.BaseLogger()

    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    fiware_wrapper.init(logger=logger)

    fiware_service = 'AAA'

    #here are the simulation models, these will go into another server (I think)
    #sim_lookup['AAA'].
    if len(sim_lookup) == 0:
        sim_lookup['AAA'] = load_sim_data('AAA')
        sim_lookup['GUW'] = load_sim_data('GUW')

        #sim_lookup['GUW'].simulation_model.set_hyd_step(100)

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + fiware_service)


        print('\n')
        print('1..Webdav Management')
        print('2..Device Management')
        print('3..Simulation Management')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            testbed_webdav(fiware_wrapper, fiware_service, logger)

        if key == '2':
            testbed_device(fiware_wrapper, fiware_service, logger)

        if key == '3':
            testbed_sim_management(fiware_wrapper, fiware_service, logger)

        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    testbed()
