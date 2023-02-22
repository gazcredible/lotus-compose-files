import os

import unexeaqua3s.deviceinfo
import unexeaqua3s.epanomalies
import inspect



def create_device_data(fiware_service:str, device:unexeaqua3s.deviceinfo.DeviceSmartModel, state:str, fiware_time:str, epanomalies:unexeaqua3s.epanomalies.EPAnomalies):

    if device.get_id() == 'urn:ngsi-ld:Device:UNEXE_TEST_28':
        print()

    if state == 'offline':
        # do stuff
        if device.deviceState() == 'Green' or device.deviceState() == 'unclear':
            device.deviceState_set('Red')
            device.deviceState_patch(fiware_service)
        else:
            # do nothing
            pass
    else:
        # is online
        if device.deviceState() == 'Red' or device.deviceState() == 'unclear':
            device.deviceState_set('Green')
            device.deviceState_patch(fiware_service)
        else:
            # do nothing
            pass

        # update the value
        value = device.model['value']['value']

        if state == 'normal':

            try:
                if device.isEPANET():
                    value = epanomalies.get_device_prop_value(device.EPANET_id(), device.property_observedAt(), in_range=True)
                else:
                    anomaly_values = device.get_anomaly_raw_values(fiware_time, lerp=True)
                    value = float(anomaly_values['average'])
            except Exception as e:
                unexeaqua3s.deviceinfo.logger.exception(inspect.currentframe(), e)

        if state == 'alert':
            try:
                value_min = float(device.alertsetting_get_entry('current_min'))
                value_max = float(device.alertsetting_get_entry('current_max'))
            except Exception as e:
                value_min = -9000
                value_max = 9000

            value = value_max * 1.10

        if state == 'anomaly':
            value = device.get_anomaly_value(fiware_time)

        if state == 'epanomaly':
            # do stuff
            if device.isEPANET():
                # do stuff
                device.epanomaly_fudge_setting(fiware_service, True)

                value = float(device.alertsetting_get_entry('current_max'))*0.99
                #value = epanomalies.get_device_prop_value(device.EPANET_id(), device.property_observedAt(), in_range=False)

        else:
            if device.isEPANET():
                device.epanomaly_fudge_setting(fiware_service, False)

        if 'IOTAGENT_WRITE_TO_FIWARE' in os.environ:
            if os.environ['IOTAGENT_WRITE_TO_FIWARE'].lower() == 'true':
                device.model['value']['value'] = device.print_with_dp(value)
                device.value_patch(fiware_service, fiware_time)
        else:
            device.model['value']['value'] = device.print_with_dp(value)
            device.value_patch(fiware_service, fiware_time)
