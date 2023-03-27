import copy
import os
import threading
import time

import requests
import unexefiware.ngsildv1
import unexefiware.model
import datetime
import inspect
import unexeaqua3s.json
import unexeaqua3s.support
import unexeaqua3s.deviceinfo
import unexefiware.base_logger
import pytz
import unexeaqua3s.pilot_timezone

import unexeaqua3s.service_anomaly
import unexeaqua3s.visualiser
import unexeaqua3s.epanomalies
import unexeaqua3s.mailing_service

#GARETH - this (workhorse) should be about processing device data and not doing 'stuff'
#POST commands
command_device_update = 'device_update'
command_pilot_update = 'pilot_update'
command_rebuild_charts = 'rebuild_charts'
command_build_userlayer_references = 'build_userlayer_references'
command_rebuild_anomaly_settings = 'command_rebuild_anomaly_settings'
command_post_certh_alert = 'command_post_certh_alert'

#GET commands
command_get_giota_data = 'command_get_giota_data'
command_get_anomaly_data = 'command_get_anomaly_data'

leaky_devices = ['urn:ngsi-ld:Device:UNEXE_TEST_76']

current_leak_status = False

def create_property_status(fiware_time, property_name, value, unitCode):
    record = {}

    record[property_name] = {}
    record[property_name]['type'] = "Property"
    record[property_name]['value'] = str(round(value, 2))
    record[property_name]['observedAt'] = fiware_time
    record[property_name]['unitCode'] = unitCode

    return record

def get_device_anomaly_text(device_id):
    global current_leak_status

    anomaly_result = {}

    if current_leak_status  and device_id in leaky_devices:
        anomaly_result['triggered'] = 'True'
        anomaly_result['reason'] = 'Out of Range!'

    else:
        anomaly_result['triggered'] = 'False'
        anomaly_result['reason'] = 'Everything is fine'

    return anomaly_result


def patch_device(session, fiware_service, device_record, fiware_time, leak_status=False):

    try:
        property_label = 'value'

        global leaky_devices
        if leak_status == True and device_record['id'] in leaky_devices:
            property_value = 0
        else:
            property_value = 100

        property_unitcode = 'G51'
        try:
            property_unitcode = device_record['value']['unitCode']
        except Exception as e:
            pass

        patch_data = create_property_status(fiware_time, property_label, property_value, property_unitcode)

        if 'CYGNUS_HACK_ADDRESS' in os.environ:
            # do hacky add data to cygnus approach
            gnarly_cygnus_data = {}
            gnarly_cygnus_data['notifiedAt'] = fiware_time

            record = {}
            record['id'] = device_record['id']
            record['type'] = device_record['type']
            record['value'] = patch_data['value']
            record['@context'] = device_record['@context']

            record['dateLastValueReported'] = {
                "type": "Property",
                "value": {
                    "@type": "DateTime",
                    "@value": fiware_time
                }
            }

            gnarly_cygnus_data['data'] = [record]

            try:
                headers = {}
                headers['Content-Type'] = 'application/json'

                if fiware_service:
                    headers['fiware-service'] = fiware_service

                path = os.environ['CYGNUS_HACK_ADDRESS']

                r = session.post(path, data=unexeaqua3s.json.dumps(gnarly_cygnus_data), headers=headers, timeout=100)

                if not r.ok:
                    logger = unexefiware.base_logger.BaseLogger()
                    logger.fail(inspect.currentframe(), 'Failed to hack cygnus')

            except Exception as e:
                logger = unexefiware.base_logger.BaseLogger()
                logger.exception(inspect.currentframe(), e)

        # and patch it normally ...
        fiware_wrapper =unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
        result = fiware_wrapper.patch_entity(device_record['id'], patch_data, service=fiware_service)

    except Exception as e:
        logger = unexefiware.base_logger.BaseLogger()
        logger.exception(inspect.currentframe(), e)

def patch_device2(session, fiware_service, device_record, fiware_time, patch_data):

    try:
        property_label = 'value'

        if ('CYGNUS_HACK_ADDRESS' in os.environ) and ('observedAt' in patch_data):
            # do hacky add data to cygnus approach
            gnarly_cygnus_data = {}
            gnarly_cygnus_data['notifiedAt'] = fiware_time

            record = {}
            record['id'] = device_record['id']
            record['type'] = device_record['type']
            record['value'] = patch_data['value']
            record['@context'] = device_record['@context']

            record['dateLastValueReported'] = {
                "type": "Property",
                "value": {
                    "@type": "DateTime",
                    "@value": fiware_time
                }
            }

            gnarly_cygnus_data['data'] = [record]

            try:
                headers = {}
                headers['Content-Type'] = 'application/json'

                if fiware_service:
                    headers['fiware-service'] = fiware_service

                path = os.environ['CYGNUS_HACK_ADDRESS']

                r = session.post(path, data=unexeaqua3s.json.dumps(gnarly_cygnus_data), headers=headers, timeout=100)

                if not r.ok:
                    logger = unexefiware.base_logger.BaseLogger()
                    logger.fail(inspect.currentframe(), 'Failed to hack cygnus')

            except Exception as e:
                logger = unexefiware.base_logger.BaseLogger()
                logger.exception(inspect.currentframe(), e)

        # and patch it normally ...
        fiware_wrapper =unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
        result = fiware_wrapper.patch_entity(device_record['id'], patch_data, service=fiware_service)

    except Exception as e:
        logger = unexefiware.base_logger.BaseLogger()
        logger.exception(inspect.currentframe(), e)


class PilotProcessor:
    def __init__(self, debug = False, do_automatic_updates = False):
        self.command_list = []
        self.charting_command_list = []
        self.logger = None
        self.last_charting = None
        self.fiware_service = None

        self.disable_updates = False
        self.debug = debug

        self.epanomalies = None
        self.alert_mailing = None

        #GARETH - this stops the system from doing periodic updates
        self.do_automatic_updates = do_automatic_updates


    def init(self, fiware_service, logger=None):
        self.logger = logger

        if self.logger == None:
            self.logger = unexefiware.base_logger.BaseLogger()

        self.fiware_service = fiware_service

        self.epanomalies = unexeaqua3s.epanomalies.EPAnomalies(fiware_service)
        self.epanomalies.load_data()

        self.alert_mailing = unexeaqua3s.mailing_service.Mailservice()
        self.alert_mailing.logger = self.logger
        self.alert_mailing.init(self.fiware_service)

        if self.debug:
            pass
        else:
            self.main_thread = threading.Thread(target=self.process, args = ())
            self.main_thread.start()

            self.charting_thread = threading.Thread(target=self.charting_process, args=())
            self.charting_thread.start()

            self.certhalert_thread = threading.Thread(target=self.certhalert_process, args=())
            self.certhalert_thread.start()

    def get_command(self, cmd: str, data: dict = None):
        try:
            if cmd == command_get_giota_data:
                deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(self.fiware_service)
                deviceInfo.run()

                return unexeaqua3s.json.dumps(deviceInfo.get_alert_data_for_giota())

            if cmd == command_get_anomaly_data:
                deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(self.fiware_service)
                deviceInfo.logger = self.logger
                deviceInfo.run()

                device = deviceInfo.get_smart_model(data['device'])
                time = data['fiware_time']

                result = {}
                result['high_value'] = str(device.get_anomaly_value(time))
                result['anomaly_settings'] = device.get_anomaly_raw_values(time, lerp=True)
                result['fiware_time'] = str(time)

                return unexeaqua3s.json.dumps(result, indent=2)

        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

        return unexeaqua3s.json.dumps({})


    def add_command(self, cmd:str, data:dict = None):
        if self.debug:
            self.process_command({'command': cmd, 'data': data})
        else:
            if cmd == command_rebuild_charts:
                self.charting_command_list.append({'command':cmd, 'data':data})
            else:
                self.command_list.append({'command':cmd, 'data':data})

    def process_command(self, cmd_packet):

        current_command = cmd_packet['command']
        data = cmd_packet['data']

        if current_command == command_pilot_update:
            self.update_devices()
            unexeaqua3s.visualiser.pilot_device_update(self.fiware_service, self.logger)

        if current_command == command_device_update:
            self.update_single_device(data)
            unexeaqua3s.visualiser.pilot_device_update(self.fiware_service, self.logger)

        if current_command == command_rebuild_charts:
            self.update_charting(data)
            unexeaqua3s.visualiser.pilot_device_update(self.fiware_service, self.logger)

        if current_command == command_build_userlayer_references:
            self.build_userlayers()
            self.update_devices()

        if current_command == command_rebuild_anomaly_settings:
            self.rebuild_anomaly_settings()

    def charting_process(self):
        while True:
            try:
                if len(self.charting_command_list):
                    self.last_charting = datetime.datetime.utcnow()
                    current_command = self.charting_command_list.pop(0)

                    self.process_command(current_command)
            except Exception as e:
                self.logger.exception(inspect.currentframe(),e)
            time.sleep(1)

    def certhalert_process(self):
        while True:
            self.process_certh_alert()
            time.sleep(60*5)

    def process_certh_alert(self):
        data = {}

        try:
            if self.fiware_service_to_certh() != 'N/A':
                params = {}
                params['organizationDescription'] = self.fiware_service_to_certh()
                r = requests.get(os.environ['CERTH_ALERTS'] + '/CurrentAllAlertsService', params=params, timeout=60)

                if r.ok:
                    data = unexeaqua3s.json.loads(r.text)

                    if 'alerts' in data:
                        for category in data['alerts']:
                            for inst in data['alerts'][category]:
                                inst['timestamp'] = unexefiware.time.prettyprint_fiware(inst['timestamp'])


        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)
            data = {}

        try:
            if len(data) == 0:
                dt = datetime.datetime.now(unexeaqua3s.pilot_timezone.get(self.fiware_service))
                timestamp = unexefiware.time.prettyprint_fiware(unexefiware.time.datetime_to_fiware(dt))

                data = {
                    "alerts": {
                        "satellite": [
                            {
                                "reason": "No CERTH data for Pilot",
                                "property": "N/A",
                                "source_id": "N/A",
                                "timestamp": timestamp
                            }
                        ],
                        "social_media": [
                            {
                                "reason": "No CERTH data for Pilot",
                                "property": "N/A",
                                "source_id": "N/A",
                                "timestamp": timestamp
                            }
                        ],
                        "drone": [
                            {
                                "reason": "No CERTH data for Pilot",
                                "property": "N/A",
                                "source_id": "N/A",
                                "timestamp": timestamp
                            }
                        ],
                        "cctv": [
                            {
                                "reason": "No CERTH data for Pilot",
                                "property": "N/A",
                                "source_id": "N/A",
                                "timestamp": timestamp
                            }
                        ]
                    }
                }

            #post data here
            fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            alert_data = {
                "@context": "https://smartdatamodels.org/context.jsonld",
                "id": "urn:ngsi-ld:CerthAlertData:CerthAlertData",
                "type": "CerthAlertData",

                "alert_status": {
                    "type": "Property",
                    "value": unexeaqua3s.json.dumps(data)
                },
            }

            result = fiware_wrapper.get_entity(alert_data['id'], self.fiware_service)

            if len(result) == 0:
                fiware_wrapper.create_instance(alert_data,self.fiware_service)
            else:
                fiware_wrapper.patch_entity(alert_data['id'], {'alert_status': alert_data['alert_status']}, service=self.fiware_service)

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)
    def fiware_service_to_certh(self):
        if self.fiware_service == 'EYA':
            return 'Thessaloniki'

        if self.fiware_service == 'SOF':
            return 'Sofia'

        if self.fiware_service == 'AAA':
            return 'Trieste'

        if self.fiware_service == 'SVK':
            return 'Botevgrad'

        if self.fiware_service == 'WBL':
            return 'Lemesos'

        if self.fiware_service == 'VVQ':
            return 'Brussels'

        return 'N/A'

    def process(self):

        while True:
            try:
                if len(self.command_list):
                    current_command = self.command_list.pop(0)

                    self.process_command(current_command)

                if self.do_automatic_updates:
                    if self.last_charting == None:
                        self.update_devices()
                    else:
                        min_diff = (datetime.datetime.utcnow() - self.last_charting).seconds / 60

                        if min_diff > 10:
                            self.update_devices()
            except Exception as e:
                self.logger(inspect.currentframe(),e)

            time.sleep(1)


    def rebuild_anomaly_settings(self):
        raise Exception('GARETH_rewrite this to address new smart model for devies')

    def build_userlayer_references(self):
        unexeaqua3s.support.delete_resources(os.environ['DEVICE_BROKER'], self.fiware_service)
        unexeaqua3s.support.add_user_resources(os.environ['DEVICE_BROKER'],[self.fiware_service])

    def get_anomalyvalue(self, deviceInfo, device_id, fiware_time):
        return unexeaqua3s.service_anomaly.get_anomaly_value(fiware_time, deviceInfo.anomalysetting_get(device_id))

    def update_charting(self, data:dict=None):
        #GARETH - id dict != none it's a single device to update
        if self.disable_updates == False:

            force_interday = False
            now = datetime.datetime.now(unexeaqua3s.pilot_timezone.get(self.fiware_service)).replace(tzinfo=None)

            if data and 'force_interday' in data:
                force_interday = data['force_interday'].lower() == 'true'

            if data and 'datetime' in data:
                now = unexefiware.time.fiware_to_datetime(data['datetime'])
                
            unexeaqua3s.support.do_charting(self.fiware_service, force_interday=force_interday, logger=self.logger, charting_time=now)            
        else:
            self.logger.log(inspect.currentframe(), 'No update enabled:' + self.fiware_service)

    def update_device_model(self, model:unexeaqua3s.deviceinfo.DeviceSmartModel):
        model.alertstatus_update_and_patch(self.fiware_service)
        model.anomalystatus_update_and_patch(self.fiware_service)

        if model.isEPANET():
            self.epanomalies.process_device(self.fiware_service, model)

    def update_single_device(self,data:dict):
        try:
            self.logger.log(inspect.currentframe(),'update_single_device:' + str(data) )

            session = requests.session()
            broker_url = os.environ['DEVICE_BROKER']

            fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            result = fiware_wrapper.get_entity(entity_id=data['device'],service=self.fiware_service)

            if type(result) is dict:
                self.update_device_model(unexeaqua3s.deviceinfo.DeviceSmartModel(result))
                self.add_command(cmd=command_rebuild_charts, data= {'device': data['device']})

            #GARETH - do this to force mail update
            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(self.fiware_service)
            deviceInfo.run()

            self.alert_mailing.update(deviceInfo)

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

    def update_devices(self):
        if self.disable_updates == False:
            #self.logger.log(inspect.currentframe(),'update_pilot_devices:' + self.fiware_service)

            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(self.fiware_service)
            deviceInfo.run()
            for entry in deviceInfo.deviceModelList:
                self.update_device_model(deviceInfo.deviceModelList[entry])

            self.alert_mailing.update(deviceInfo)
        else:
            self.logger.log(inspect.currentframe(),'No update enabled:' + self.fiware_service)



        #GARETH only do this once per block of updates
        # self.add_command(cmd = command_rebuild_charts)

    def get_fiware_time(self):
        fiware_time = None
        try:
            # try local timezone
            dt = datetime.datetime.now(unexeaqua3s.pilot_timezone.get(self.fiware_service) )
            fiware_time = unexefiware.time.datetime_to_fiware(dt)
        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)
            fiware_time = unexefiware.time.datetime_to_fiware(datetime.datetime.utcnow())

        return fiware_time

class WorkhorseBackend():
    def __init__(self):
        self.link = '<https://smartdatamodels.org/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'

    def init(self, logger = None, debug = False, do_automatic_updates = False):
        self.pilots = {}

        self.logger = logger

        if self.logger == None:
            self.logger = unexefiware.base_logger.BaseLogger()

        pilot_list = os.environ['PILOTS'].split(',')

        for fiware_service in pilot_list:
            self.pilots[fiware_service] = PilotProcessor(debug=debug, do_automatic_updates=do_automatic_updates)
            self.pilots[fiware_service].init(fiware_service, self.logger)

    def add_command(self, fiware_service:str, cmd:str, data:dict = None):
        if fiware_service in self.pilots:
            self.pilots[fiware_service].add_command(cmd, data)
        else:
            self.logger.fail(inspect.currentframe(),'No pilot:' + fiware_service)

    def get_command(self, fiware_service:str, cmd:str, data:dict = None) -> dict:
        if fiware_service in self.pilots:
            return self.pilots[fiware_service].get_command(cmd, data)
        else:
            self.logger.fail(inspect.currentframe(),'No pilot:' + fiware_service)


def device_update(fiware_service:str, device_id:str, logger=None) -> bool:
    try:
        headers = {}
        headers['Content-Type'] = 'application/ld+json'
        headers['fiware-service'] = fiware_service
        headers['device'] = device_id
        session = requests.session()

        path = os.environ['WORKHORSE_BROKER'] + '/pilot_device_update'
        payload = {}

        r = session.post(path, data=unexeaqua3s.json.dumps(payload), headers=headers, timeout=10)

        return r.ok
    except Exception as e:
        if logger:
            logger.exception(inspect.currentframe(), e )

    return False

def pilot_update(fiware_service:str, logger=None) -> bool:
    try:
        headers = {}
        headers['Content-Type'] = 'application/ld+json'
        headers['fiware-service'] = fiware_service
        session = requests.session()

        path = os.environ['WORKHORSE_BROKER'] + '/pilot_update'
        payload = {}

        r = session.post(path, data=unexeaqua3s.json.dumps(payload), headers=headers, timeout=10)

        return r.ok
    except Exception as e:
        if logger:
            logger.exception(inspect.currentframe(), e )

    return False



import unexeaqua3s.kibanablelog
import os
import requests
import unexeaqua3s.json
import unexefiware.fiwarewrapper

servicelog = unexeaqua3s.kibanablelog.KibanableLog('Special Test')

def testbed(fiware_service):
    quitApp = False

    workhorse = unexeaqua3s.workhorse_backend.WorkhorseBackend()
    workhorse.init(logger=servicelog, debug = True)

    anomaly_sensor = 'urn:ngsi-ld:Device:RISensor-TS0031-ch0'

    while quitApp is False:
        print('\nWorkhouse Testbed')

        print('\n')
        print('1..' + unexeaqua3s.workhorse_backend.command_device_update +' '  + anomaly_sensor)
        print('2..' + unexeaqua3s.workhorse_backend.command_pilot_update)
        print('2a..' + unexeaqua3s.workhorse_backend.command_rebuild_charts)
        print('3..Setup epanomaly')
        print('4..Get giota data')
        print('5..Process CERTH Alert into FIWARE:' + fiware_service)
        print('6..Get anomaly data for:' + anomaly_sensor)
        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            workhorse.add_command(fiware_service,unexeaqua3s.workhorse_backend.command_device_update, {'device': anomaly_sensor})
            #device_update(fiware_service, anomaly_sensor, unexeaqua3s.kibanablelog.KibanableLog('WorkhorseTestbed') )


        if key == '2':
            workhorse.add_command(fiware_service, unexeaqua3s.workhorse_backend.command_pilot_update)

        if key == '2a':
            workhorse.add_command(fiware_service, unexeaqua3s.workhorse_backend.command_rebuild_charts)

        if key == '3':
            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service=fiware_service)
            deviceInfo.logger = unexeaqua3s.kibanablelog.KibanableLog('WorkhorseTestbed')
            deviceInfo.run()

            device = deviceInfo.deviceModelList['urn:ngsi-ld:Device:UNEXE_TEST_76']
            device.epanomaly_fudge_setting(fiware_service,True)

            workhorse.add_command(fiware_service,unexeaqua3s.workhorse_backend.command_device_update, {'device': 'urn:ngsi-ld:Device:UNEXE_TEST_76'})

        if key =='4':
            result = workhorse.get_command(fiware_service, command_get_giota_data)
            print(unexeaqua3s.json.dumps(unexeaqua3s.json.loads(result),indent=2))

        if key == '5':
            workhorse.pilots[fiware_service].process_certh_alert()

        if key == '6':
            deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service=fiware_service)
            deviceInfo.logger = unexeaqua3s.kibanablelog.KibanableLog('WorkhorseTestbed')
            deviceInfo.run()

            device = deviceInfo.get_smart_model(anomaly_sensor)
            time = unexefiware.time.datetime_to_fiware(datetime.datetime.utcnow())

            print( unexefiware.time.prettyprint_fiware(time) + ' high:' + str(device.get_anomaly_value(time)))
            print(unexefiware.time.prettyprint_fiware(time) + ' ' + str(device.get_anomaly_raw_values(time, lerp=True)))

        if key == '7':
            time = unexefiware.time.datetime_to_fiware(datetime.datetime.utcnow())
            result = workhorse.get_command(fiware_service, unexeaqua3s.workhorse_backend.command_get_anomaly_data, {'device': anomaly_sensor, 'fiware_time': time})

            print(str(result))

        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    testbed('AAA')

