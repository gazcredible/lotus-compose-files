# flake8: noqa: W293,E303,501

from pyproj import CRS
import jenkspy
import json
import copy

import matplotlib.pyplot as plt

import epanet_fiware.ngsi_ld_writer
import epanet_fiware.epanetmodel
import epanet_fiware.epanet_simulation
import epanet_fiware.waternetwork
import unexefiware.model
import epanet.toolkit as en

jsonld_labels = ['Junction', 'Reservoir', 'Tank', 'Pipe', 'Pump', 'Valve', 'Pattern', 'Curve']

link_lookup = {}
link_lookup['Junction'] = 'https://schema.lab.fiware.org/ld/context'  # 'https://smartdatamodels.org/context.jsonld' #'http://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context'
link_lookup['Reservoir'] = 'https://schema.lab.fiware.org/ld/context'  # 'http://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context'
link_lookup['Tank'] = 'https://schema.lab.fiware.org/ld/context'  # 'http://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context'
link_lookup['Pipe'] = 'https://schema.lab.fiware.org/ld/context'
link_lookup['Pump'] = 'https://schema.lab.fiware.org/ld/context'
link_lookup['Valve'] = 'https://schema.lab.fiware.org/ld/context'
link_lookup['Pattern'] = 'https://schema.lab.fiware.org/ld/context'
link_lookup['Curve'] = 'https://schema.lab.fiware.org/ld/context'

link_lookup['WaterNetwork'] = 'https://smartdatamodels.org/context.jsonld'


class WaterNetwork:
    def __init__(self):
        # this is the fiware representation of the waternetwork (WaterNetwork)
        self.fiware_waternetwork = {}

        # this is the set of components that the water network references ('Junction', 'Reservoir', 'Tank', 'Pipe', 'Pump', 'Valve', 'Pattern', 'Curve')
        self.fiware_component = {}

        # this is a set of reverse lookups from fiware ID ('Junction', 'Reservoir', 'Tank', 'Pipe', 'Pump', 'Valve', 'Pattern', 'Curve')
        # to index (as the components are all stored in arrays
        self.reverse_lookups = {}
        self.lookups = {}

        # these are generated from the epanet file
        self.epanet_lookups = {}

    def build_from_fiware(self, fiware_water_network, fiware_components):
        print('building: ' + fiware_water_network['id'])

        try:
            self.fiware_waternetwork = {}
            self.fiware_component = {}
            self.reverse_lookups = {}
            self.epanet_lookups = {}

            self.fiware_waternetwork['WaterNetwork'] = copy.deepcopy(fiware_water_network)

            for component in self.fiware_waternetwork['WaterNetwork']['components']['value']:
                self.fiware_component[component] = []

                if isinstance(self.fiware_waternetwork['WaterNetwork'][component]['value'], list) is True:
                    for inst_id in self.fiware_waternetwork['WaterNetwork'][component]['value']:
                        inst = unexefiware.model.get_entity_from_orion_list(fiware_components[component], inst_id)
                        self.fiware_component[component].append(copy.deepcopy(inst))
                else:
                    self.fiware_component[component].append(copy.deepcopy(self.fiware_waternetwork['WaterNetwork'][component]['value']))

            self.create_reverselookup()
        except Exception as e:
            print('build_from_fiware() - failed:' + str(e))

    def build_epanetlookups(self, proj):
        # For simulation visualisation, the geojson indices need to map to the simulation indices
        # for the inp file, we can get these from here. For fiware models, we'll need to do something else
        # I assume this will be to parse the sim output and link everything up from there.
        try:
            self.epanet_lookups = {}

            self.epanet_lookups['nodes'] = {}
            self.epanet_lookups['nodes']['index'] = {}
            self.epanet_lookups['nodes']['label'] = {}

            num_nodes = en.getcount(ph=proj, object=en.NODECOUNT)+1
            for index in range(1, num_nodes):
                zero_based_index = index - 1
                label = en.getnodeid(proj, index)
                self.epanet_lookups['nodes']['index'][zero_based_index] = label
                self.epanet_lookups['nodes']['label'][label] = zero_based_index

            self.epanet_lookups['links'] = {}
            self.epanet_lookups['links']['index'] = {}
            self.epanet_lookups['links']['label'] = {}

            num_links = en.getcount(ph=proj, object=en.LINKCOUNT)+1
            for index in range(1, num_links):
                zero_based_index = index - 1
                label = en.getlinkid(proj, index)
                self.epanet_lookups['links']['index'][zero_based_index] = label
                self.epanet_lookups['links']['label'][label] = zero_based_index
        except Exception as e:
            print('build_epanetlookups() - failed! ' + str(e))

    def get_simulation_index_from_id(self, name):
        for type_label in epanet_fiware.waternetwork.jsonld_labels:
            if type_label in name:
                epanet_label = name.replace('urn:ngsi-ld:' + type_label + ':', '')

                if epanet_label in self.epanet_lookups['nodes']['label']:
                    return ['nodes', self.epanet_lookups['nodes']['label'][epanet_label]]

                if epanet_label in self.epanet_lookups['links']['label']:
                    return ['links', self.epanet_lookups['links']['label'][epanet_label]]

        return ['node', -1]

    def load_epanet(self, filename, coord_system=CRS.from_epsg(4326)):
        try:
            self.fiware_waternetwork = {}
            self.fiware_component = {}
            self.reverse_lookups = {}

            self.epanetmodel = epanet_fiware.epanetmodel.EPAnetModel('temp', filename)

            self.build_epanetlookups(self.epanetmodel.proj_for_simulation)
            if False:
                print('EPANET data')
                print('Nodes')
                for entry in self.epanet_lookups['nodes']['index']:
                    print('\t' + str(entry) + ' ' + self.epanet_lookups['nodes']['index'][entry])

            transformer = epanet_fiware.ngsi_ld_writer.transformer(coord_system)

            self.fiware_waternetwork['WaterNetwork'] = {}

            self.fiware_waternetwork['WaterNetwork']['id'] = 'urn:ngsi-ld:WaterNetwork:01'
            self.fiware_waternetwork['WaterNetwork']['type'] = 'WaterNetwork'
            self.fiware_waternetwork['WaterNetwork']['description'] = {}
            self.fiware_waternetwork['WaterNetwork']['description']['type'] = 'Property'
            self.fiware_waternetwork['WaterNetwork']['description']['value'] = 'Free Text'

            self.fiware_waternetwork['WaterNetwork']['components'] = {}
            self.fiware_waternetwork['WaterNetwork']['components']['type'] = 'Property'
            self.fiware_waternetwork['WaterNetwork']['components']['value'] = []

            self.fiware_waternetwork['WaterNetwork']['@context'] = link_lookup['WaterNetwork']

            for component in jsonld_labels:

                if component == 'Junction':
                    self.fiware_component[component] = epanet_fiware.ngsi_ld_writer.json_ld_junction(self.epanetmodel.proj_for_simulation, transformer)

                if component == 'Reservoir':
                    self.fiware_component[component] = epanet_fiware.ngsi_ld_writer.json_ld_reservoir(self.epanetmodel.proj_for_simulation, transformer)

                if component == 'Tank':
                    self.fiware_component[component] = epanet_fiware.ngsi_ld_writer.json_ld_tank(self.epanetmodel.proj_for_simulation, transformer)

                if component == 'Pipe':
                    self.fiware_component[component] = epanet_fiware.ngsi_ld_writer.json_ld_pipe(self.epanetmodel.proj_for_simulation, transformer)

                if component == 'Pump':
                    self.fiware_component[component] = epanet_fiware.ngsi_ld_writer.json_ld_pump(self.epanetmodel.proj_for_simulation, transformer)

                if component == 'Valve':
                    self.fiware_component[component] = epanet_fiware.ngsi_ld_writer.json_ld_valve(self.epanetmodel.proj_for_simulation, transformer)

                if component == 'Pattern':
                    self.fiware_component[component] = epanet_fiware.ngsi_ld_writer.json_ld_pattern(self.epanetmodel.proj_for_simulation)

                if component == 'Curve':
                    self.fiware_component[component] = epanet_fiware.ngsi_ld_writer.json_ld_curve(self.epanetmodel.proj_for_simulation)

                if len(self.fiware_component[component]) > 0:

                    self.fiware_waternetwork['WaterNetwork']['components']['value'].append(component)

                    self.fiware_waternetwork['WaterNetwork'][component] = {}
                    self.fiware_waternetwork['WaterNetwork'][component]['type'] = 'Property'
                    self.fiware_waternetwork['WaterNetwork'][component]['value'] = []

                    for entry in self.fiware_component[component]:
                        jsonld = {}
                        jsonld['type'] = 'Relationship'
                        jsonld['object'] = entry['id']

                        try:
                            self.fiware_waternetwork['WaterNetwork'][component]['value'].append(entry['id'])
                        except Exception as e:
                            print(str(e) + filename)

            self.create_reverselookup()

        except Exception as e:
            print(str(e) + filename)

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

                            data['geojson']['features'].append(feature)

                    except Exception as e:
                        print('waternetwork.geojsonise():Bad Property: ' + name + ' ' + str(e))
                        print(json.dumps(component, indent=4, sort_keys=True))

                if current_component_label not in ['Curve', 'Pattern']:
                    layer = current_component_label.lower() + '_geojson'
                    network_geojson[layer] = data

        return network_geojson

    def create_reverselookup(self):
        self.reverse_lookups = {}
        self.lookup = {}

        self.reverse_lookups['diameter'] = []

        try:
            for component in jsonld_labels:
                index = 0
                self.reverse_lookups[component] = {}
                self.lookup[component] = {}

                if component in self.fiware_component:
                    for element in self.fiware_component[component]:

                        if 'id' in element:
                            self.reverse_lookups[component][element['id']] = index
                            self.lookup[component][index] = element['id']
                            index = index + 1

                            if component == 'Pipe':
                                if element['diameter']['value'] not in self.reverse_lookups['diameter']:
                                    self.reverse_lookups['diameter'].append(element['diameter']['value'])
        except Exception as e:
            print('create_reverselookup() - failed: ' + str(e))

    def get_index_from_id(self, id):

        try:
            for component in jsonld_labels:
                if component in id:
                    return self.reverse_lookups[component][id]
        except Exception as e:
            print('get_index_from_id() - failed: ' + str(e))

        return None

    def get_coordinates_from_id(self, id):

        try:
            for component in jsonld_labels:
                if component in id:
                    index = self.reverse_lookups[component][id]
                    return self.fiware_component[component][index]['location']['value']['coordinates']

        except Exception as e:
            print('get_coordinates_from_id() - failed: ' + str(e))

        return None

    def diameter_to_line_width(self, breaks, component_diam):
        for i in range(0, len(breaks)):
            if component_diam <= breaks[i]:
                return ((i + 1) * 3) / 6.0

    def visualise_with_matplotlib(self):
        geojson_data = self.geojsonise()

        for component in geojson_data:
            try:
                if component in ['pipe_geojson', 'pump_geojson', 'valve_geojson']:

                    if len(geojson_data[component]['geojson']['features']) > 0:
                        fig = plt.figure()
                        ax = fig.gca()

                        for feature in geojson_data[component]['geojson']['features']:
                            x_cord = []
                            y_cord = []
                            for point in feature['geometry']['coordinates']:
                                x_cord.append(point[0])
                                y_cord.append(point[1])

                            plt.plot(x_cord, y_cord, color=feature['properties']['line-color'],
                                     linewidth=feature['properties']['line-width'])
                        ax.axis('scaled')
                        plt.title(component)
                        plt.show()
                else:

                    if len(geojson_data[component]['geojson']['features']) > 0:
                        fig = plt.figure()
                        ax = fig.gca()

                        for feature in geojson_data[component]['geojson']['features']:
                            if 'geometry' in feature:
                                x_cord = feature['geometry']['coordinates'][0]
                                y_cord = feature['geometry']['coordinates'][1]
                                plt.scatter(x_cord, y_cord, color=feature['properties']['line-color'])
                        ax.axis('scaled')
                        plt.title(component)
                        plt.show()

            except Exception as e:
                print(str(e))