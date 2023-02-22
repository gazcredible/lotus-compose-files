import os
import datetime

from unexeaqua3s import support
import unexefiware.time
import unexeaqua3s.deviceinfo
import unexeaqua3s.service_alert
import unexeaqua3s.service_anomaly

def testbed(fiware_service):
    quitApp = False

    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=support.device_wrapper, other_wrapper=support.alert_wrapper)
    deviceInfo.run()

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])
        print('ALERT_BROKER:  ' + os.environ['ALERT_BROKER'])

        print('\n')
        print('1..Process Alerts')
        print('2..Process Anomalies')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            try:
                #for a device, get all the historic sensor data and compare with historic alert status data
                processor = unexeaqua3s.service_alert.AlertService()

                now = datetime.datetime.utcnow()
                fiware_time = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))

                processor.lumpyprocess(deviceInfo, fiware_time)
            except Exception as e:
                print(str(e))

        if key == '2':
            try:
                #for a device, get all the historic sensor data and compare with historic anomaly status data
                processor = unexeaqua3s.service_anomaly.AnomalyService()

                now = datetime.datetime.utcnow()
                fiware_time = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))

                processor.lumpyprocess(deviceInfo, fiware_time)
            except Exception as e:
                print(str(e))



        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    testbed()
