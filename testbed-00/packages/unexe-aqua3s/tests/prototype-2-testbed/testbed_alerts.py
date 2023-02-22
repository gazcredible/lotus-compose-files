import unexeaqua3s.deviceinfo
import unexeaqua3s.service_alert
import datetime
import unexefiware.time
import os
from unexeaqua3s import support


def print_device_info2(deviceInfo, device_id,service):
    text = ''

    text += device_id.ljust(30, ' ')
    text += ' '
    text += deviceInfo.device_name(device_id).ljust(30, ' ')
    text += ' '

    text += deviceInfo.property_prettyprint(device_id).ljust(16, ' ')
    text += ' '
    text += deviceInfo.property_value_prettyprint(device_id).rjust(8, ' ')
    text += ' '
    text += deviceInfo.property_observedAt(device_id)

    text += ' '
    text += deviceInfo.device_status(device_id).ljust(6, ' ')

    text += ' Anomaly: '
    text += ('Count:'  + str(deviceInfo._get_value_entry(device_id, unexeaqua3s.deviceinfo.anomalyStatus_label, 'count'))).ljust(10, ' ')
    text += ' '
    text += ('State:' + str(deviceInfo._get_value_entry(device_id, unexeaqua3s.deviceinfo.anomalyStatus_label, 'state'))).ljust(20, ' ')

    text += ' Alert: '
    text += ('T:' + str(deviceInfo.alert_isTriggered(device_id)) + ' ' + str(deviceInfo.alertstatus_reason_prettyprint(device_id))).ljust(30, ' ')

    return text



class AlertSettingUI:
    def __init__(self):
        pass
    def doStuff(self, title, deviceInfo, service):
        quitApp = False

        while quitApp is False:
            print(title)
            print()
            print(service)

            i = 1
            key_list = list(deviceInfo.deviceInfoList.keys())

            for device_id in key_list:
                text = ''
                text += str(i).ljust(3, ' ') + '..'
                text += device_id
                text += str(deviceInfo.alertsetting_get(device_id))

                print(text)
                i += 1

            print('X..Back')
            print('\n')

            key = input('>')

            if key == 'x':
                quitApp = True
            else:
                try:
                    key_to_index = int(key) - 1

                    if key_to_index >= 0 and key_to_index < len(key_list):
                        self.onAction(deviceInfo, service, key_list[key_to_index])

                except Exception as e:
                    pass
    def onAction(self,deviceInfo, service, current_device):
        pass

class alertsetting_numeric_value(AlertSettingUI):
    def __init__(self, label, reduce = True):
        super().__init__()

        self.reduce = reduce
        self.label = label

    def doStuff(self, deviceInfo, service):
        super().doStuff(self.label, deviceInfo,service)

    def onAction(self,deviceInfo, service, current_device):
        current_value = float(deviceInfo.alertsetting_get_entry(current_device,self.label))
        step = float(deviceInfo.alertsetting_get_entry(current_device, 'step'))

        new_value = 0

        if self.reduce:
            new_value = current_value - step
        else:
            new_value = current_value + step

        now = datetime.datetime.utcnow()
        fiware_time = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))

        deviceInfo.alertsetting_set_entry(current_device, self.label, str(round(new_value, 2)))
        deviceInfo.alertsetting_patch(current_device, fiware_time)

class alertsetting_active_toggle(AlertSettingUI):
    def __init__(self):
        super().__init__()

    def onAction(self,deviceInfo, service, current_device):
        current_value = deviceInfo.alertsetting_get_entry(current_device,'active')

        if current_value == 'True':
            current_value = 'False'
        else:
            current_value = 'True'

        deviceInfo.alertsetting_set_entry(current_device,'active',current_value)

        now = datetime.datetime.utcnow()
        fiware_time = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))

        deviceInfo.alertsetting_patch(current_device, fiware_time)

class alertsetting_set_value(AlertSettingUI):
    def __init__(self, label):
        super().__init__()

        self.label = label

    def doStuff(self, deviceInfo, service):
        super().doStuff(self.label, deviceInfo,service)

    def onAction(self,deviceInfo, service, current_device):
        value = input('Enter Value>')

        if value != 'x':
            deviceInfo.alertsetting_set_entry(current_device, self.label, value)

            now = datetime.datetime.utcnow()
            fiware_time = unexefiware.time.datetime_to_fiware(now.replace(microsecond=0))

            deviceInfo.alertsetting_patch(current_device, fiware_time)


def testbed(fiware_wrapper, fiware_service):
    quitApp = False


    device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    alert_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['ALERT_BROKER'], historic_url=os.environ['ALERT_HISTORIC_BROKER'])
    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
    deviceInfo.run()

    current_device = None

    key_list = list(deviceInfo.deviceInfoList.keys())
    key_list = sorted(key_list)

    if len(key_list) > 0:
        current_device = key_list[0]

    while quitApp is False:
        print('aqua3s:' + os.environ['ALERT_BROKER'] + ' pilot:' + fiware_service + '\n')

        support.print_devices(deviceInfo)
        print('')

        print()
        print('1..Alert Current Min - Reduce')
        print('2..Alert Current Min - Increase')
        print('3..Alert Current Max - Reduce')
        print('4..Alert Current Max - Increase')
        print('5..Alert Current Min - Set')
        print('6..Alert Current Max - Set')
        print('7..Active - Toggle')
        print('8..Process Alerts')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            opt = alertsetting_numeric_value(label = 'current_min', reduce=True)
            opt.doStuff(deviceInfo, fiware_service)

        if key == '2':
            opt = alertsetting_numeric_value(label = 'current_min',reduce=False)
            opt.doStuff(deviceInfo, fiware_service)

        if key == '3':
            opt = alertsetting_numeric_value(label = 'current_max', reduce=True)
            opt.doStuff(deviceInfo, fiware_service)

        if key == '4':
            opt = alertsetting_numeric_value(label = 'current_max',reduce=False)
            opt.doStuff(deviceInfo, fiware_service)

        if key == '5':
            opt = alertsetting_set_value(label = 'current_min')
            opt.doStuff(deviceInfo, fiware_service)

        if key == '6':
            opt = alertsetting_set_value(label = 'current_max')
            opt.doStuff(deviceInfo, fiware_service)

        if key == '7':
            opt = alertsetting_active_toggle()
            opt.doStuff('Active Toggle', deviceInfo, fiware_service)

        if key == '8':
            alertService = unexeaqua3s.service_alert.AlertService()
            alertService.update(deviceInfo)

        if key == 'x':
            quitApp = True