import os
import requests

import unexefiware.ngsildv1
import unexeaqua3s.resourcebuilder
import unexeaqua3s.fiwareresources

def add_user_resources(url, pilot_list = None, create_fiware_resources = True, force_build_files = False):

    if 'WEBDAV_URL' not in os.environ:
        raise Exception('Webdav not defined')

    options = {
        'webdav_hostname':  os.environ['WEBDAV_URL'],
        'webdav_login': os.environ['WEBDAV_NAME'],
        'webdav_password': os.environ['WEBDAV_PASS']
    }

    resourcebuilder = unexeaqua3s.resourcebuilder.ResourceBuilder(options=options)
    resourcebuilder.convert_files = True
    resourcebuilder.perform_file_operations = True
    #gareth -   this is the same as the path in visualiser.resourceManager
    resourcebuilder.remote_root = '/data/'
    resourcebuilder.init(path_root = os.environ['FILE_PATH'] + os.sep + 'visualiser', clone_remote=True,pilot_list=pilot_list)

    for service in pilot_list:
        resourcebuilder.clone_pilot(service)

    resources = resourcebuilder.process_kmz_resources()
    resources += resourcebuilder.process_shapefile_resources(force_build_files)
    resources += resourcebuilder.process_waternetwork_resources()

    if create_fiware_resources:
        resourcebuilder.create_fiware_assets(url, resources)


def print_resources(broker_url, service):
    types = ['WaterNetwork', 'SimulationResult', 'UserLayer']

    session = requests.Session()
    link = 'https://schema.lab.fiware.org/ld/context'

    for model_type in types:
        result = unexefiware.ngsildv1.get_type_count_orionld(session, broker_url, model_type, link=link, fiware_service=service)

        if result[0] == 200:

            item_count = result[1]['entityCount']

            if item_count > 0:
                print(model_type)

                for i in range(0, item_count):
                    try:
                        # get first entry in the list, rather than ith one as it will move :S
                        result = unexefiware.ngsildv1.get_type_by_index_orionld(session, broker_url, model_type, i, link, service)
                        if result[0] == 200:
                            print('\t'+ result[1][0]['id'])


                    except Exception as e:
                        print('Vague failure: ' + str(e))

                print()

    print()

def delete_resources(broker_url, service):
    types = ['WaterNetwork', 'SimulationResult', 'UserLayer']

    session = requests.Session()
    link = 'https://schema.lab.fiware.org/ld/context'

    for model_type in types:
        result = unexefiware.ngsildv1.get_type_count_orionld(session, broker_url, model_type, link=link, fiware_service=service)

        if result[0] == 200:

            item_count = result[1]['entityCount']

            if item_count > 0:
                for i in range(0, item_count):
                    try:
                        # get first entry in the list, rather than ith one as it will move :S
                        result = unexefiware.ngsildv1.get_type_by_index_orionld(session, broker_url, model_type, 0, link, service)
                        if result[0] == 200:
                            result = unexefiware.ngsildv1.delete_instance(session, broker_url, result[1][0]['id'], link, service)

                            if result[0] != 200:
                                print('Deletion failed: ' + result[1])

                    except Exception as e:
                        print('Vague failure: ' + str(e))

def testbed(fiware_wrapper, fiware_service):

    quitApp = False
    pilot_list = [fiware_service]

    pilot_list = ['GUW','AAA']


    while quitApp is False:
        print('aqua3s:' + os.environ['DEVICE_BROKER'] +'\n')

        print()
        print('1..View Userlayers')
        print('2..Build Userlayers')
        print('3..Delete Userlayers')

        print('4..Just convert files')
        print('5..View webdav resources')
        print('6..Copy userlayers to service file store')

        print('99..Set-up webdav with epanet')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            for pilot in pilot_list:
                print(pilot)
                print_resources(os.environ['DEVICE_BROKER'], pilot.replace(' ', ''), )
                print()

        if key == '2':
            add_user_resources(os.environ['DEVICE_BROKER'], pilot_list = pilot_list)

        if key == '3':
            for pilot in pilot_list:
                delete_resources(os.environ['DEVICE_BROKER'], pilot.replace(' ', ''), )

        if key == '4':
            add_user_resources(os.environ['DEVICE_BROKER'], pilot_list = pilot_list, create_fiware_resources=False, force_build_files = True)

        if key =='5':
            if 'WEBDAV_URL' not in os.environ:
                raise Exception('Webdav not defined')

            options = {
                'webdav_hostname': os.environ['WEBDAV_URL'],
                'webdav_login': os.environ['WEBDAV_NAME'],
                'webdav_password': os.environ['WEBDAV_PASS']
            }

            resourcebuilder = unexeaqua3s.resourcebuilder.ResourceBuilder(options=options)
            resourcebuilder.convert_files = False
            resourcebuilder.perform_file_operations = False
            resourcebuilder.remote_root = '/data/'

            for pilot in pilot_list:
                print(pilot)
                resourcebuilder.print_remote_tree(resourcebuilder.remote_root+os.sep+pilot+os.sep)
                print()

        if key == '6':
            options = {
                'webdav_hostname': os.environ['WEBDAV_URL'],
                'webdav_login': os.environ['WEBDAV_NAME'],
                'webdav_password': os.environ['WEBDAV_PASS']
            }

            resources = unexeaqua3s.fiwareresources.FiwareResources(options)
            resources.url = os.environ['DEVICE_BROKER']
            resources.file_root = os.environ['FILE_PATH'] + os.sep + os.environ['FILE_VISUALISER_FOLDER']

            resources.remote_root = '/data/'

            unexefiware.file.buildfilepath(resources.file_root)
            resources.init(url=resources.url, file_root=resources.file_root, fiware_service_list=pilot_list)

        if key == '99':
            options = {
                'webdav_hostname': os.environ['WEBDAV_URL'],
                'webdav_login': os.environ['WEBDAV_NAME'],
                'webdav_password': os.environ['WEBDAV_PASS']
            }

            dav = unexeaqua3s.webdav.webdav(options)

            if dav.is_remote_available():
                dav.copy_to_dav('local_data/KMKHYA_GHY_WDN.inp', 'data/GUW/epanet/KMKHYA_GHY_WDN.inp')
                dav.copy_to_dav('local_data/KMKHYA_GHY_WDN.inp', 'data/GUW/waternetwork/epanet.inp')

                dav.copy_to_dav('local_data/TS network.inp', 'data/AAA/epanet/TS network.inp')
                dav.copy_to_dav('local_data/TS network.inp', 'data/AAA/waternetwork/epanet.inp')



        if key == 'x':
            quitApp = True
