import inspect

import unexeaqua3s.fiwareresources
import threading
import blueprints.globals
import blueprints.debug
import os
import unexefiware.file
import requests
import pyproj
import epanet_fiware.epanet_outfile_handler
import epanet_fiware.waternetwork
import epanet_fiware.epanetmodel
import json
import jenkspy

class Aqua3sWaterNetwork(epanet_fiware.waternetwork.WaterNetwork):
    def __init__(self):
        super().__init__()

    def diameter_to_line_width(self, breaks, component_diam):

        if component_diam < 500:
            return 4

        if component_diam < 1000:
            return 8


        return 12


        for i in range(0, len(breaks)):
            if component_diam <= breaks[i]:
                return (((i + 1) * 3) / 6.0) * 2.0


    def geojsonise(self, flip_coordinates=False):
        breaks = jenkspy.jenks_breaks(self.reverse_lookups['diameter'], 7)

        variable_colours = {
            'Pipe': '#ff0000',
            'Pump': '#FDEE00',
            'Valve': '#FF7E00',
            'Junction': '#000000',
            'Reservoir': '#0000FF',
            'Tank': '#0048BA'
        }

        network_geojson = {}
        for current_component_label in list(variable_colours.keys()):
            data = {}
            data['source'] = {}
            data['source']['id'] = id

            data['geojson'] = {}
            data['geojson']['type'] = 'FeatureCollection'
            data['geojson']['features'] = []

            data['setup'] = {}
            data['setup']['id'] = id
            data['setup']['source'] = id
            data['setup']['type'] = 'line'
            data['setup']['layout'] = {}
            data['setup']['layout']['visibility'] = 'visible'
            data['setup']['layout']['line-join'] = 'round'
            data['setup']['layout']['line-cap'] = 'round'

            data['setup']['paint'] = {}
            data['setup']['paint']['line-color'] = ['get', 'line-color']
            data['setup']['paint']['line-width'] = ['get', 'line-width']
            data['setup']['filter'] = {}
            data['setup']['filter'] = ['==', '$type', 'LineString']

            if current_component_label in self.fiware_component:
                #print(current_component_label)
                feature_index = 0
                for component in self.fiware_component[current_component_label]:
                    try:
                        name = component['id']

                        if name == 'urn:ngsi-ld:Valve:BP600.1500.BP2600.15.1':
                            print()

                        feature = {}
                        feature['type'] = 'Feature'
                        feature['properties'] = {}

                        # index map lookup
                        feature['properties']['index'] = feature_index
                        feature_index = feature_index + 1

                        # index for simulation
                        info = self.get_simulation_index_from_id(name)
                        feature['properties']['sim_source'] = info[0]
                        feature['properties']['sim_source_index'] = info[1]

                        if current_component_label in ['Pipe', 'Pump', 'Valve']:
                            startID = component['startsAt']['object']
                            endID = component['endsAt']['object']
                            vx = None
                            vy = None
                            if 'vertices' in component.keys():
                                vertices = component['vertices']['value']['coordinates']
                                if isinstance(vertices[0], list):
                                    vx = [point[0] for point in vertices]
                                    vy = [point[1] for point in vertices]
                                else:
                                    vx = [vertices[0]]
                                    vy = [vertices[1]]

                            component_diam = 100
                            #do pumps have diamater?
                            if current_component_label not in ['Pump']:
                                component_diam = component['diameter']['value']

                            startPos = self.get_coordinates_from_id(startID)
                            endPos = self.get_coordinates_from_id(endID)

                            feature['properties']['line-width'] = self.diameter_to_line_width(breaks, component_diam)
                            feature['properties']['line-color'] = variable_colours[current_component_label]

                            feature['geometry'] = {}
                            feature['geometry']['type'] = 'LineString'
                            feature['geometry']['coordinates'] = []

                            if not flip_coordinates:
                                feature['geometry']['coordinates'].append(startPos)
                            else:
                                feature['geometry']['coordinates'].append([startPos[1], startPos[0]])

                            try:
                                if vx is not None:
                                    for i in range(0, len(vx)):
                                        coord = []

                                        if not flip_coordinates:
                                            coord.append(vx[i])
                                            coord.append(vy[i])
                                        else:
                                            coord.append(vy[i])
                                            coord.append(vx[i])

                                        feature['geometry']['coordinates'].append(coord)

                                if not flip_coordinates:
                                    feature['geometry']['coordinates'].append(endPos)
                                else:
                                    feature['geometry']['coordinates'].append([endPos[1], endPos[0]])
                            except Exception as e:
                                print('borked! - ' + str(e))

                            data['geojson']['features'].append(feature)

                        if current_component_label in ['Junction', 'Reservoir', 'Tank']:
                            coord = component['location']['value']['coordinates']

                            if flip_coordinates is True:
                                coord = [coord[1], coord[0]]

                            feature['geometry'] = {}
                            feature['geometry']['type'] = 'Point'
                            feature['geometry']['coordinates'] = coord
                            feature['properties']['line-color'] = variable_colours[current_component_label]
                            feature['properties']['circle-radius'] = 7

                            data['geojson']['features'].append(feature)

                    except Exception as e:
                        print('waternetwork.geojsonise():Bad Property: ' + name + ' ' + str(e))
                        print(json.dumps(component, indent=4, sort_keys=True))

                if current_component_label not in ['Curve', 'Pattern']:
                    layer = current_component_label.lower() + '_geojson'
                    network_geojson[layer] = data

        return network_geojson

    def get_stuff(self) ->dict:
        data = {}
        try:
            if 'Junction' in self.fiware_component:
                for item in self.fiware_component['Junction']:
                    data[item['id']] = [item['location']['value']['coordinates'][0],item['location']['value']['coordinates'][1]]
        except Exception as e:
            print(inspect.currentframe() + ' Epic Fail')
        return data


class Aqua3sFiwareResources(unexeaqua3s.fiwareresources.FiwareResources):
    def __init__(self, options=None):
        super().__init__(options)
        #GARETH - this is hard-coded in base to kr_10
        self.remote_root = 'data/'

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
                                self.resources[fiware_service]['userlayer'][resource_name]['server'] = json.load(f)
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

                                if fiware_service == 'GUW':
                                    coord_system = pyproj.CRS.from_epsg(32646)
                                    flip_coordindates = True

                                self.resources[fiware_service]['epanet'] = Aqua3sWaterNetwork()
                                self.resources[fiware_service]['epanet'].load_epanet(self.get_local_filepath(model['file_path']['value']), coord_system)

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



class ResourceManager(Aqua3sFiwareResources):
    def __init__(self):

        try:
            webdav_options = {
               'webdav_hostname': os.environ['WEBDAV_URL'],
                'webdav_login': os.environ['WEBDAV_NAME'],
                'webdav_password': os.environ['WEBDAV_PASS']
            }

            super().__init__(options = webdav_options)

            self.url = os.environ['DEVICE_BROKER']
            self.file_root = os.environ['FILE_PATH'] + os.sep + os.environ['FILE_VISUALISER_FOLDER']

            unexefiware.file.buildfilepath(self.file_root)

        except Exception as e:
            blueprints.debug.servicelog.exception(inspect.currentframe(), e)

        self.has_loaded_content = False


    def launch(self):
        self.thread = threading.Thread(target = self._loadingthread, args='')
        self.thread.start()

    def _loadingthread(self):

        try:
            self.init(url=self.url, file_root= self.file_root , fiware_service_list=blueprints.globals.fiware_service_list)


        except Exception as e:
            blueprints.debug.servicelog.exception(inspect.currentframe(), e)

        self.has_loaded_content = True

    def isAvailable(self):
        return self.has_loaded_content

    def reload(self, fiware_service):
        print('Reloading!')
        self.clone_pilot(fiware_service)
        self.clone_from_orion(self.url, fiware_service, types=['WaterNetwork', 'SimulationResult', 'UserLayer'])

    @staticmethod
    def one_time_init():
        blueprints.globals.fiware_resources = ResourceManager()
        blueprints.globals.fiware_resources.logger = blueprints.debug.servicelog
        blueprints.globals.fiware_resources.launch()

    def clone_from_orion(self, url, fiware_service, types):
        super().clone_from_orion(url,fiware_service,types)

        #remove gnarly content
        if fiware_service == 'EYA':
            for userlayer in self.resources[fiware_service]:
                for layer in self.resources[fiware_service][userlayer]:
                    for entry in self.resources[fiware_service][userlayer][layer]['server']:
                        labels_to_bin = ['description', 'styleUrl']

                        for label in labels_to_bin:
                            if label in entry:
                                entry.pop(label)


