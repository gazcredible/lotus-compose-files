import copy
import inspect

import sim.epasim
import sim.epanet_model
import random
import json
import unexefiware.fiwarewrapper
import epanet.toolkit as en
import epanet_fiware.ngsi_ld_writer
import pyproj


class epasim_fiware(sim.epanet_model.epanet_model):
    def __init__(self):
        super().__init__()

    def init(self, epanet_file:str, coord_system:pyproj.CRS, fiware_service:str, flip_coordindates:bool=False):

        self.flip_coordinates = flip_coordindates
        self.coord_system = coord_system
        self.transformer = pyproj.Transformer.from_crs(self.coord_system, pyproj.CRS.from_epsg(4326))

        super().init(epanet_file)
        self.simulation_model = sim.epasim.EPASim()
        self.simulation_model.init(epanet_file)

        self.epanetmodel = epanet_fiware.epanetmodel.EPAnetModel('sim network', epanet_file)

        self.device_index = 1

    def update_entities(self, fiware_wrapper:unexefiware.fiwarewrapper.fiwareWrapper, fiware_service:str, fiware_time:str):
        """
            get the current data from orion and see when the last update was
        """

        if self.simulation_model.elapsed_time_in_sec == 0:
            print('no model!')
        else:
            if self.simulation_model.time_for_step(fiware_time):
                while self.simulation_model.time_for_step(fiware_time):
                    print('do a step')
                    sim_fiware_time = self.simulation_model.do_a_step()

                    devices = fiware_wrapper.get_entities('Device', fiware_service)

                    if devices[0] == 200:
                        for device in devices[1]:
                            epanet_reference = json.loads(device['epanet_reference']['value'])

                            print(str(device['id']) + ' ' + epanet_reference['epanet_id'] + ' ' + epanet_reference['epanet_type'])

                            if epanet_reference['epanet_type'] == 'node':
                                self.update_node(fiware_wrapper, fiware_service, sim_fiware_time, device)

                            if epanet_reference['epanet_type'] == 'pipe':
                                self.update_link(fiware_wrapper, fiware_service, sim_fiware_time, device)
            else:
                print('not time yet')

    def create_entities(self, fiware_wrapper:unexefiware.fiwarewrapper.fiwareWrapper, fiware_service:str, fiware_time:str, sensor_list):
        self.simulation_model.reset()
        sim_fiware_time = self.simulation_model.step_to(fiware_time)

        for sensor in sensor_list:
            if 'Type' in sensor:
                if sensor['Type'] == 'pressure':
                    self.do_node(fiware_wrapper, fiware_service, sensor['ID'], sim_fiware_time)

                if sensor['Type'] == 'flow':
                    self.do_link(fiware_wrapper, fiware_service, sensor['ID'], sim_fiware_time)


    def do_link(self, fiware_wrapper, fiware_service, epanet_id, fiware_time):
        urn = 'urn:ngsi-ld:Pipe:' + epanet_id

        try:
            index = self.simulation_model.getlinkindex(epanet_id)
            link_node_indices = self.simulation_model.getlinknodes(index)

            coords = []
            coords.append(self.simulation_model.getcoord(link_node_indices[0]))

            num_vertices = self.simulation_model.getvertexcount(index)
            if num_vertices:
                for vertex in range(1, num_vertices + 1):
                    coords.append(self.simulation_model.getvertex( index, vertex))

            coords.append(self.simulation_model.getcoord(link_node_indices[1]))

            if len(coords) == 2:
                coords = [coords[0][0] + (coords[1][0] - coords[0][0])/2, coords[0][1] + (coords[1][1] - coords[0][1])/2]
            else:
                vert_index = random.randint(0, len(coords) - 1)
                coords = coords[vert_index]

            if coords and len(coords) == 2:
                coords = list(coords)

                coords = self.transformer.transform(coords[0], coords[1])

                if self.flip_coordinates:
                    coords = [coords[1], coords[0]]

                value = self.simulation_model.getlinkvalue(index, en.FLOW)

                self.add_entity(fiware_wrapper, fiware_service, urn, epanet_id, 'pipe',coords, epanet_id, 'flow', value, 'G51', fiware_time)
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

    def do_node(self, fiware_wrapper, fiware_service, epanet_id, fiware_time):
        urn = 'urn:ngsi-ld:Junction:' + epanet_id

        index = self.simulation_model.getnodeindex(epanet_id)
        coords = self.simulation_model.getcoord(index)

        if coords and len(coords) == 2:
            coords = list(coords)

            coords = self.transformer.transform(coords[0], coords[1])

            if self.flip_coordinates:
                coords = [coords[1], coords[0]]

            value = self.simulation_model.getnodevalue(index, en.PRESSURE)

            self.add_entity(fiware_wrapper, fiware_service, urn, epanet_id, 'node', coords, epanet_id, 'pressure', value,'N23', fiware_time)
        else:
            print('coords error:' + urn)

    def update_node(self, fiware_wrapper, fiware_service, fiware_time, device):

        epanet_reference = json.loads(device['epanet_reference']['value'])
        index = self.simulation_model.getnodeindex(epanet_reference['epanet_id'])

        patch_data = copy.deepcopy(device['pressure'])
        patch_data['observedAt'] = fiware_time
        patch_data['value'] = self.simulation_model.getnodevalue(index, en.PRESSURE)

        #fiware_wrapper.patch_entity(device['id'],{'pressure':patch_data}, fiware_service)

    def update_link(self, fiware_wrapper, fiware_service, fiware_time, device):
        epanet_reference = json.loads(device['epanet_reference']['value'])
        index = self.simulation_model.getlinkindex(epanet_reference['epanet_id'])

        patch_data = copy.deepcopy(device['flow'])
        patch_data['observedAt'] = fiware_time
        patch_data['value'] = self.simulation_model.getnodevalue(index, en.FLOW)

        #fiware_wrapper.patch_entity(device['id'], {'flow': patch_data}, fiware_service)

    def add_entity(self, fiware_wrapper, fiware_service, urn, epanet_id, epanet_type, coords, name, prop_type,value, unitcode, fiware_time):
        short_name = name + '-' + epanet_type
        device_record = self.create_device_model(device_index=self.device_index, sensor_name=short_name, name=name, property=prop_type, location=coords, unitcode=unitcode, fiware_time=fiware_time,value=value)
        device_record['id'] = self.get_deviceid_from_definition(short_name)
        device_record['location']['value']['coordinates'] = [round(coords[0],5),round(coords[1],5)]
        device_record['epanet_reference']['value'] = json.dumps({'urn': urn, 'epanet_id': epanet_id, 'epanet_type': epanet_type})
        fiware_wrapper.create_instance(entity_json=device_record, service=fiware_service, link=device_record['@context'])

        self.device_index += 1

    def create_device(self, index):
        record = {}

        record['type'] = 'Device'
        record['@context'] = 'https://schema.lab.fiware.org/ld/context'
        record['id'] = "urn:ngsi-ld:" + record['type'] + ':' + str(index)
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

    def create_property_status(self, fiware_time, property_name, value, unitCode):
        record = {}

        record[property_name] = {}
        record[property_name]['type'] = 'Property'
        record[property_name]['value'] = str(round(value, 2))
        record[property_name]['observedAt'] = fiware_time
        record[property_name]['unitCode'] = unitCode

        return record

    def get_deviceid_from_definition(self, sensor_name):
        return ("urn:ngsi-ld:" + 'Device' + ':' + sensor_name).replace(' ', '-')

    def generate_property_ngsildv1(self, baseline: dict, prop: str, fiware_time: str, value: float = 0):
        record = {}

        record[prop] = {}
        record[prop]['type'] = 'Property'
        record[prop]['value'] = '##.##'
        record[prop]['observedAt'] = fiware_time
        record[prop]['unitCode'] = baseline['unitCode']

        record[prop]['value'] = str(round(value, 3))

        return record

    def create_device_model(self, device_index, sensor_name, name, property, location, unitcode, fiware_time, value):

        device_record = self.create_device(device_index)

        device_record['name']['value'] = name
        device_record['location']['value']['coordinates'] = [location[1], location[0]]
        device_record['controlledProperty']['value'] = property

        # gareth - hmmmm 0 is not a good starting value as it messes things up ;)

        prop_staus = self.create_property_status(fiware_time, property, value, unitcode)
        device_record[property] = prop_staus[property]

        patch_data = self.generate_property_ngsildv1(device_record[property], property, fiware_time,value)

        device_record[property] = patch_data[property]

        return device_record






