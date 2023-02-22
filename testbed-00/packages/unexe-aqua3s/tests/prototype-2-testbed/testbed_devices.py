import os

import unexeaqua3s.service_alert
import unexeaqua3s.service_anomaly
import unexeaqua3s.epanet_data_generator

import unexefiware.fiwarewrapper
import unexefiware.fiwarewrapper_debug
import unexefiware.base_logger
import unexefiware.time

import unexeaqua3s.deviceinfo


import unexeaqua3s.json
import datetime
import inspect

from unexeaqua3s import support
import requests

import resourcemanager
import unexefiware.model

def create_property_status(fiware_time, property_name, value, unitCode):
    record = {}

    record[property_name] = {}
    record[property_name]['type'] = "Property"
    record[property_name]['value'] = str(round(value, 2))
    record[property_name]['observedAt'] = fiware_time
    record[property_name]['unitCode'] = unitCode

    return record

def generate_deviceState_ngsildv1(enabled=True):
    record = {'deviceState': {'type': 'Property', 'value': 'Green'}}

    if enabled:
        record['deviceState']['value'] = 'Green'
    else:
        record['deviceState']['value'] = 'Red'

    return record


def create_device(fiware_label):
    record = {}

    record['type'] = 'Device'
    record['@context'] = 'https://schema.lab.fiware.org/ld/context'
    record['id'] = fiware_label

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

    record['deviceState'] = generate_deviceState_ngsildv1()['deviceState']

    record['controlledProperty'] = {}
    record['controlledProperty']['type'] = 'Property'
    record['controlledProperty']['value'] = 'TBD'
    return record

def build_pilot_from_epanet(fiware_wrapper, fiware_service):

    if 'WEBDAV_URL' not in os.environ:
        raise Exception('Webdav not defined')

    options = {
        'webdav_hostname':  os.environ['WEBDAV_URL'],
        'webdav_login': os.environ['WEBDAV_NAME'],
        'webdav_password': os.environ['WEBDAV_PASS']
    }

    resource_manager = resourcemanager.ResouceManager(options=options)
    fiware_service_list = [fiware_service]
    resource_manager.init(url=os.environ['USERLAYER_BROKER'], file_root=os.environ['FILE_PATH']+'/visualiser', fiware_service_list=fiware_service_list)
    resource_manager.has_loaded_content = True

    try:
        timestep_mins = 15
        #timestep_mins = 60*8
        #This may need to be adjusted so simulation always starts on a Friday (i.e. Jan 1, 2021 to matched up with demand)
        now = datetime.datetime.utcnow()
        start_date = datetime.datetime(2022, 4, 29)
        leakdate =now.replace(microsecond=0, second=0, minute=0, hour=6)
        #leakdate = datetime.datetime(year=2022, month=5, day=8, hour=6)  # simulated leak at 6 AM april 5.
        enddate = leakdate + datetime.timedelta(days=2)


        # 1. delete all the existing device data for the pilot
        #support.delete_type_from_broker(os.environ['DEVICE_BROKER'], fiware_service, ['Device'])

        # 2. load up the epanet file for the pilot
        water_network = None
        try:
            water_network = resource_manager.resources[fiware_service]['epanet']
        except Exception as e:
            print('Pilot has no water network!')
            return

        epanet_model = water_network.epanetmodel

        #Load sensor data - still need to add this to webdav but have hard coded it here:
        if fiware_service == 'GT':
            leakID = '3092019_7481'

            sensors = [
                {'ID': 'Moortown_SR.3092019_7230.1','Type': 'flow', 'unitcode': 'G51'},
                {'ID': '3092019_2290.3092019_2348.1','Type': 'flow', 'unitcode': 'G51'},
                {'ID': '3092019_7481','Type': 'pressure', 'unitcode': 'MTR'},
                {'ID': '3092019_2136','Type': 'pressure', 'unitcode': 'MTR'},
                {'ID': '3092019_2604','Type': 'pressure', 'unitcode': 'MTR'},
                {'ID': '3092019_3276','Type': 'pressure', 'unitcode': 'MTR'},
                {'ID': '3092019_2291','Type': 'pressure', 'unitcode': 'MTR'},
                {'ID': '3092019_3276.3092019_3143.1','Type': 'flow', 'unitcode': 'G51'},
                {'ID': '3092019_11921.3092019_2773.1','Type': 'flow', 'unitcode': 'G51'},
                {'ID': '3092019_2612.3092019_2608.1','Type': 'flow','unitcode': 'G51'},
                {'ID': '3092019_10509.3092019_2356.1','Type': 'flow','unitcode': 'G51'},
                {'ID': '3092019_12016.3092019_2136.1','Type': 'flow','unitcode': 'G51'},
                {'ID': '3092019_12045.3092019_1869.1','Type': 'flow','unitcode': 'G51'}
            ]

        else: #Trieste
            leakID = '79'
            sensors = [
                #{'ID': '1', 'Type': 'flow', 'unitcode': 'G51'},
                {'ID': '2', 'Type': 'flow', 'unitcode': 'G51'},
                {'ID': '76', 'Type': 'pressure', 'unitcode': 'MTR'},
                {'ID': '87', 'Type': 'pressure', 'unitcode': 'MTR'},
                {'ID': '94', 'Type': 'pressure', 'unitcode': 'MTR'},
                {'ID': '97', 'Type': 'pressure', 'unitcode': 'MTR'},
                {'ID': '103', 'Type': 'pressure', 'unitcode': 'MTR'},
                {'ID': '32', 'Type': 'flow', 'unitcode': 'G51'},
                {'ID': '9', 'Type': 'flow', 'unitcode': 'G51'},
                {'ID': '28', 'Type': 'flow', 'unitcode': 'G51'}
            ]

        # 3. Run simulation grab readings for sensors
        simulation_model = unexeaqua3s.epanet_data_generator.simulation_model(epanet_model, sensors)
        df = simulation_model.simulate_leak(stepDuration=int(timestep_mins*60),
                                            leakID = leakID,
                                            leakEmitter=5,
                                            start_date= start_date,
                                            end_date= enddate,
                                            leakdate = leakdate
                                            )


        # 4. Create devices for each sensor:
        for sensor in simulation_model.sensors:
            if sensor['Type'] == "pressure":
                component = water_network.fiware_component['Junction'][sensor['Index']-1] # minus 1 due to list conatation
                if fiware_service == 'GT':
                    coordinates = [component['location']['value']['coordinates'][0], component['location']['value']['coordinates'][1]]
                else:
                    coordinates = [component['location']['value']['coordinates'][1], component['location']['value']['coordinates'][0]]
            if sensor['Type'] == "flow":
                component = water_network.fiware_component['Pipe'][sensor['Index']-1] # minus 1 due to list conatation
                #weird list format depending on # of vertices - could cause error when 2 vertices exist - should be rewritten
                if 'vertices' in component.keys():
                    if len(component['vertices']['value']['coordinates']) > 2:
                      middle_coordinate = len(component['vertices']['value']['coordinates'])//2 #two dashes rounds down
                      if fiware_service == 'GT':
                          coordinates = [component['vertices']['value']['coordinates'][middle_coordinate][0],
                                         component['vertices']['value']['coordinates'][middle_coordinate][1]]
                      else:
                        coordinates = [component['vertices']['value']['coordinates'][middle_coordinate][1],
                                      component['vertices']['value']['coordinates'][middle_coordinate][0]]

                    else:
                        if fiware_service == 'GT':
                            coordinates = [component['vertices']['value']['coordinates'][0],
                                           component['vertices']['value']['coordinates'][1]]
                        else:
                            coordinates = [component['vertices']['value']['coordinates'][1],
                                       component['vertices']['value']['coordinates'][0]]
                else:
                    startID = component['startsAt']['object']
                    endID = component['endsAt']['object']
                    startPos = water_network.get_coordinates_from_id(startID)
                    endPos = water_network.get_coordinates_from_id(endID)
                    if fiware_service == 'GT':
                        middle_coordinate_y=(startPos[1]+endPos[1])/2
                        middle_coordinate_x=(startPos[0]+endPos[0])/2
                        coordinates = [middle_coordinate_x, middle_coordinate_y]
                    else:
                        middle_coordinate_x=(startPos[1]+endPos[1])/2
                        middle_coordinate_y=(startPos[0]+endPos[0])/2
                        coordinates = [middle_coordinate_x, middle_coordinate_y]

            # create initial data
            current_time = start_date + datetime.timedelta(minutes=timestep_mins) #initial start time
            fiware_time = unexefiware.time.datetime_to_fiware(current_time)

            name = sensor['ID']
            name = name.replace(".", "__")
            device_id = 'urn:ngsi-ld:Device:UNEXE_TEST_' + name
            device_record = create_device(device_id)

            property = 'epanet_'+ sensor['Type']
            property_unitcode = sensor['unitcode']
            property_value =df.loc[(df['Sensor_ID'] == sensor['ID']) &
                   (df['ReportTime'] == current_time)]['Read_noise'].values[0]

            device_record['epanet_reference'] = {}
            device_record['epanet_reference']['type'] = 'Property'
            device_record['epanet_reference']['value'] = str(sensor['ID'])

            device_record['name']['value'] = name
            device_record['location']['value']['coordinates'] = coordinates
            device_record['controlledProperty']['value'] = sensor['Type']
            device_record['value'] =  create_property_status(fiware_time, property, property_value, property_unitcode)[property]

            # create initial data for the device instance using create
            # this is the oldest record in orion/cygnus and needs to contain valid data

            fiware_wrapper.delete_instance(device_record['id'],service=fiware_service, link=device_record['@context'])
            fiware_wrapper.create_instance(entity_json=device_record, service=fiware_service, link=device_record['@context'])

            current_time = current_time + datetime.timedelta(minutes=timestep_mins)

            batch_patch = False

            if '0.0.0.0' in os.environ['DEVICE_HISTORIC_BROKER']:
                batch_patch = True

            if batch_patch:
                patch_list = []
                device_record = fiware_wrapper.get_entity(device_id, fiware_service)
                while current_time < now:
                    fiware_time = unexefiware.time.datetime_to_fiware(current_time)

                    # generate device state data
                    patch_data = generate_deviceState_ngsildv1(enabled=True)

                    # gareth - only do patch if the data has changed
                    if device_record['deviceState']['value'] != patch_data['deviceState']['value']:
                        patch_list.append(patch_data)

                    if patch_data['deviceState']['value'] == 'Green':
                        # generate device prop data
                        # but only if the deviceState is Green
                        if 'controlledProperty' in device_record:
                            property_label = 'value'
                            property_value = df.loc[(df['Sensor_ID'] == sensor['ID']) &
                                                    (df['ReportTime'] == current_time)]['Read_noise'].values[0]

                            patch_data = create_property_status(fiware_time, property_label, property_value, property_unitcode)
                            patch_list.append(patch_data)

                    current_time = current_time + datetime.timedelta(minutes=timestep_mins)

                fiware_wrapper.patch_entity(device_record['id'], patch_list, service=fiware_service)

            else:
                session = requests.session()

                while current_time < now:

                    fiware_time = unexefiware.time.datetime_to_fiware(current_time)
                    device_record = fiware_wrapper.get_entity(device_id, fiware_service)

                    print(str(fiware_time) + ' ' + device_record['id'])

                    # generate device state data
                    patch_data = generate_deviceState_ngsildv1(enabled=True)

                    # gareth - only do patch if the data has changed
                    deviceState = unexefiware.model.get_property_value(device_record, 'deviceState')

                    if deviceState != patch_data['deviceState']['value']:
                        fiware_wrapper.patch_entity(device_id, patch_data, service=fiware_service)

                    if deviceState == 'Green':
                        # generate device prop data
                        # but only if the deviceState is Green
                        if unexefiware.model.get_property_value(device_record, 'controlledProperty') != None:
                            try:
                                property_label = 'value'

                                property_value = df.loc[(df['Sensor_ID'] == sensor['ID']) &
                                                        (df['ReportTime'] == current_time)]['Read_noise'].values[0]

                                patch_data = create_property_status(fiware_time, property_label, property_value, property_unitcode)

                                if 'CYGNUS_HACK_ADDRESS' in os.environ:
                                    #do hacky add data to cygnus approach
                                    gnarly_cygnus_data = {}
                                    gnarly_cygnus_data['notifiedAt'] = unexefiware.time.datetime_to_fiware(datetime.datetime.utcnow())

                                    record = {}
                                    record['id'] = device_record['id']
                                    record['type'] = device_record['type']
                                    record['value'] = patch_data['value']
                                    record['@context'] = device_record['@context']

                                    record['dateLastValueReported']= {
                                        "type": "Property",
                                        "value": {
                                            "@type": "DateTime",
                                            "@value": fiware_time
                                        }
                                    }

                                    gnarly_cygnus_data['data'] = [record]

                                    try:
                                        headers = {}
                                        headers['Content-Type'] = 'application/json'

                                        if fiware_service:
                                            headers['fiware-service'] = fiware_service

                                        path = os.environ['CYGNUS_HACK_ADDRESS']

                                        r = session.post(path, data=unexeaqua3s.json.dumps(gnarly_cygnus_data), headers=headers, timeout=100)

                                        if not r.ok:
                                            logger = unexefiware.base_logger.BaseLogger()
                                            logger.fail(inspect.currentframe(), 'Failed to hack cygnus')

                                    except Exception as e:
                                        logger = unexefiware.base_logger.BaseLogger()
                                        logger.exception(inspect.currentframe(), e)

                                #and patch it normally ...
                                result = fiware_wrapper.patch_entity(device_record['id'], patch_data, service=fiware_service)

                                print()
                            except Exception as e:
                                logger = unexefiware.base_logger.BaseLogger()
                                logger.exception(inspect.currentframe(), e)

                    current_time = current_time + datetime.timedelta(minutes=timestep_mins)

    except Exception as e:
        logger = unexefiware.base_logger.BaseLogger()
        logger.exception(inspect.currentframe(),e)

def testbed(fiware_wrapper, fiware_service):

    quitApp = False

    while quitApp is False:
        print('aqua3s:' + '\n')

        device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
        alert_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['ALERT_BROKER'], historic_url=os.environ['ALERT_HISTORIC_BROKER'])
        deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
        deviceInfo.run()

        support.print_devices(deviceInfo)

        print()
        print('1..Build Devices from EPANET')
        print('3..Print Pilots / Devices')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            try:
                build_pilot_from_epanet(fiware_wrapper, fiware_service)
            except Exception as e:
                logger = unexefiware.base_logger.BaseLogger()
                logger.exception(inspect.currentframe(),e)


        if key == '3':
            device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            alert_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['ALERT_BROKER'], historic_url=os.environ['ALERT_HISTORIC_BROKER'])
            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper,other_wrapper=None)
            deviceInfo.run()

            for device_id in deviceInfo.deviceInfoList:
                print(device_id)

        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    logger = unexefiware.base_logger.BaseLogger()

    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    fiware_wrapper.init(logger=logger)
    fiware_service = 'GT'

    testbed(fiware_wrapper, fiware_service)
