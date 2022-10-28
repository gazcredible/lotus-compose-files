import os
import random

import support
import unexefiware.fiwarewrapper
import unexeaqua3s.deviceinfo

import datetime
import math
import random

import sim.epanet_model
import sim.epasim_fiware

raw_device_info = [
    # 3-lotus, 4-pressure,5-flow

    [1, 'Reservoir Outlet', [26.1694684, 91.6899477], 'Y', 'Y', 'Y', {'junction': 'GJ533'}],
    [2, '1.1', [26.1663876, 91.6872343], 'Y', 'Y', 'Y', {'junction': 'GJ519'}],
    [3, '1.2', [26.1619912, 91.7011538], 'Y', 'Y', 'O', {'junction': 'GJ409'}],
    [4, '1.3', [26.1641121, 91.6975702], 'Y', 'Y', 'O', {'junction': 'GJ414'}],
    [5, '1.4', [26.1653476, 91.6911213], 'Y', 'Y', 'O', {'junction': 'GJ531'}],
    [6, '1.5', [26.1653418, 91.692331], 'Y', 'Y', 'O', {'junction': 'GJ498'}],
    [7, '1.6', [26.1648991, 91.7153255], 'Y', 'Y', 'O', {'junction': 'GJ452'}],
    [8, '1.7', [26.168017, 91.6902627], 'Y', 'Y', 'O', {'junction': 'GJ513'}],
    [9, '1.8', [26.1586467, 91.6934328], 'Y', 'Y', 'O', {'junction': 'GJ457'}],
    [10, '2.1', [26.1604852, 91.6820665], 'Y', 'Y', 'O', {'junction': 'GJ350'}],
    [11, '2.2', [26.1604852, 91.6820665], 'Y', 'Y', 'O', {'junction': 'GJ316'}],
    [12, '2.3', [26.1588261, 91.6841764], 'Y', 'Y', 'Y', {'junction': 'GJ379'}],
    [13, '2.4', [26.1593926, 91.6862521], 'Y', 'Y', 'O', {'junction': 'GJ348'}],
    [14, '2.5', [26.1603742, 91.6848933], 'Y', 'Y', 'O', {'junction': 'GJ329'}],
    [15, '3.1', [26.1587947, 91.6880288], 'Y', 'Y', 'Y', {'junction': 'GJ394'}],
    [16, '3.2', [26.1584781, 91.6871471], 'Y', 'Y', 'O', {'junction': 'GJ382'}],
    [17, '4.1', [26.1622775, 91.679676], 'Y', 'Y', 'O', {'junction': 'GJ151'}],
    [18, '4.2', [26.1622775, 91.679676], 'Y', 'Y', 'O', {'junction': 'GJ104'}],
    [19, '4.3', [26.1614796, 91.6774528], 'Y', 'Y', 'O', {'junction': '5'}],
    [20, '4.4', [26.1582508, 91.6779762], 'Y', 'Y', 'Y', {'junction': 'GJ327'}],

    [1, '1A', [26.1637427, 91.691368], 'N', 'Y', 'Y', {'pipe': 'GP256'}],
    [2, '1B', [26.16208, 91.6950582], 'N', 'Y', 'Y', {'pipe': 'GP249'}],
    [3, '1C', [26.1600834, 91.6952671], 'N', 'Y', 'Y', {'pipe': 'GP464'}],
    [4, '1D', [26.1596827, 91.7011849], 'N', 'Y', 'Y', {'pipe': 'GP532'}],
    [5, '1E', [26.1667538, 91.7194524], 'N', 'Y', 'Y', {'pipe': 'GP239'}],
    [6, '2A', [26.159004, 91.6849541], 'N', 'Y', 'Y', {'pipe': 'GP465'}],
    [7, '2B', [26.1589227, 91.6882977], 'N', 'Y', 'Y', {'pipe': 'GP280'}],
    [8, '2C', [26.1608241, 91.6845924], 'N', 'Y', 'Y', {'pipe': 'GP145'}],
    [9, '3A', [26.1579675, 91.6858475], 'N', 'Y', 'Y', {'pipe': 'GP272'}],
    [10, '4A', [26.1629768, 91.6777687], 'N', 'Y', 'Y', {'pipe': 'GP331'}],
    [11, '4B', [26.163769, 91.6784903], 'N', 'Y', 'Y', {'pipe': 'GP323'}],
    [12, '4C', [26.1627777, 91.6792041], 'N', 'Y', 'Y', {'pipe': 'GP308'}],
]
guw_sensors = [
    {'ID': 'GJ533', 'Type': 'pressure'},
    {'ID': 'GJ519', 'Type': 'pressure'},
    {'ID': 'GJ409', 'Type': 'pressure'},
    {'ID': 'GJ414', 'Type': 'pressure'},
    {'ID': 'GJ531', 'Type': 'pressure'},
    {'ID': 'GJ498', 'Type': 'pressure'},
    {'ID': 'GJ452', 'Type': 'pressure'},
    {'ID': 'GJ513', 'Type': 'pressure'},
    {'ID': 'GJ457', 'Type': 'pressure'},
    {'ID': 'GJ350', 'Type': 'pressure'},
    {'ID': 'GJ316', 'Type': 'pressure'},
    {'ID': 'GJ379', 'Type': 'pressure'},
    {'ID': 'GJ348', 'Type': 'pressure'},
    {'ID': 'GJ329', 'Type': 'pressure'},
    {'ID': 'GJ394', 'Type': 'pressure'},
    {'ID': 'GJ382', 'Type': 'pressure'},
    {'ID': 'GJ151', 'Type': 'pressure'},
    {'ID': 'GJ104', 'Type': 'pressure'},
    {'ID': '5', 'Type': 'pressure'},
    {'ID': 'GJ327', 'Type': 'pressure'},

    {'ID': 'GP256', 'Type': 'flow'},
    {'ID': 'GP249', 'Type': 'flow'},
    {'ID': 'GP464', 'Type': 'flow'},
    {'ID': 'GP532', 'Type': 'flow'},
    {'ID': 'GP239', 'Type': 'flow'},
    {'ID': 'GP465', 'Type': 'flow'},
    {'ID': 'GP280', 'Type': 'flow'},
    {'ID': 'GP145', 'Type': 'flow'},
    {'ID': 'GP272', 'Type': 'flow'},
    {'ID': 'GP331', 'Type': 'flow'},
    {'ID': 'GP323', 'Type': 'flow'},
    {'ID': 'GP308', 'Type': 'flow'},
]


def create_device(index):
    record = {}

    record['type'] = 'Device'
    record['@context'] = 'https://schema.lab.fiware.org/ld/context'
    record['id'] = "urn:ngsi-ld:" + record['type'] + ': ' + str(index)
    record['id'] = record['id'].replace(' ', '-')

    record['name'] = {}
    record['name']['type'] = 'Property'
    record['name']['value'] = 'TBD'

    record['location'] = {}
    record['location']['type'] = 'GeoProperty'
    record['location']['value'] = {}
    record['location']['value']['coordinates'] = 'TBD'
    record['location']['value']['type'] = 'Point'

    record['deviceState'] = {}
    record['deviceState']['type'] = 'Property'

    record['deviceState']['value'] = 'Green'

    record['controlledProperty'] = {}
    record['controlledProperty']['type'] = 'Property'

    record['controlledProperty']['value'] = 'TBD'

    record['epanet_reference'] = {}
    record['epanet_reference']['type'] = 'Property'
    record['epanet_reference']['value'] = json.dumps({})

    return record


def create_property_status(fiware_time, property_name, value, unitCode):
    record = {}

    record[property_name] = {}
    record[property_name]['type'] = 'Property'
    record[property_name]['value'] = str(round(value, 2))
    record[property_name]['observedAt'] = fiware_time
    record[property_name]['unitCode'] = unitCode

    return record


def get_deviceid_from_definition(sensor_name):
    return ("urn:ngsi-ld:" + 'Device' + ': ' + sensor_name).replace(' ', '-')


def generate_property_ngsildv1(baseline, prop, fiware_time, simulation_settings=None):
    record = {}

    record[prop] = {}
    record[prop]['type'] = 'Property'
    record[prop]['value'] = '##.##'
    record[prop]['observedAt'] = fiware_time
    record[prop]['unitCode'] = baseline['unitCode']

    # get the range from alert_settings
    # use that to build the alert triggers & anomalies?

    value = 0

    if simulation_settings:
        id_range = float(simulation_settings['sim_step'])

        date = unexefiware.time.time_to_datetime(unexefiware.time.fiware_to_time(fiware_time))

        minutes = int(date.strftime('%w')) * 24 * 60
        minutes += int((date.hour) * 60)
        minutes += int(date.minute)
        # normalise to 7days * 24hr * 60min

        minutes += id_range * 3 * 24 * 60

        period = minutes / (7 * 24 * 60)

        full_range = (float(simulation_settings['max']) - float(simulation_settings['min']))

        range = (full_range / 2) * id_range

        value = float(simulation_settings['min']) + (full_range / 2)
        value += (range * math.sin(6.28 * period))

        if simulation_settings['prop_state'] == unexeaqua3s.sim_pilot.controlled_by_scenario_out_of_range_low:
            value -= full_range * 2

        if simulation_settings['prop_state'] == unexeaqua3s.sim_pilot.controlled_by_scenario_out_of_range_high:
            value += full_range * 2

        if simulation_settings['prop_state'] == unexeaqua3s.sim_pilot.controlled_by_scenario_in_anomaly_low:
            value -= full_range * 1

        if simulation_settings['prop_state'] == unexeaqua3s.sim_pilot.controlled_by_scenario_in_anomaly_high:
            value += full_range * 1

        # this is normal behaviour
        if simulation_settings['prop_state'] == unexeaqua3s.sim_pilot.controlled_by_scenario:
            pass

        record[prop]['value'] = str(round(value, 3))
    else:
        record[prop]['value'] = str(round(0, 3))

    return record


def create_device_from_lotus_data(device_index, sensor_name, name, property, location, unitcode, fiware_time):
    device_record = create_device(device_index)

    device_record['name']['value'] = name
    device_record['location']['value']['coordinates'] = [location[1], location[0]]
    device_record['controlledProperty']['value'] = property

    # gareth - hmmmm 0 is not a good starting value as it messes things up ;)

    prop_staus = create_property_status(fiware_time, property, 0, unitcode)
    device_record[property] = prop_staus[property]

    # gareth -   update the property here to stop everything getting messed up
    #           by everything, I mean the charting and anomaly settings
    patch_data = generate_property_ngsildv1(device_record[property], property, fiware_time)

    device_record[property] = patch_data[property]

    return device_record


import requests
import json
import pyproj
import epanet_fiware.waternetwork


def update_visualiser(fiware_service):
    headers = {}
    headers['Content-Type'] = 'application/ld+json'
    headers['fiware-service'] = fiware_service
    session = requests.session()

    path = os.environ['VISUALISER'] + '/pilot_device_update'
    payload = {}

    try:
        r = session.post(path, data=json.dumps(payload), headers=headers, timeout=10)
    except Exception as e:
        print(str(e))


class EPANETDeviceBuilder:

    def __init__(self):
        self.water_network = None
        self.device_index = 0
        self.fiware_time = ''

    def do_pipe(self, fiware_wrapper, fiware_service, epanet_id):
        urn = 'urn:ngsi-ld:Pipe: ' + epanet_id

        try:
            index = self.water_network.reverse_lookups['Pipe'][urn]
            pipe = self.water_network.fiware_component['Pipe'][index]
            if 'location' in pipe:
                coords = self.water_network.get_coordinates_from_id(urn)

            if 'startsAt' in pipe:
                start = self.water_network.get_coordinates_from_id(pipe['startsAt']['object'])
                end = self.water_network.get_coordinates_from_id(pipe['endsAt']['object'])

                coords = [0, 0]
                coords[0] = start[0] + (end[0] - start[0]) / 2
                coords[1] = start[1] + (end[1] - start[1]) / 2

            if 'vertices' in pipe:

                if not isinstance(pipe['vertices']['value']['coordinates'][0], float):
                    vert_index = random.randint(0, len(pipe['vertices']['value']['coordinates']) - 1)
                    coords = pipe['vertices']['value']['coordinates'][vert_index]
                else:
                    coords = pipe['vertices']['value']['coordinates']

            if coords and len(coords) == 2:
                coords = list(coords)
                coords = [coords[1], coords[0]]

                self.add_entity(fiware_wrapper, fiware_service, urn, epanet_id, 'pipe', coords, epanet_id, 'flow')
        except Exception as e:
            pass

    def add_entity(self, fiware_wrapper, fiware_service, urn, epanet_id, epanet_type, coords, name, prop_type):
        short_name = name + '-' + epanet_type
        device_record = self.create_device_model(device_index=self.device_index, sensor_name=short_name, name=name, property=prop_type, location=coords, unitcode='n/a', fiware_time=self.fiware_time)
        device_record['id'] = get_deviceid_from_definition(short_name)
        device_record['location']['value']['coordinates'] = [round(coords[0], 5), round(coords[1], 5)]
        device_record['epanet_reference']['value'] = json.dumps({'urn': urn, 'epanet_id': epanet_id, 'epanet_type': epanet_type})
        fiware_wrapper.create_instance(entity_json=device_record, service=fiware_service, link=device_record['@context'])

        self.device_index += 1

    def do_node(self, fiware_wrapper, fiware_service, epanet_id):
        urn = 'urn:ngsi-ld:Junction: ' + epanet_id
        coords = self.water_network.get_coordinates_from_id(urn)

        if coords and len(coords) == 2:
            coords = list(coords)
            coords = [coords[1], coords[0]]

            self.add_entity(fiware_wrapper, fiware_service, urn, epanet_id, 'node', coords, epanet_id, 'pressure')
        else:
            print('coords error: ' + urn)
            coords = self.water_network.get_coordinates_from_id(urn)

    def create_device_model(self, device_index, sensor_name, name, property, location, unitcode, fiware_time):

        device_record = create_device(device_index)

        device_record['name']['value'] = name
        device_record['location']['value']['coordinates'] = [location[1], location[0]]
        device_record['controlledProperty']['value'] = property

        # gareth - hmmmm 0 is not a good starting value as it messes things up ;)

        prop_staus = create_property_status(fiware_time, property, 0, unitcode)
        device_record[property] = prop_staus[property]

        # gareth -   update the property here to stop everything getting messed up
        #           by everything, I mean the charting and anomaly settings
        patch_data = generate_property_ngsildv1(device_record[property], property, fiware_time)

        device_record[property] = patch_data[property]

        return device_record


def create_fiware_AAA():
    fiware_service = 'AAA'

    epasim_fiware_model = sim.epasim_fiware.epasim_fiware()

    inp_file = '/docker/lotus-visualiser/visualiser/data/' + fiware_service + '/waternetwork/epanet.inp'

    coord_system = pyproj.CRS.from_epsg(32632)

    epasim_fiware_model.init(epanet_file=inp_file, coord_system=coord_system, fiware_service=fiware_service, flip_coordindates=True)

    sensors = epasim_fiware_model.get_sensors()
    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.now())

    epasim_fiware_model.create_entities(fiware_wrapper, fiware_service, fiware_time, sensors)


sim_lookup = {}


def load_sim_data(fiware_service):
    epasim_fiware_model = sim.epasim_fiware.epasim_fiware()

    inp_file = os.environ['FILE_PATH'] + os.sep + os.environ['FILE_VISUALISER_FOLDER'] + os.sep + 'data' + os.sep + fiware_service + os.sep + 'waternetwork' + os.sep + 'epanet.inp'

    coord_system = pyproj.CRS.from_epsg(32632)

    if fiware_service == 'GUW':
        coord_system = pyproj.CRS.from_epsg(32646)

    epasim_fiware_model.init(epanet_file=inp_file, coord_system=coord_system, fiware_service=fiware_service, flip_coordindates=True)

    return epasim_fiware_model


def testbed(fiware_service):
    quitApp = False
    pilot_list = []

    fiware_service = 'GUW'

    if len(sim_lookup) == 0:
        sim_lookup['AAA'] = load_sim_data('AAA')
        sim_lookup['GUW'] = load_sim_data('GUW')

    pilots = os.environ['PILOTS'].split(',')
    for pilot in pilots:
        pilot_list.append(pilot.replace(' ', ''))

    while quitApp is False:
        print('aqua3s: ' + os.environ['USERLAYER_BROKER'] + '\n')

        print()
        print('1..View Devices: ' + fiware_service)
        print('2..Delete Devices: ' + fiware_service)
        print('3..Create Devices: ' + fiware_service)
        print('4..Update Visualiser: ' + os.environ['VISUALISER'])

        print('5..Load anomaly data')
        print('55..Create Smart Devices from epanet')

        print('6..Update pilot: ' + fiware_service)

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])

            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper)
            deviceInfo.run()

            support.print_devices(deviceInfo)

        if key == '2':
            # delete devices
            support.delete_type_from_broker(os.environ['DEVICE_BROKER'], fiware_service, ['Device'])

        if key == '3':
            # create devices
            if False:
                if fiware_service == 'GUW':

                    epanet_model = sim.epanet_model.epanet_model()

                    inp_file = '/docker/lotus-visualiser/visualiser/data/' + fiware_service + '/waternetwork/epanet.inp'

                    coord_system = pyproj.CRS.from_epsg(32646)

                    # GARETH? epanet_model.init(inp_file = inp_file, coord_system = coord_system, fiware_service=fiware_service, flip_coordindates=True)
                    epanet_model.init(inp_file=inp_file)

                    sensor_list = []
                    leak_list = []

                    for entry in raw_device_info:
                        if 'junction' in entry[6]:
                            sensor_list.append({'ID': entry[6]['junction'], 'Type': 'pressure'})

                            # leak_list.append(entry[6]['junction'])

                        if 'pipe' in entry[6]:
                            sensor_list.append({'ID': entry[6]['pipe'], 'Type': 'flow'})

                    epanet_model.build_anomaly_data(sensors=sensor_list, leak_node_ids=leak_list)
                    epanet_model.save_anomaly_data('/docker/lotus-visualiser/visualiser/data/' + fiware_service + '/epanet_anomaly/')

                    epanet_model.graph()

                    # epanet_model.create_devices()

                    return
                    device_index = 1

                    now = datetime.datetime.utcnow()
                    start = now
                    start = start.replace(hour=0, minute=0, second=0, microsecond=0)

                    # create initial data
                    fiware_time = unexefiware.time.datetime_to_fiware(start)

                    # load epanet model & convert to wgs84
                    inp_file = '/docker/lotus-visualiser/visualiser/data/' + fiware_service + '/waternetwork/epanet.inp'

                    coord_system = pyproj.CRS.from_epsg(32646)
                    flip_coordindates = True

                    water_network = epanet_fiware.waternetwork.WaterNetwork()
                    water_network.load_epanet(inp_file, coord_system)

                    for entry in raw_device_info:
                        print(entry[1])

                        coords = None
                        urn = None
                        epanet_id = None
                        epanet_type = None

                        if len(entry) > 5:

                            if 'pipe' in entry[6]:
                                epanet_type = 'pipe'
                                epanet_id = entry[6]['pipe']
                                urn = 'urn:ngsi-ld:Pipe: ' + epanet_id

                                if epanet_id == 'GP256':
                                    print()

                                index = water_network.reverse_lookups['Pipe'][urn]
                                pipe = water_network.fiware_component['Pipe'][index]
                                if 'location' in pipe:
                                    coords = water_network.get_coordinates_from_id(urn)

                                if 'startsAt' in pipe:
                                    start = water_network.get_coordinates_from_id(pipe['startsAt']['object'])
                                    end = water_network.get_coordinates_from_id(pipe['endsAt']['object'])

                                    coords = [0, 0]
                                    coords[0] = start[0] + (end[0] - start[0]) / 2
                                    coords[1] = start[1] + (end[1] - start[1]) / 2

                                if 'vertices' in pipe:

                                    if not isinstance(pipe['vertices']['value']['coordinates'][0], float):
                                        vert_index = random.randint(0, len(pipe['vertices']['value']['coordinates']) - 1)
                                        coords = pipe['vertices']['value']['coordinates'][vert_index]
                                    else:
                                        coords = pipe['vertices']['value']['coordinates']

                            if 'junction' in entry[6]:
                                epanet_type = 'junction'
                                epanet_id = entry[6]['junction']
                                urn = 'urn:ngsi-ld:Junction: ' + epanet_id
                                coords = water_network.get_coordinates_from_id(urn)

                            if not coords or len(coords) != 2:
                                print('error')

                            coords = list(coords)

                            coords = [coords[1], coords[0]]

                            print(epanet_id + ' ' + str(coords))

                        if entry[3] == 'Y':  # lotus sensor
                            device_record = create_device_from_lotus_data(device_index=device_index, sensor_name=entry[1] + '-lotus', name=entry[1], property='lotus', location=entry[2], unitcode='n/a', fiware_time=fiware_time)
                            device_record['id'] = get_deviceid_from_definition(entry[1] + '-lotus')
                            device_record['location']['value']['coordinates'] = coords
                            device_record['epanet_reference']['value'] = json.dumps({'urn': urn, 'epanet_id': epanet_id, 'epanet_type': epanet_type})
                            fiware_wrapper.create_instance(entity_json=device_record, service=fiware_service, link=device_record['@context'])

                            device_index += 1

                        if entry[4] == 'Y':  # pressure sensor
                            device_record = create_device_from_lotus_data(device_index=device_index, sensor_name=entry[1] + '-pressure', name=entry[1], property='pressure', location=entry[2], unitcode='N23', fiware_time=fiware_time)
                            device_record['id'] = get_deviceid_from_definition(entry[1] + '-pressure')
                            device_record['location']['value']['coordinates'] = coords
                            device_record['epanet_reference']['value'] = json.dumps({'urn': urn, 'epanet_id': epanet_id, 'epanet_type': epanet_type})

                            fiware_wrapper.create_instance(entity_json=device_record, service=fiware_service, link=device_record['@context'])

                            device_index += 1

                        if entry[5] == 'Y':  # flow sensor
                            device_record = create_device_from_lotus_data(device_index=device_index, sensor_name=entry[1] + '-flow', name=entry[1], property='flow', location=entry[2], unitcode='G51', fiware_time=fiware_time)
                            device_record['id'] = get_deviceid_from_definition(entry[1] + '-flow')
                            device_record['location']['value']['coordinates'] = coords
                            device_record['epanet_reference']['value'] = json.dumps({'urn': urn, 'epanet_id': epanet_id, 'epanet_type': epanet_type})

                            fiware_wrapper.create_instance(entity_json=device_record, service=fiware_service, link=device_record['@context'])

                            device_index += 1

            if fiware_service == 'AAA':
                sensors = sim_lookup[fiware_service].get_sensors()
                fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
                fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.now())

                sim_lookup[fiware_service].create_entities(fiware_wrapper, fiware_service, fiware_time, sensors)

            if fiware_service == 'GUW':
                sensors = guw_sensors
                fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
                fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.now())

                sim_lookup[fiware_service].create_entities(fiware_wrapper, fiware_service, fiware_time, sensors)


            update_visualiser(fiware_service)

        if key == '4':
            update_visualiser(fiware_service)

        if key == '55':

            # do GUW
            epanet_model = sim.epanet_model.epanet_model()

            service = 'GUW'
            support.delete_type_from_broker(os.environ['DEVICE_BROKER'], fiware_service, ['Device'])

            inp_file = '/docker/lotus-visualiser/visualiser/data/' + service + '/waternetwork/epanet.inp'

            coord_system = pyproj.CRS.from_epsg(32646)

            # GARETH? epanet_model.init(inp_file=inp_file, coord_system=coord_system, fiware_service=service, flip_coordindates=True)
            epanet_model.init(inp_file=inp_file)

            sensor_list = []
            leak_list = []

            for entry in raw_device_info:
                if 'junction' in entry[6]:
                    sensor_list.append({'ID': entry[6]['junction'], 'Type': 'pressure', 'Name': entry[1]})

                    # leak_list.append(entry[6]['junction'])

                if 'pipe' in entry[6]:
                    sensor_list.append({'ID': entry[6]['pipe'], 'Type': 'flow', 'Name': entry[1]})

            start = datetime.datetime.now()

            fiware_time = unexefiware.time.datetime_to_fiware(start)
            epanet_model.build_device_smart_models(fiware_time, sensor_list)
            update_visualiser(fiware_service)

        if key == '6':
            fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            sim_lookup[fiware_service].update_entities(fiware_wrapper, fiware_service, unexefiware.time.datetime_to_fiware(datetime.datetime.now()))

        if key == 'x':
            quitApp = True
