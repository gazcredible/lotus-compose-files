import unexeaqua3s.resourcebuilder
import unexeaqua3s.fiwareresources

import unexeaqua3s.service_alert
import unexeaqua3s.service_anomaly

import unexeaqua3s.service_chart

from unexeaqua3s import support


def testbed(fiware_wrapper, fiware_service):
    quitApp = False
    current_service = fiware_service

    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=support.device_wrapper, other_wrapper=support.alert_wrapper)
    deviceInfo.run()

    while quitApp is False:
        print('aqua3s:' + fiware_wrapper.url + ' pilot:' + current_service + '\n')

        print('1..Build Charting Data')
        print('2..Update Charting Data')
        print('3..Get properties by sensor')
        print('4..Get sensors by property')
        print('9..Update DeviceInfo')


        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            chartingService = unexeaqua3s.service_chart.ChartService()
            chartingService.build_from_deviceInfo(deviceInfo)

        if key == '2':
            chartingService = unexeaqua3s.service_chart.ChartService()
            chartingService.update(deviceInfo, write_to_broker=True, force_process=True)


        if key == '3':
            chartingService = unexeaqua3s.service_chart.ChartService()
            result = chartingService.get_properties_by_sensor(deviceInfo, unexeaqua3s.service_chart.chart_modes[0])


            #print(unexeaqua3s.json.dumps(result, indent=4) )

        if key == '4':
            chartingService = unexeaqua3s.service_chart.ChartService()
            result = chartingService.get_sensor_by_properties(deviceInfo, unexeaqua3s.service_chart.chart_modes[3], 'pressure')

            #print(unexeaqua3s.json.dumps(result, indent=4) )

        if key == '9':
            deviceInfo.run()


        if key == 'x':
            quitApp = True


if __name__ == '__main__':
    testbed()
