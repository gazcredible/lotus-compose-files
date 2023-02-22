import unexefiware.base_logger
import os
import requests
import unexeaqua3s.json
import unexefiware.fiwarewrapper

import requests
import os
import unexeaqua3s.json
import inspect

import unexeaqua3s.kibanablelog


def pilot_device_update(fiware_service:str, logger=None) -> bool:
    try:
        headers = {}
        headers['Content-Type'] = 'application/ld+json'
        headers['fiware-service'] = fiware_service
        session = requests.session()

        path = os.environ['VISUALISER'] + '/pilot_device_update'
        payload = {}

        r = session.post(path, data=unexeaqua3s.json.dumps(payload), headers=headers, timeout=10)

        return r.ok
    except Exception as e:
        if logger:
            logger.exception(inspect.currentframe(), e )

    return False


def testbed(fiware_service):
    quitApp = False

    while quitApp is False:
        print('\nVisualiser Testbed')

        print('\n')
        print('1..' + 'pilot_device_update:' + os.environ['VISUALISER'])
        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            pilot_device_update(fiware_service, unexeaqua3s.kibanablelog.KibanableLog('Visualiser.Testbed'))

        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    testbed('AAA')

