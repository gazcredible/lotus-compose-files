import local_environment_settings
import os

import testbed_devices
import testbed_broker
import testbed_fiwareresources
import unexeaqua3s.iotagent

import unexeaqua3s.visualiser
import unexeaqua3s.workhorse_backend
import unexeaqua3s.service_chart

import unexefiware.fiwarewrapper
import unexefiware.fiwarewrapper_debug
import unexefiware.base_logger
import unexefiware.time

import unexeaqua3s.IMM_PI_MO

import unexeaqua3s.deviceinfo
import unexeaqua3s.mailing_service

def testbed():
    quitApp = False

    logger = unexefiware.base_logger.BaseLogger()

    fiware_service = 'AAA'
    #fiware_service = 'EYA'
    #fiware_service = 'BDI'
    #fiware_service = 'VVQ'

    #fiware_service = 'SOF'
    #fiware_service = 'WBL'
    fiware_service = 'GUW'
    fiware_service = 'TTT'

    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    fiware_wrapper.init(logger=logger)

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])

        print('\n')
        print('1..Devices')
        print('2..Broker')
        print('3..DeviceInfo2')
        print('4..User Layers & EPANET')
        print('5..IoTAgent')
        print('6..Charting')
        print('7..Workhorse')
        print('8..Visualiser')
        print('9..IMM')
        print('0..Mailing')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            testbed_devices.testbed(fiware_service)

        if key == '2':
            testbed_broker.testbed(fiware_wrapper, fiware_service)

        if key == '3':
            unexeaqua3s.deviceinfo.testbed(fiware_service = fiware_service)

        if key == '4':
            testbed_fiwareresources.testbed(fiware_wrapper = fiware_wrapper, fiware_service = fiware_service)

        if key == '5':
            unexeaqua3s.iotagent.testbed(fiware_service = fiware_service)

        if key == '6':
            unexeaqua3s.service_chart.testbed(fiware_service = fiware_service)

        if key == '7':
            unexeaqua3s.workhorse_backend.testbed(fiware_service=fiware_service)

        if key == '8':
            unexeaqua3s.visualiser.testbed(fiware_service=fiware_service)

        if key == '9':
            unexeaqua3s.IMM_PI_MO.testbed(fiware_service)

        if key == '0':
            unexeaqua3s.mailing_service.testbed(fiware_service)

        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    testbed()
