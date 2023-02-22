import local_environment_settings
import os


import testbed_devices
import testbed_alerts
import testbed_anomalies
import testbed_visualisation_service
import testbed_userlayer
import testbed_broker
import testbed_mailing
import testbed_workhouse
import testbed_deviceinfo2
import testbed_anomalies_epanet
import testbed_IMM

import unexefiware.fiwarewrapper
import unexefiware.fiwarewrapper_debug
import unexefiware.base_logger
import unexefiware.time

import unexeaqua3s.deviceinfo
import testbed_localization

import unexeaqua3s.IMM_PI

import geopandas
import unexeaqua3s.json

def testbed():
    quitApp = False

    logger = unexefiware.base_logger.BaseLogger()


    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    fiware_wrapper.init(logger=logger)
    fiware_service = 'AAA'
    fiware_service = 'SOF'
    fiware_service = 'TTT'
    fiware_service = os.environ['PILOTS']

    my_broker = unexeaqua3s.brokerdefinition.BrokerDefinition()
    my_broker.init(fiware_wrapper)

    alert_init_data = {'orion_broker': fiware_wrapper.url, 'drop_tables': 'True', 'fiware_service': fiware_service}

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])
        print('ALERT_BROKER:  ' + os.environ['ALERT_BROKER'])

        print('\n')
        print('0..Visualisation Service')
        print('1..Devices')
        print('2..Mailing')
        print('3..Alert Settings')
        print('4..Anomaly Settings')
        print('5..Workhouse Settings')
        print('6..Userlayer Settings')
        print('7..Gareth\'s terrible shapefile code' )
        print('7a..EPANET anomalies')
        print('8..A&A Settings')
        print('9..Broker Settings')
        print('10..DeviceInfo2')
        print('10a..Localise leak')
        print('11..Processor Server:' + os.environ['PROCESSOR_SERVER'])
        print('12..IMM Testbed' + os.environ['PROCESSOR_SERVER'])
        print('13..Scenario')


        print('X..Back')
        print('\n')

        key = input('>')

        if key == '0':
            testbed_visualisation_service.testbed()

        if key == '1':
            testbed_devices.testbed(fiware_wrapper, fiware_service)

        if key == '2':
            testbed_mailing.testbed(fiware_service)

        if key == '3':
            testbed_alerts.testbed(fiware_wrapper, fiware_service)

        if key == '4':
            testbed_anomalies.testbed(fiware_wrapper, fiware_service)

        if key == '5':
            testbed_workhouse.testbed(fiware_service = fiware_service)

        if key == '6':
            testbed_userlayer.testbed(fiware_wrapper, fiware_service)

        if key == '7':
            source_filepath = '/home/gareth/Documents/dev/exeter/aqua3s/aqua3s-prototype-2/packages/unexe-aqua3s/tests/prototype-2-testbed/data/shapefiles/ISONZO_TR300_WGS84.shp'
            localdestfilepath = '/home/gareth/Documents/dev/exeter/aqua3s/aqua3s-prototype-2/packages/unexe-aqua3s/tests/prototype-2-testbed/data/ISONZO_TR300_WGS84.geojson'

            myshpfile = geopandas.read_file(source_filepath)
            myshpfile.to_file(localdestfilepath, driver='GeoJSON')

        if key == '7a':
            testbed_anomalies_epanet.testbed(fiware_service)

        if key == '8':
            #testbed_aanda.testbed(fiware_service)
            pass

        if key == '9':
            testbed_broker.testbed()

        if key == '10':
            testbed_deviceinfo2.testbed(fiware_service)

        if key == '10a':
            testbed_localization.testbed(fiware_service)

        if key == '11':
            #testbed_processor_server.testbed()
            pass

        if key == '12':
            testbed_IMM.testbed(fiware_wrapper, fiware_service)
            #unexeaqua3s.IMM_PI.testbed(fiware_service)

        if key == '13':
            #testbed_scenario.testbed(fiware_wrapper, fiware_service)
            pass


    if key == 'x':
            quitApp = True

if __name__ == '__main__':
    testbed()
