import inspect
import os
import unexeaqua3s.json
import json
import pathlib
import zipfile
import copy
import unexefiware.file

import unexefiware.base_logger
from pyproj import CRS, Transformer

def rgb_to_hex(r,g,b):
    return '#%02x%02x%02x' % (r,g,b)

def transform_list_coords(transformer, element_list, flip_coords):
    if isinstance(element_list[0], list):
        for element in element_list:
            transform_list_coords(transformer, element, flip_coords)
    else:
        if flip_coords == True:
            element_list[1], element_list[0] = transformer.transform(element_list[0], element_list[1])
        else:
            element_list[0], element_list[1] = transformer.transform(element_list[0], element_list[1])


def transform_coords(geojson_data, source_system, target_system, flip_coords):
    transformer = Transformer.from_crs(source_system, target_system)
    # coords[0] - east, coords[1] - north
    feature_index = 0
    for feature_index in range(0, len(geojson_data['features'])):
        if isinstance(geojson_data['features'][feature_index]['geometry']['coordinates'][0], list):
            for element in geojson_data['features'][feature_index]['geometry']['coordinates']:
                transform_list_coords(transformer, element, flip_coords)
        else:
            transform_list_coords(transformer, geojson_data['features'][feature_index]['geometry']['coordinates'], flip_coords)

    return geojson_data


def getGeometryType(data):
    geom_type = ''
    if 'geometries' in data[0]['geometry']:
        geom_type = data[0]['geometry']['geometries'][0]['type']

    if 'type' in data[0]['geometry']:
        geom_type = data[0]['geometry']['type']

    if geom_type == 'GeometryCollection':
        geom_type = data[0]['geometry']['geometries'][0]['type']

    if geom_type == 'LineString':
        return 'line'

    if geom_type == 'Point':
        return 'circle'

    if geom_type == 'Polygon' or geom_type == 'MultiPolygon':
        return 'fill'

    raise ('Unknown type')


# does the geojson file have AWA colour lookups? for isonzo etc
def geojson_requires_colour_lookup(json_data):
    feature_index = 0
    for feature_index in range(0, len(json_data)):
        # AAWA CLASSE risk
        if 'CLASSE' in json_data[feature_index]['properties']:
            print('CLASSE')
            return True

        # AAWA CL_RISK risk
        if 'CL_RISK' in json_data[feature_index]['properties']:
            print('CL_RISK')
            return True

        if 'hdescript' in json_data[feature_index]['properties']:
            print('hdescript')
            return True

        if 'PDESCRIPT' in json_data[feature_index]['properties']:
            print('PDESCRIPT')
            return True

        if 'RISCHIO' in json_data[feature_index]['properties']:
            print('RISCHIO')
            return True



    return False


def convert_file(geojson_file, resource_name, client_filepath, server_filepath, col):
    try:
        f = open(geojson_file, 'r')
        json_data = json.load(f, parse_float=lambda x: round(float(x), 6))
        f.close()
        # replace properties with index
        server_data = []
        feature_index = 0

        feature_list = None

        if 'features' in json_data:
            feature_list = json_data['features']
        else:
            for entry in json_data:
                if entry['type'] == 'FeatureCollection':
                    feature_list = entry['features']



        # short name with no extension to make loading zip content consistent
        # add mapbox wrapper
        mapbox_data = {}
        mapbox_data['info'] = {}

        mapbox_data['info']['has_colour_lookups'] = geojson_requires_colour_lookup(feature_list)
        mapbox_data['info']['colour'] = col

        for feature_index in range(0, len(feature_list)):
            server_data.append(copy.deepcopy(feature_list[feature_index]['properties']))

            new_properties = {}
            new_properties['index'] = feature_index

            if mapbox_data['info']['has_colour_lookups'] == True:
                colour = col

                # AAWA CLASSE risk
                if 'CLASSE' in feature_list[feature_index]['properties']:
                    if feature_list[feature_index]['properties']['CLASSE'] == 'R1':
                        colour = '#00ff00'
                    if feature_list[feature_index]['properties']['CLASSE'] == 'R2':
                        colour = '#ffff00'
                    if feature_list[feature_index]['properties']['CLASSE'] == 'R3':
                        colour = '#ffc000'
                    if feature_list[feature_index]['properties']['CLASSE'] == 'R4':
                        colour = '#ff0000'

                # AAWA CL_RISK risk
                if 'CL_RISK' in feature_list[feature_index]['properties']:
                    if feature_list[feature_index]['properties']['CL_RISK'] == 'R1':
                        colour = '#00ff00'
                    if feature_list[feature_index]['properties']['CL_RISK'] == 'R2':
                        colour = '#ffff00'
                    if feature_list[feature_index]['properties']['CL_RISK'] == 'R3':
                        colour = '#ffc000'
                    if feature_list[feature_index]['properties']['CL_RISK'] == 'R4':
                        colour = '#ff0000'

                label = 'hdescript'
                if label in feature_list[feature_index]['properties']:
                    colour = rgb_to_hex(255, 255, 0)
                    if feature_list[feature_index]['properties'][label] == 'h>=2':
                        colour = rgb_to_hex(0, 77, 182)

                    if feature_list[feature_index]['properties'][label] == '1.5<=h<2':
                        colour = rgb_to_hex(0, 92, 230)

                    if feature_list[feature_index]['properties'][label] == '1<=h<1.5':
                        colour = rgb_to_hex(0, 122, 255)

                    if feature_list[feature_index]['properties'][label] == '0.5<=h<1':
                        colour = rgb_to_hex(115, 178, 255)

                    if feature_list[feature_index]['properties'][label] == 'h<0.5':
                        colour = rgb_to_hex(190, 210, 255)

                label = 'PDESCRIPT'
                if label in feature_list[feature_index]['properties']:
                    colour = rgb_to_hex(255, 255, 0)

                    if feature_list[feature_index]['properties'][label] == 'F':
                        colour = rgb_to_hex(190, 232, 255)

                    if feature_list[feature_index]['properties'][label] == 'P1':
                        colour = rgb_to_hex(170, 255, 0)

                    if feature_list[feature_index]['properties'][label] == 'P2':
                        colour = rgb_to_hex(255, 255, 0)

                    if feature_list[feature_index]['properties'][label] == 'P3A':
                        colour = rgb_to_hex(255, 170, 0)

                    if feature_list[feature_index]['properties'][label] == 'P3B':
                        colour = rgb_to_hex(255, 82, 0)

                    if feature_list[feature_index]['properties'][label] == 'AA':
                        colour = rgb_to_hex(130, 130, 130)

                label = 'RISCHIO'
                if label in feature_list[feature_index]['properties']:
                    colour = rgb_to_hex(255, 255, 0)

                    if feature_list[feature_index]['properties'][label] == 'F':
                        colour = rgb_to_hex(190, 232, 255)

                    if feature_list[feature_index]['properties'][label] == 'R1':
                        colour = rgb_to_hex(170, 255, 0)

                    if feature_list[feature_index]['properties'][label] == 'R2':
                        colour = rgb_to_hex(255, 255, 0)

                    if feature_list[feature_index]['properties'][label] == 'R3':
                        colour = rgb_to_hex(255, 170, 0)

                    if feature_list[feature_index]['properties'][label] == 'R4':
                        colour = rgb_to_hex(255, 82, 0)


                new_properties['c'] = colour

            feature_list[feature_index]['properties'] = new_properties

        path = os.path.dirname(server_filepath)
        unexefiware.file.buildfilepath(path)

        f = open(server_filepath, 'w')
        f.write(unexeaqua3s.json.dumps(server_data))
        f.close()

        mapbox_data['header'] = {}
        mapbox_data['header']['id'] = resource_name
        mapbox_data['header']['type'] = getGeometryType(feature_list)
        mapbox_data['header']['source'] = resource_name
        mapbox_data['header']['layout'] = {}
        mapbox_data['header']['paint'] = {}

        if mapbox_data['header']['type'] == 'fill':
            mapbox_data['header']['paint']['fill-color'] = ['get', 'c']
            mapbox_data['header']['paint']['fill-opacity'] = 0.25

            mapbox_data['info']['colour_label'] = 'fill-color'

        if mapbox_data['header']['type'] == 'circle':
            mapbox_data['header']['paint']['circle-color'] = ['get', 'c']
            mapbox_data['header']['paint']['circle-radius'] = {}
            mapbox_data['header']['paint']['circle-radius']['base'] = 5
            mapbox_data['header']['paint']['circle-radius']['stops'] = [[1, 5], [20, 5]]
            mapbox_data['header']['paint']['circle-stroke-width'] = 1;
            mapbox_data['header']['paint']['circle-stroke-color'] = '#000000';

            mapbox_data['info']['colour_label'] = 'circle-color'

        if mapbox_data['header']['type'] == 'line':
            mapbox_data['header']['paint']['line-width'] = 3
            mapbox_data['header']['paint']['line-color'] = ['get', 'c']

            mapbox_data['info']['colour_label'] = 'line-color'

        mapbox_data['geojson'] = json_data

        zipf = zipfile.ZipFile(client_filepath, "w", zipfile.ZIP_DEFLATED)
        zipf.writestr(resource_name, unexeaqua3s.json.dumps(mapbox_data))
        zipf.close()
    except Exception as e:
        logger = unexefiware.base_logger.BaseLogger()
        logger.exception(inspect.currentframe(),e)