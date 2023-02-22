import os
from unexeaqua3s import support


def testbed():
    quitApp = False

    fiware_service = 'AAA'

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])
        print('ALERT_BROKER:  ' + os.environ['ALERT_BROKER'])

        print('\n')
        print('1..Delete Broker')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            support.device_wrapper.erase_broker()
            support.alert_wrapper.erase_broker()




        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    testbed()
