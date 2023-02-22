import epanet_fiware.epanet_outfile_handler
import epanet_fiware.waternetwork
import pyproj
import os
import unexeaqua3s.json
import unexefiware.ngsildv1
import requests

def create_waternetwork(filename, coord_system):

    inp_file = epanet_fiware.epanetmodel.EPAnetModel('temp', filename)
    transformer = epanet_fiware.ngsi_ld_writer.transformer(coord_system)

    fiware_waternetwork = {}
    fiware_component = {}
    reverse_lookups = {}

    fiware_waternetwork['WaterNetwork'] = {}
    fiware_waternetwork['Components'] = {}

    fiware_waternetwork['WaterNetwork']['id'] = 'urn:ngsi-ld:WaterNetwork:01'
    fiware_waternetwork['WaterNetwork']['type'] = 'WaterNetwork'
    fiware_waternetwork['WaterNetwork']['description'] = {}
    fiware_waternetwork['WaterNetwork']['description']['type'] = 'Property'
    fiware_waternetwork['WaterNetwork']['description']['value'] = 'Free Text'

    fiware_waternetwork['WaterNetwork']['components'] = {}
    fiware_waternetwork['WaterNetwork']['components']['type'] = 'Property'
    fiware_waternetwork['WaterNetwork']['components']['value'] = []

    fiware_waternetwork['WaterNetwork']['@context'] = epanet_fiware.waternetwork.link_lookup['WaterNetwork']

    for component in epanet_fiware.waternetwork.jsonld_labels:

        component_list  = []

        if component == 'Junction':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_junction(inp_file.proj_for_simulation, transformer)

        if component == 'Reservoir':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_reservoir(inp_file.proj_for_simulation, transformer)

        if component == 'Tank':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_tank(inp_file.proj_for_simulation, transformer)

        if component == 'Pipe':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_pipe(inp_file.proj_for_simulation, transformer)

        if component == 'Pump':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_pump(inp_file.proj_for_simulation, transformer)

        if component == 'Valve':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_valve(inp_file.proj_for_simulation, transformer)

        if component == 'Pattern':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_pattern(inp_file.proj_for_simulation)

        if component == 'Curve':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_curve(inp_file.proj_for_simulation)

        if len(component_list) > 0:

            fiware_waternetwork['WaterNetwork']['components']['value'].append( component)
            fiware_waternetwork['Components'][component] = component_list

            fiware_waternetwork['WaterNetwork'][component] = {}
            fiware_waternetwork['WaterNetwork'][component]['type'] = 'Property'
            fiware_waternetwork['WaterNetwork'][component]['value'] = []
            fiware_waternetwork['WaterNetwork'][component]['count'] = str(len(component_list))


            for entry in component_list:
                jsonld = {}
                jsonld['type'] = 'Relationship'
                jsonld['object'] = entry['id']

                try:
                    fiware_waternetwork['WaterNetwork'][component]['value'].append(entry['id'])
                except Exception as e:
                    print(str(e) + filename)

    return fiware_waternetwork


def add_waternetwork(url, fiware_waternetwork, fiware_service):

    session = requests.session()

    for component_type in fiware_waternetwork['Components']:

        for entry in fiware_waternetwork['Components'][component_type]:
            result = unexefiware.ngsildv1.delete_instance(session, url,entry['id'], entry['@context'][0], fiware_service)

            result = unexefiware.ngsildv1.create_instance(session,url, unexeaqua3s.json.dumps(entry), fiware_service)
            if result[0] == 201:
                print('Added: ' + entry['id'])
    #water network
    result = unexefiware.ngsildv1.delete_instance(session, url, fiware_waternetwork['WaterNetwork']['id'], fiware_waternetwork['WaterNetwork']['@context'][0], fiware_service)

    result = unexefiware.ngsildv1.create_instance(session, url, unexeaqua3s.json.dumps(fiware_waternetwork['WaterNetwork']), fiware_service)
    if result[0] == 201:
        print('Added: ' + fiware_waternetwork['WaterNetwork']['id'])
    else:
        print(str(result))

def rawname_from_id(id):
    id = id.replace('urn:ngsi-ld:','')
    #type:name
    return id.split(':')[1]


def create_waternetwork2(filename, coord_system):

    inp_file = epanet_fiware.epanetmodel.EPAnetModel('temp', filename)
    transformer = epanet_fiware.ngsi_ld_writer.transformer(coord_system)

    fiware_waternetwork = {}
    fiware_component = {}
    reverse_lookups = {}

    fiware_waternetwork['Components'] = {}

    fiware_waternetwork['WaterNetwork'] = {}

    fiware_waternetwork['WaterNetwork']['id'] = 'urn:ngsi-ld:WaterNetwork:01'
    fiware_waternetwork['WaterNetwork']['type'] = 'WaterNetwork'
    fiware_waternetwork['WaterNetwork']['description'] = {}
    fiware_waternetwork['WaterNetwork']['description']['type'] = 'Property'
    fiware_waternetwork['WaterNetwork']['description']['value'] = 'Free Text'

    fiware_waternetwork['WaterNetwork']['isComposedOf'] = []

    fiware_waternetwork['WaterNetwork']['@context'] = epanet_fiware.waternetwork.link_lookup['WaterNetwork']

    for component in epanet_fiware.waternetwork.jsonld_labels:

        component_list = []

        if component == 'Junction':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_junction(inp_file.proj_for_simulation, transformer)

        if component == 'Reservoir':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_reservoir(inp_file.proj_for_simulation, transformer)

        if component == 'Tank':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_tank(inp_file.proj_for_simulation, transformer)

        if component == 'Pipe':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_pipe(inp_file.proj_for_simulation, transformer)

        if component == 'Pump':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_pump(inp_file.proj_for_simulation, transformer)

        if component == 'Valve':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_valve(inp_file.proj_for_simulation, transformer)

        if component == 'Pattern':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_pattern(inp_file.proj_for_simulation)

        if component == 'Curve':
            component_list = epanet_fiware.ngsi_ld_writer.json_ld_curve(inp_file.proj_for_simulation)

        if len(component_list) > 0:

            fiware_waternetwork['Components'][component] = component_list

            for entry in component_list:
                jsonld = {}
                jsonld['type'] = 'Relationship'
                jsonld['object'] = entry['id']
                jsonld['datasetId'] = 'urn:ngsi-ld:Dataset:' + rawname_from_id(jsonld['object'])

                try:
                    fiware_waternetwork['WaterNetwork']['isComposedOf'].append(jsonld)
                except Exception as e:
                    print(str(e) + filename)

    return fiware_waternetwork



source_data = [('/../data/AAA/waternetwork/epanet.inp', 32632),
    #('/../data/GT/waternetwork/epanet.inp', 4326),
    #('/../data/WIS/waternetwork/epanet.inp', 4326)
]

for entry in source_data:
    print()
    print(entry[0])

    fiware_waternetwork = create_waternetwork( os.getcwd()+entry[0], pyproj.CRS.from_epsg(entry[1]) )

    for entry in fiware_waternetwork['Components']:
        print(entry + ' ' + str(len(fiware_waternetwork['Components'][entry])))

    raw_data = unexeaqua3s.json.dumps(fiware_waternetwork['WaterNetwork'])
    print('Water Network Packet size:' +str(len(raw_data)))

    print(unexeaqua3s.json.dumps(fiware_waternetwork, indent=4))

    #add_waternetwork('http://localhost:1026', fiware_waternetwork, 'AAA')

