import backlogbuilder
import os
import requests

import unexefiware.ngsildv1

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
    pilot_list = []

    pilots = os.environ['PILOTS'].split(',')
    for pilot in pilots:
        pilot_list.append(pilot.replace(' ', ''))

    while quitApp is False:
        print('aqua3s:' + os.environ['USERLAYER_BROKER'] +'\n')

        print()
        print('1..View Userlayers')
        print('2..Build Userlayers')
        print('3..Delete Userlayers')

        print('4..Just convert files')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            pilots = os.environ['PILOTS'].split(',')
            for pilot in pilots:
                print(pilot)
                print_resources(os.environ['ALERT_BROKER'], pilot.replace(' ', ''), )
                print()

        if key == '2':
            backlogbuilder.add_user_resources(os.environ['ALERT_BROKER'], pilot_list = pilot_list)

        if key == '3':
            pilots = os.environ['PILOTS'].split(',')
            for pilot in pilots:
                delete_resources(os.environ['ALERT_BROKER'], pilot.replace(' ', ''), )

        if key == '4':
            backlogbuilder.add_user_resources(os.environ['ALERT_BROKER'], pilot_list = pilot_list, create_fiware_resources=False, force_build_files = True)


        if key == 'x':
            quitApp = True
