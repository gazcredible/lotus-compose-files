import os
import unexefiware.fiwarewrapper
import unexeaqua3s.deviceinfo

def testbed(fiware_service):
    quitApp = False

    while quitApp is False:
        print('\nDeviceInfo Testbed')

        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])
        print('ALERT_BROKER:  ' + os.environ['ALERT_BROKER'])

        print('\n')
        print('1..Run DeviceInfo' + ' ' + fiware_service)
        print('2..Run DeviceInfo2' + ' ' + fiware_service)


        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            alert_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['ALERT_BROKER'], historic_url=os.environ['ALERT_HISTORIC_BROKER'])
            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
            deviceInfo.run()

            print('Took: '+str(deviceInfo.execution_time))

        if key == '2':
            device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            alert_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['ALERT_BROKER'], historic_url=os.environ['ALERT_HISTORIC_BROKER'])
            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
            deviceInfo.run2()

            print('Took: ' + str(deviceInfo.execution_time))



        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    testbed()


