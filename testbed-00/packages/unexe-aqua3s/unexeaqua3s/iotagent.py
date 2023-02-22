import os
import datetime
import threading
import time
import unexeaqua3s.kibanablelog
import unexeaqua3s.pilot_timezone
import inspect
import unexefiware.ngsildv1
import requests
import copy
import unexeaqua3s.deviceinfo
import unexeaqua3s.device_simulation
import unexeaqua3s.epanomalies

logger = unexeaqua3s.kibanablelog.KibanableLog('IoT Agent')

pilot_list = {}

periodic_update_time = (10) #in seconds

def patch_devices_with_value_data(fiware_service):
    fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.now(unexeaqua3s.pilot_timezone.get(fiware_service)))

    epanomalies = unexeaqua3s.epanomalies.EPAnomalies(fiware_service)
    epanomalies.load_data()

    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service=fiware_service)
    deviceInfo.logger = logger
    deviceInfo.run()

    for device_id in deviceInfo.deviceModelList:
        device = deviceInfo.deviceModelList[device_id]
        unexeaqua3s.device_simulation.create_device_data(fiware_service, device, 'normal', fiware_time, epanomalies)

    unexeaqua3s.workhorse_backend.pilot_update(fiware_service, logger)


def thread_process(pilot):

    print('Starting IoT for: ' + pilot['name'])
    last_period_update = datetime.datetime.strptime('26 Sep 2012', '%d %b %Y')
    while True:
        #do periodic work here
        now = datetime.datetime.utcnow()
        time_diff = (now - last_period_update).total_seconds()

        global periodic_update_time

        if (time_diff >= periodic_update_time):
            #do actual processing
            last_period_update = now
            patch_devices_with_value_data(pilot['name'])

            logger.log(inspect.currentframe(), 'Doing periodic device update:' + pilot['name'])

        #do on-demand work here
        while len(pilot['worklist']) > 0:
            task = pilot['worklist'].pop(0)
            logger.log(inspect.currentframe(),'Doing device update:' + task)

        time.sleep(1)

def on_start():
    pilots = os.environ['PILOTS'].split(',')

    global thread

    for pilot in pilots:
        pilot_list[pilot] = {}
        pilot_list[pilot]['worklist'] = []
        pilot_list[pilot]['name'] = pilot
        pilot_list[pilot]['thread'] = threading.Thread(target=thread_process, args=(pilot_list[pilot],) )

        pilot_list[pilot]['thread'].start()


    logger.log(inspect.currentframe(),'Starting IoT Processor')

def add_task(pilot, task):
    pilot_list[pilot]['worklist'].append(task)



def testbed(fiware_service):
    quitApp = False

    logger = unexefiware.base_logger.BaseLogger()

    while quitApp is False:
        print('\n')
        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])

        print('\n')
        print('1..Create IoT Device Data')


        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            try:
                patch_devices_with_value_data(fiware_service=fiware_service)
            except Exception as e:
                logger.exception(inspect.currentframe(),e)


        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    testbed()
