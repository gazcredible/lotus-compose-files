import copy
import datetime
import inspect

import unexe_epanet.epanet_model
import random
import json
import unexefiware.fiwarewrapper
import unexefiware.time
import epanet.toolkit as en
import epanet_fiware.ngsi_ld_writer
import pyproj
import unexewrapper
import os


class epanet_fiware(unexe_epanet.epanet_model.epanet_model):
    def __init__(self):
        super().__init__()

        self.fiware_service = ''
        self.value_dp = 3

        self.link_property_lookups = {}
        self.link_property_lookups['flow'] = {'label': en.FLOW, 'unitcode': 'G51'}
        #reduce properties to speed up simulation
        #self.link_property_lookups['velocity'] = {'label': en.VELOCITY, 'unitcode':  'XXX'}
        #self.link_property_lookups['headloss'] = {'label': en.HEADLOSS, 'unitcode':  'XXX'}
        #self.link_property_lookups['quality'] = {'label': en.QUALITY, 'unitcode':  'XXX'}
        #self.link_property_lookups['status'] = {'label': en.STATUS, 'unitcode':  'XXX'}
        #self.link_property_lookups['setting'] = {'label':en.SETTING, 'unitcode':  'XXX'}

        self.node_property_lookups = {}
        #self.node_property_lookups['head'] = {'label': en.HEAD, 'unitcode': 'XXX'}
        self.node_property_lookups['pressure'] = {'label': en.PRESSURE, 'unitcode':  'N23'}
        #self.node_property_lookups['quality'] = {'label':  en.QUALITY, 'unitcode':  'XXX'}

    def init(self, epanet_file:str, coord_system:pyproj.CRS, fiware_service:str, flip_coordindates:bool=False):

        self.flip_coordinates = flip_coordindates
        self.coord_system = coord_system
        self.transformer = pyproj.Transformer.from_crs(self.coord_system, pyproj.CRS.from_epsg(4326))

        super().init(epanet_file)

        self.device_index = 1

    def do_link(self, fiware_wrapper, epanet_id, fiware_time):

        try:
            index = self.getlinkindex(epanet_id)
            link_node_indices = self.getlinknodes(index)

            coords = []
            coords.append(self.getcoord(link_node_indices[0]))

            num_vertices = self.getvertexcount(index)
            if num_vertices:
                for vertex in range(1, num_vertices + 1):
                    coords.append(self.getvertex( index, vertex))

            coords.append(self.getcoord(link_node_indices[1]))

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

                device = self.create_device()
                device['id'] = self.fiware_legal_name('urn:ngsi-ld:Device:' + epanet_id)
                device['name']['value'] = epanet_id

                for link_label in self.link_property_lookups:
                    link_info = self.link_property_lookups[link_label]
                    self.device_add_property(device, link_label, self.getlinkvalue(index, link_info['label']), link_info['unitcode'], fiware_time)

                device['location']['value']['coordinates'] = [round(coords[0], 5), round(coords[1], 5)]
                device['epanet_reference']['value'] = json.dumps({'urn': device['id'], 'epanet_id': epanet_id, 'epanet_type': 'link'})
                fiware_wrapper.create_instance(entity_json=device, service=self.fiware_service, link=device['@context'])

        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

    def do_node(self, fiware_wrapper, epanet_id, fiware_time):

        try:
            index = self.getnodeindex(epanet_id)
            coords = self.getcoord(index)

            if coords and len(coords) == 2:
                coords = list(coords)

                coords = self.transformer.transform(coords[0], coords[1])

                if self.flip_coordinates:
                    coords = [coords[1], coords[0]]

                device = self.create_device()
                device['id'] = self.fiware_legal_name('urn:ngsi-ld:Device:' + epanet_id)
                device['name']['value'] = epanet_id

                for node_label in self.node_property_lookups:
                    node_info = self.node_property_lookups[node_label]
                    self.device_add_property(device, node_label, self.getnodevalue(index, node_info['label']), node_info['unitcode'], fiware_time)

                device['location']['value']['coordinates'] = [round(coords[0], 5), round(coords[1], 5)]
                device['epanet_reference']['value'] = json.dumps({'urn': device['id'], 'epanet_id': epanet_id, 'epanet_type': 'node'})
                fiware_wrapper.create_instance(entity_json=device, service=self.fiware_service, link=device['@context'])

        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

    def fiware_legal_name(self, name):
        return name.replace(' ', '-')

    def on_patch_entity(self, fiware_service:str, entity_id:str):
        pass

    def device_add_property(self, device, property_label, property_value, property_unitcode, fiware_time):

        if isinstance(device['controlledProperty']['value'], str):
            if len(device['controlledProperty']['value']) == 0:
                device['controlledProperty']['value'] = property_label
            else:
                existing_prop = device['controlledProperty']['value']
                device['controlledProperty']['value'] = []
                device['controlledProperty']['value'].append(existing_prop)
                device['controlledProperty']['value'].append(property_label)
        else:
            device['controlledProperty']['value'].append(property_label)

        if property_label not in device:
            device[property_label] = {}

        device[property_label]['type'] = 'Property'
        device[property_label]['value'] = str(round(property_value, self.value_dp))
        device[property_label]['observedAt'] = fiware_time
        device[property_label]['unitCode'] = property_unitcode

    def create_device(self):
        record = {}

        record['type'] = 'Device'
        record['@context'] = 'https://schema.lab.fiware.org/ld/context'
        record['id'] = ''

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

        record['controlledProperty']['value'] = ''

        record['epanet_reference'] = {}
        record['epanet_reference']['type'] = 'Property'
        record['epanet_reference']['value'] = json.dumps({})

        return record

    def get_deviceid_from_definition(self, sensor_name):
        return ("urn:ngsi-ld:" + 'Device' + ':' + sensor_name).replace(' ', '-')

    def reset(self, sensor_list:list=None, start_datetime:datetime.datetime=None):
        super().reset(start_datetime)

        self.delete()

        try:
            if self.epanetmodel:
                if self.epanetmodel is not None:

                    self.elapsed_time_in_sec = self.next_time_step_in_sec

                    en.runH(self.epanetmodel.proj_for_simulation)
                    t = en.nextH(self.epanetmodel.proj_for_simulation)

                    self.post(sensor_list)

                    self.next_time_step_in_sec += t

                    dur = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.DURATION)
                    en.settimeparam(self.epanetmodel.proj_for_simulation, en.DURATION, dur + t)

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

    def step(self):
        try:
            if self.epanetmodel:
                if self.epanetmodel is not None:

                    self.elapsed_time_in_sec = self.next_time_step_in_sec

                    en.runH(self.epanetmodel.proj_for_simulation)
                    t = en.nextH(self.epanetmodel.proj_for_simulation)

                    self.patch()

                    self.next_time_step_in_sec += t

                    dur = en.gettimeparam(self.epanetmodel.proj_for_simulation, en.DURATION)
                    en.settimeparam(self.epanetmodel.proj_for_simulation, en.DURATION, dur + t)

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

    def delete(self):
        try:
            # delete FIWARE components for devices
            fiware_wrapper = unexewrapper.unexewrapper(url = os.environ['DEVICE_BROKER'])
            fiware_wrapper.delete_type(self.fiware_service, ['Device'])

        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

    def post(self, sensor_list:list=None):
        try:
            #create FIWARE components for devices
            fiware_wrapper = unexewrapper.unexewrapper(url=os.environ['DEVICE_BROKER'])
            sim_fiware_time = unexefiware.time.datetime_to_fiware(self.elapsed_datetime())

            if sensor_list == None or len(sensor_list) == 0:
                sensor_list = self.get_sensors()

            for sensor in sensor_list:
                if 'Type' in sensor:
                    if sensor['Type'] == 'pressure':
                        self.do_node(fiware_wrapper, sensor['ID'], sim_fiware_time)

                    if sensor['Type'] == 'flow':
                        self.do_link(fiware_wrapper, sensor['ID'], sim_fiware_time)

        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

    def patch(self):
        try:
            # update FIWARE components for devices
            fiware_wrapper = unexewrapper.unexewrapper(url=os.environ['DEVICE_BROKER'])
            fiware_time = unexefiware.time.datetime_to_fiware(self.elapsed_datetime())

            devices = fiware_wrapper.get_entities('Device', self.fiware_service)

            if devices[0] == 200:
                for device in devices[1]:
                    epanet_reference = json.loads(device['epanet_reference']['value'])

                    if epanet_reference['epanet_type'] == 'node':
                        try:
                            epanet_reference = json.loads(device['epanet_reference']['value'])
                            index = self.getnodeindex(epanet_reference['epanet_id'])

                            for node_label in self.node_property_lookups:
                                node_info = self.node_property_lookups[node_label]

                                patch_data = copy.deepcopy(device[node_label])
                                patch_data['observedAt'] = fiware_time
                                patch_data['value'] = str(round(self.getnodevalue(index, node_info['label']),self.value_dp))

                                fiware_wrapper.patch_entity(device['id'], {node_label: patch_data}, self.fiware_service)
                                self.on_patch_entity(self.fiware_service,device['id'])
                        except Exception as e:
                            self.logger.exception(inspect.currentframe(), e)

                    if epanet_reference['epanet_type'] == 'link':
                        try:
                            epanet_reference = json.loads(device['epanet_reference']['value'])
                            index = self.getlinkindex(epanet_reference['epanet_id'])

                            for link_label in self.link_property_lookups:
                                link_info = self.link_property_lookups[link_label]

                                patch_data = copy.deepcopy(device[link_label])
                                patch_data['observedAt'] = fiware_time
                                patch_data['value'] = str(round(self.getlinkvalue(index,link_info['label']),self.value_dp))

                                fiware_wrapper.patch_entity(device['id'], {link_label: patch_data}, self.fiware_service)
                                self.on_patch_entity(self.fiware_service, device['id'])
                        except Exception as e:
                            self.logger.exception(inspect.currentframe(), e)

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)