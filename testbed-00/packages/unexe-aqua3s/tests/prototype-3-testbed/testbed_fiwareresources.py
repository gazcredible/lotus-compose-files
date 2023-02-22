import local_environment_settings
import os
import unexeaqua3s.json

import unexefiware.fiwarewrapper
import unexefiware.fiwarewrapper_debug
import unexefiware.base_logger
import unexefiware.time
import unexeaqua3s.resourcebuilder
import unexeaqua3s.support
import requests

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
                            print('\t'+ result[1][0]['id'] +' ' + result[1][0]['name']['value']+' ' + result[1][0]['file_path']['value'])


                    except Exception as e:
                        print('Vague failure: ' + str(e))

                print()

    print()


def add_user_resources(url:str, pilot_list:list = None, create_fiware_resources:bool = True, force_build_files:bool = False):

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
    resourcebuilder.remote_root = 'data/'
    #gareth -   this is the same as the path in visualiser.resourceManager
    resourcebuilder.init(path_root = os.environ['FILE_PATH'] + os.sep + os.environ['FILE_VISUALISER_FOLDER'], clone_remote=True,delete_local=True, pilot_list=pilot_list)

    resources = resourcebuilder.process_kmz_resources()
    resources += resourcebuilder.process_shapefile_resources(force_build_files)
    resources += resourcebuilder.process_waternetwork_resources()

    if create_fiware_resources:
        resourcebuilder.create_fiware_assets(url, resources, upload_files=True)


def testbed(fiware_wrapper, fiware_service):
    quitApp = False

    logger = unexefiware.base_logger.BaseLogger()

    while quitApp is False:
        print('\n')
        print('Testbed FIWARE resources')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])

        print('\n')
        print('1..View Webdav resources')
        print('2..View Userlayers')
        print('3..Build Userlayers')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':

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
            #resourcebuilder.remote_root = 'kr_10/data/'
            resourcebuilder.remote_root = '/data/'

            pilots = os.environ['PILOTS'].split(',')
            for pilot in pilots:
                print(pilot)
                resourcebuilder.print_remote_tree(resourcebuilder.remote_root+pilot+os.sep)
                print()

        if key == '2':
            pilots = os.environ['PILOTS'].split(',')
            for pilot in pilots:
                print(pilot)
                print_resources(os.environ['DEVICE_BROKER'], pilot.replace(' ', ''), )
                print()

        if key == '3':
            pilots = os.environ['PILOTS'].split(',')
            add_user_resources(os.environ['DEVICE_BROKER'], pilot_list = pilots, force_build_files=False)

        if key == '4':
            pilots = os.environ['PILOTS'].split(',')
            for pilot in pilots:
                unexeaqua3s.support.delete_resources(os.environ['DEVICE_BROKER'], pilot)
        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    logger = unexefiware.base_logger.BaseLogger()

    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    fiware_wrapper.init(logger=logger)
    fiware_service = 'AAA'

    testbed(fiware_wrapper=None, fiware_service=fiware_service)
