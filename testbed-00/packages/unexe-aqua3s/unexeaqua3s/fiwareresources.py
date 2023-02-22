import unexeaqua3s.resourcebuilder
import os
import pathlib
import inspect
import unexeaqua3s.json
import requests
import unexefiware.ngsildv1

import epanet_fiware.epanet_outfile_handler
import epanet_fiware.waternetwork
import epanet_fiware.epanetmodel
import pyproj


class FiwareResources(unexeaqua3s.resourcebuilder.ResourceBuilder):
    def __init__(self, options=None):
        super().__init__(options)
        self.resources = {}
        self.perform_file_operations = True
        self.remote_root = 'kr_10/data/'
        self.local_root = None
        self.webdav_resources = True

    def init(self, url, file_root, fiware_service_list, types=['WaterNetwork', 'SimulationResult', 'UserLayer']):

        super().init(path_root=file_root, clone_remote=True, delete_local=False, pilot_list=fiware_service_list)

        self.webdav_resources = True

        if self.is_remote_available() == False:
            self.logger.fail(inspect.currentframe(), 'Webdav not available!')
            self.webdav_resources = False

        for fiware_service in self.fiware_service_list:
            self.clone_from_orion(url, fiware_service, types)

    def clone_from_orion(self, url, fiware_service, types):

        session = requests.Session()

        if fiware_service not in self.resources:
            self.resources[fiware_service] = {}

        for model_type in types:
            result = unexefiware.ngsildv1.get_type_count_orionld(session, url, model_type, link=None, fiware_service=fiware_service)

            if result[0] == 200:
                item_count = result[1]['entityCount']
                for i in range(0, item_count):

                    try:
                        # get first entry in the list, rather than ith one as it will move :S
                        result = unexefiware.ngsildv1.get_type_by_index_orionld(session, url, model_type, i, link=None, fiware_service=fiware_service)

                        model = result[1][0]
                        resource_name = model['name']['value']

                        self.logger.log(inspect.currentframe(), 'Loading ' + model['id'] + ' as ' + model_type + ' ' + resource_name)

                        if model_type == 'UserLayer':
                            if 'userlayer' not in self.resources[fiware_service]:
                                self.resources[fiware_service]['userlayer'] = {}

                            self.resources[fiware_service]['userlayer'][resource_name] = {}

                            try:
                                if self.webdav_resources == True:
                                    self.download_file(model['client_file_path']['value'])

                                f = open(self.get_local_filepath(model['client_file_path']['value']), "rb")  # zip file
                                self.resources[fiware_service]['userlayer'][resource_name]['client'] = f.read()
                            except Exception as e:
                                self.logger.fail(inspect.currentframe(), 'Failed to load file: ' + str(e))

                            try:
                                if self.webdav_resources == True:
                                    self.download_file(model['server_file_path']['value'])

                                f = open(self.get_local_filepath(model['server_file_path']['value']), "r")  # json file
                                self.resources[fiware_service]['userlayer'][resource_name]['server'] = unexeaqua3s.json.load(f)
                            except Exception as e:
                                self.logger.fail(inspect.currentframe(), 'Failed to load file: ' + str(e))

                        if model_type == 'WaterNetwork':
                            if 'epanet' not in self.resources[fiware_service]:
                                self.resources[fiware_service]['epanet'] = {}

                            if 'geojson' not in self.resources[fiware_service]:
                                self.resources[fiware_service]['geojson'] = {}

                            try:
                                if self.webdav_resources == True:
                                    self.download_file(model['file_path']['value'])

                                coord_system = pyproj.CRS.from_epsg(4326)
                                flip_coordindates = False

                                if fiware_service == 'AAA' or fiware_service == 'TTT' or fiware_service == 'P2B':  # gareth - this is bad ;) should make this part of the databuild process (I think)
                                    coord_system = pyproj.CRS.from_epsg(32632)
                                    flip_coordindates = True

                                self.resources[fiware_service]['epanet'] = epanet_fiware.waternetwork.WaterNetwork()
                                self.resources[fiware_service]['epanet'].load_epanet(self.get_local_filepath(model['file_path']['value']), coord_system)
                                # self.resources[fiware_service]['epanetmodel'] = epanet_fiware.epanetmodel.EPAnetModel(network_name = fiware_service,
                                #                                                                                filename = self.get_local_filepath(model['file_path']['value']),
                                #                                                                                inp_coordinate_system = coord_system)

                                if self.resources[fiware_service]['epanet'].reverse_lookups:
                                    self.resources[fiware_service]['geojson'] = self.resources[fiware_service]['epanet'].geojsonise(flip_coordinates=flip_coordindates)
                                else:
                                    self.resources[fiware_service]['geojson'] = {}

                            except Exception as e:
                                self.logger.fail(inspect.currentframe(), 'Failed to load file: ' + str(e))

                        if model_type == 'SimulationResult':
                            if 'sim_data' not in self.resources[fiware_service]:
                                self.resources[fiware_service]['sim_data'] = {}

                            try:
                                if self.webdav_resources == True:
                                    self.download_file(model['file_path']['value'])

                                self.resources[fiware_service]['sim_data'] = epanet_fiware.epanet_outfile_handler.EpanetOutFile(self.get_local_filepath(model['file_path']['value']))
                            except Exception as e:
                                self.logger.fail(inspect.currentframe(), 'Failed to load file: ' + str(e))

                    except Exception as e:
                        self.logger.exception(inspect.currentframe(), e)

    def has_userlayers(self, service):
        if service in self.resources:

            if 'userlayer' in self.resources[service]:
                return len(self.resources[service]['userlayer']) > 0

        return False

    def get_userlayer_names(self, service):
        data = []

        if self.has_userlayers(service):

            for resource in self.resources[service]['userlayer']:
                data.append(resource)

            data.sort()

        return data

    def get_zip_data(self, service, path):
        try:
            if 'client' in self.resources[service]['userlayer'][path]:
                return self.resources[service]['userlayer'][path]['client']
        except Exception as e:
            self.log(inspect.currentframe(), str(e))

        return []

    def is_waternetwork_layer(self, service, layer):
        if self.has_waternetwork(service):
            return layer in self.resources[service]['geojson']

        return False

    def has_waternetwork(self, service):
        return 'geojson' in self.resources[service]

    def waternetwork_get_frame_count(self, service):

        if 'sim_data' in self.resources[service] and self.resources[service]['sim_data']:
            return self.resources[service]['sim_data'].reporting_periods()

        return 0

    def get_geojson_for_slipmap(self, service):

        data = []
        if 'geojson' in self.resources[service]:
            src_data = self.resources[service]['geojson']
            for entry in src_data:
                data.append({'name': entry, 'geojson': src_data[entry]['geojson'], 'layer_setup': {'guff': 0}})

        return data

    def debug_view(self, url, fiware_service_list, types=['WaterNetwork', 'SimulationResult', 'UserLayer']):
        self.fiware_service_list = fiware_service_list

        session = requests.Session()

        for service in self.fiware_service_list:
            print(service)
            if service not in self.resources:
                self.resources[service] = {}

            for model_type in types:
                result = unexefiware.ngsildv1.get_type_count_orionld(session, url, model_type, link=None, fiware_service=service)

                if result[0] == 200:
                    print('\t' + model_type)
                    item_count = result[1]['entityCount']
                    for i in range(0, item_count):

                        try:
                            # get first entry in the list, rather than ith one as it will move :S
                            result = unexefiware.ngsildv1.get_type_by_index_orionld(session, url, model_type, i, link=None, fiware_service=service)

                            model = result[1][0]
                            resource_name = model['name']['value']

                            print('\t\t' + model['id'] + ' as ' + resource_name)

                        except Exception as e:
                            self.log(inspect.currentframe(), str(e))