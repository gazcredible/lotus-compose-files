import local_environment_settings
import os

import testbed_userlayer
import unexefiware.fiwarewrapper
import unexefiware.fiwarewrapper_debug
import unexefiware.base_logger
import unexefiware.time
import unexeaqua3s.webdav

import imm.immwrapper_mo
import unexe_epanet.epasim
import anomalies.testbed
import testbed_lotus

def testbed():
    quitApp = False

    logger = unexefiware.base_logger.BaseLogger()


    fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    fiware_wrapper.init(logger=logger)


    #fiware_service = 'GUW'
    fiware_service = 'AAA'

    alert_init_data = {'orion_broker': fiware_wrapper.url, 'drop_tables': 'True', 'fiware_service': fiware_service}

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'] + ' ' + fiware_service)


        print('\n')
        print('0..SIM UI')
        print('1..Device Settings')
        print('6..Userlayer Settings')
        print('11..IMM testbed')
        print('22..EPASIM testbed')
        print('33..Anomaly testbed')


        print('X..Back')
        print('\n')

        key = input('>')

        if key == '0':
            testbed_lotus.testbed()

        if key == '1':
            testbed_device.testbed(fiware_service)

        if key == '6':
            testbed_userlayer.testbed(fiware_wrapper, fiware_service)

        if key == '11':
            imm.immwrapper_mo.testbed(fiware_service)

        if key == '22':
            unexe_epanet.epasim.testbed(fiware_service)

        if key == '33':
            anomalies.testbed.testbed(fiware_service)

    if key == 'x':
            quitApp = True

if __name__ == '__main__':
    testbed()
