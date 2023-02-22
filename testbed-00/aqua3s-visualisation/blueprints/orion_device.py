import local_environment_settings
import blueprints.debug
from flask import Blueprint
from flask import request
from flask_cors import CORS, cross_origin
from flask import Blueprint, render_template, abort


import requests
import unexeaqua3s.json
import math
import inspect
import threading
import copy

import unexefiware.time
import unexefiware.device
import unexefiware.units
import unexefiware.ngsildv1
import unexefiware.fiwarewrapper

import blueprints.keyrock_blueprint
import blueprints.globals
import blueprints.debug
import unexeaqua3s.deviceinfo
import unexeaqua3s.siteinfo

import os
import datetime
import time

class CERTHAlertCache:
    def __init__(self, fiware_service:str):
        self.fiware_service = fiware_service
        self.data = {}
        self.do_run = False

    def init(self):
        self.run()

    def run(self):
        self.data = {}

        if self.do_run == False:
            return

        try:
            fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
            result = fiware_wrapper.get_instance(entity_id='urn:ngsi-ld:CerthAlertData:CerthAlertData', service=self.fiware_service)

            if result[0] == 200 and len(result[1]) > 0:
                self.data = unexeaqua3s.json.loads(result[1]['alert_status']['value'])

        except Exception as e:
            blueprints.debug.servicelog.exception(inspect.currentframe(), e)

        return

        try:
            self.data = {}

            if self.fiware_service_to_certh() != 'N/A':
                params = {}
                params['organizationDescription'] = self.fiware_service_to_certh()
                r = requests.get(os.environ['CERTH_ALERTS'] + '/CurrentAllAlertsService', params=params, timeout=1)

                if r.ok:
                    self.data = unexeaqua3s.json.loads(r.text)

                    for category in self.data['alerts']:
                        for inst in self.data['alerts'][category]:
                            inst['timestamp'] = unexefiware.time.prettyprint_fiware(inst['timestamp'])


        except Exception as e:
            blueprints.debug.servicelog.exception(inspect.currentframe(), e)
            self.data = {}

        if len(self.data) == 0:
            dt = datetime.datetime.now(unexeaqua3s.pilot_timezone.get(self.fiware_service))
            timestamp = unexefiware.time.prettyprint_fiware(unexefiware.time.datetime_to_fiware(dt))

            self.data = {
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

    def fiware_service_to_certh(self):
        if self.fiware_service == 'EYA':
            return 'Thessaloniki'

        return 'N/A'


class DeviceCache:
    def __init__(self):
        self.deviceInfo = {}
        self.unexevisibility = {}
        self.mutex = threading.Lock()

        self.worklist = []

    def init(self):
        self.mutex.acquire()

        for pilot in blueprints.globals.fiware_service_list:
            self.unexevisibility[pilot] = True

            self.deviceInfo[pilot] = {'timestamp': datetime.datetime.utcnow(),
                                      'deviceInfo': None,
                                      'forced_update': False,
                                      'leak_localisation':False
                                      }

            #GARETH - use a local DeviceInfo for tersting
            #self.deviceInfo[pilot]['deviceInfo'] = unexeaqua3s.deviceinfo.DeviceInfo2(wrapper=None, fiware_service=pilot)
            self.deviceInfo[pilot]['deviceInfo'] = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service=pilot)
            self.deviceInfo[pilot]['deviceInfo'].logger = blueprints.debug.servicelog
            self.deviceInfo[pilot]['deviceInfo'].run()

            self.deviceInfo[pilot]['alert_cache'] = CERTHAlertCache(fiware_service=pilot)
            self.deviceInfo[pilot]['alert_cache'].logger = blueprints.debug.servicelog
            self.deviceInfo[pilot]['alert_cache'].run()

        self.mutex.release()

        self.thread = threading.Thread(target=self._periodic_process, args = '')
        self.thread.start()

    def _periodic_process(self):
        while True:
            for fiware_service in blueprints.globals.fiware_service_list:
                self.update(fiware_service, forced=self.deviceInfo[fiware_service]['forced_update'])

            while len(self.worklist) > 0:
                fiware_service = self.worklist.pop(0)
                print('Doing device update')
                self.update(fiware_service, forced=True)

            time.sleep(1)    #gareth -   wait for 1m between updates

    def update(self, loc, forced=False):
        try:
            self.mutex.acquire()

            now = datetime.datetime.utcnow()
            time_diff = (now - self.deviceInfo[loc]['timestamp']).total_seconds()

            if (time_diff > (60 * 5)) or forced:
                t0 = time.perf_counter()
                self.deviceInfo[loc]['deviceInfo'].run()
                self.deviceInfo[loc]['alert_cache'].run()

                text = 'DeviceInfo time:' + str(round(time.perf_counter() - t0, 2))

                if self.deviceInfo[loc]['forced_update']:
                    text += ' FORCED UPDATE'

                blueprints.debug.servicelog.log(inspect.currentframe(), text)
                self.deviceInfo[loc]['timestamp'] = now
                self.deviceInfo[loc]['forced_update'] = False
            self.mutex.release()

        except Exception as e:
            self.mutex.release()
            blueprints.debug.servicelog.exception(inspect.currentframe(), e)

    def get_deviceInfo(self, loc):
        self.mutex.acquire()
        data = copy.deepcopy(self.deviceInfo[loc]['deviceInfo'])
        self.mutex.release()

        return data

    def get_certh_alert(self, loc):
        self.mutex.acquire()
        data = copy.deepcopy(self.deviceInfo[loc]['alert_cache'].data)
        self.mutex.release()

        return data

    def pilot_device_update(self, fiware_service):
        self.deviceInfo[fiware_service]['forced_update'] = True
        self.worklist.append(fiware_service)

    def get_UNEXEvisibility(self, fiware_service):
        return self.unexevisibility[fiware_service]

    def set_UNEXEvisibility(self, fiware_service, visible = True):
        self.unexevisibility[fiware_service] = visible

    def set_leak_localisation_visibility(self, fiware_service:str, visible:bool = True):
        try:
            if fiware_service in self.deviceInfo:
                self.deviceInfo[fiware_service]['leak_localisation'] = visible
        except Exception as e:
            blueprints.debug.servicelog.exception(inspect.currentframe(), e)

    def get_Leak_localisation_visualisation(self, fiware_service:str) ->bool:
        try:
            if fiware_service in self.deviceInfo:
                return self.deviceInfo[fiware_service]['leak_localisation']
        except Exception as e:
            blueprints.debug.servicelog.exception(inspect.currentframe(), e)

        return False

deviceCache = None

def init():
    global deviceCache
    deviceCache = DeviceCache()
    deviceCache.init()

def force_update(fiware_service):
    global deviceCache
    deviceCache.pilot_device_update(fiware_service)

def get_deviceInfo(loc):
    global deviceCache
    return deviceCache.get_deviceInfo(loc)

def get_certh_alert(loc):
    global deviceCache
    return deviceCache.get_certh_alert(loc)

def UNEXE_visualise_enabled(loc):
    global deviceCache
    return deviceCache.get_UNEXEvisibility(loc)

def get_leak_localisation_visualisation(loc:str)->bool:
    if loc != 'AAA':
        return False

    global deviceCache

    return deviceCache.get_Leak_localisation_visualisation(loc)


def UNEXE_visualise(loc, is_UNEXE):
    if is_UNEXE and not UNEXE_visualise_enabled(loc):
        return False

    return True



blueprint = Blueprint('orion_device_blueprint', __name__, template_folder='templates')

@blueprint.route('/pilot_device_update', methods=['POST'])
@cross_origin()
def pilot_device_update():
    try:
        print(str(request) + ' ' + str(request.data))
        global deviceCache
        deviceCache.pilot_device_update(request.headers['fiware-service'])

        return 'OK', 200
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e)
        return str(e),500

@blueprint.route('/pilot_set_unexe_visibility', methods=['POST'])
@cross_origin()
def pilot_set_unexe_visibility():
    try:
        print(str(request) + ' ' + str(request.data))

        global deviceCache
        deviceCache.set_UNEXEvisibility(request.headers['fiware-service'], request.headers['visible'].lower() == 'true')

        return 'OK', 200
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e)
        return str(e), 500

@blueprint.route('/visualiser_update_userlayers', methods=['POST'])
@cross_origin()
def visualiser_update_userlayers():
    try:
        print(str(request) + ' ' + str(request.data))

        blueprints.globals.fiware_resources.reload(request.headers['fiware-service'])

        return 'OK', 200
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e)
        return str(e), 500

@blueprint.route('/visualiser_set_leak_localisation', methods=['POST'])
@cross_origin()
def visualiser_set_leak_localisation():
    try:
        print(str(request) + ' ' + str(request.data))

        global deviceCache
        deviceCache.set_leak_localisation_visibility(request.headers['fiware-service'], request.headers['visible'].lower() == 'true')

        return 'OK:' + request.headers['fiware-service'] +' ' + str(deviceCache.get_Leak_localisation_visualisation(request.headers['fiware-service']) ), 200
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e)
        return str(e), 500


class SiteInfo():

    def __init__(self, deviceInfo):
        self.site_list = {}
        self.deviceInfo = deviceInfo

        self.state_to_colour = {}
        self.state_to_colour['Red'] = '#ff0000'
        self.state_to_colour['Green'] = '#00ff00'
        self.state_to_colour['Alert'] = '#9c9900'
        self.state_to_colour['Anomaly'] = '#c03ec7'
        self.state_to_colour['EPAnomaly'] ='#46bdc6'

        self.logger = unexefiware.base_logger.BaseLogger()

        self.run()

    def run(self):
        self.site_list = {}
        self.build_site_list()

    def devicename_to_markername(self, entry):
        return self.deviceInfo.get_smart_model(entry).name()

    def include_site_in_location(self, site_name):
        return True

    def swap_lat_lng(self, site_name):
        return False

    def modify_site_loc(self, site_name):
        pass

    def build_site_list(self):
        self.site_list = {}

        try:
            # 1. build a list of named groups
            for entry in self.deviceInfo.deviceInfoList:
                name = self.devicename_to_markername(entry)
                if name not in self.site_list:
                    self.site_list[name] = {}
                    self.site_list[name]['devices'] = []

                self.site_list[name]['devices'].append(entry)
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

        for site_name in self.site_list:
            # gareth -   sort by device ID index.
            #           probably want to change this to something else ...
            # self.site_list[site_name]['devices'] = sorted(self.site_list[site_name]['devices'], key=lambda k: int(k.replace('urn:ngsi-ld:Device:', '')))
            self.site_list[site_name]['devices'] = sorted(self.site_list[site_name]['devices'])

        try:
            # 2. work out location
            for site_name in self.site_list:
                lat = 0
                lng = 0

                device_count = len(self.site_list[site_name]['devices'])

                if device_count > 0:
                    actual_device_count = 0
                    for device_label in self.site_list[site_name]['devices']:
                        device = self.deviceInfo.device_get(device_label)

                        if device:
                            lat = lat + device['location']['value']['coordinates'][0]
                            lng = lng + device['location']['value']['coordinates'][1]
                            actual_device_count += 1

                    lat = lat / actual_device_count
                    lng = lng / actual_device_count

                    if self.swap_lat_lng(site_name):
                        self.site_list[site_name]['location'] = [lng, lat]
                    else:
                        self.site_list[site_name]['location'] = [lat, lng]

                    self.modify_site_loc(site_name)

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

        for site_name in self.site_list:
            self.site_list[site_name]['location'][0] = round(self.site_list[site_name]['location'][0], 6)
            self.site_list[site_name]['location'][1] = round(self.site_list[site_name]['location'][1], 6)

        try:
            # 3. device pin colour from state
            for site in self.site_list:
                self.site_list[site]['status'] = 'Green'

                for device_id in self.site_list[site]['devices']:
                    device = self.deviceInfo.get_smart_model(device_id)

                    if device.deviceState() == 'Red':
                        self.site_list[site]['status'] = 'Red'

                if self.site_list[site]['status'] != 'Red':
                    # gareth -   also need to something about anomalies_screen & alerts_screen ...
                    #           so, will return Green if everything is fine
                    #           or Alert if there's an alert
                    #           or Anomaly if there's an anomaly but no alerts

                    for device_id in self.site_list[site]['devices']:

                        device = self.deviceInfo.get_smart_model(device_id)

                        if self.site_list[site]['status'] != 'Alert':
                            if device.anomaly_isTriggered() == True:
                                self.site_list[site]['status'] = 'Anomaly'

                            if device.epanomaly_isTriggered():
                                self.site_list[site]['status'] = 'EPAnomaly'

                            if device.alert_isTriggered() == True:
                                self.site_list[site]['status'] = 'Alert'

        except Exception as e:
            self.logger.exception(inspect.currentframe(), e)

    def site_get_property_count(self, site_name, controlled_property_type=None):
        prop_count = 0

        site = self.site_list[site_name]

        for device_label in site['devices']:
            device = self.deviceInfo.device_get(device_label)

            props = unexefiware.model.get_controlled_properties(device)
            if controlled_property_type == None:
                prop_count += len(props)
            else:
                for prop in props:
                    if prop == controlled_property_type:
                        prop_count = prop_count + 1

        return prop_count

    def get_device_extended_data(self, controlled_property_type, visualise_alerts):
        data = {}
        data['marker'] = []

        for site_name in self.site_list:
            try:
                if controlled_property_type == 'device' or self.site_get_property_count(site_name, controlled_property_type) > 0:
                    record = {}
                    record['id'] = site_name
                    record['loc'] = self.site_list[site_name]['location']

                    if controlled_property_type == 'device':
                        record['detail'] = self.site_print_detail_as_html(site_name, controlled_property_type=None, visualise_alerts=visualise_alerts)
                    else:
                        record['detail'] = self.site_print_detail_as_html(site_name, controlled_property_type, visualise_alerts=visualise_alerts)

                    record['status'] = self.site_list[site_name]['status']
                    record['color'] = '#000000'

                    result = self.site_list[site_name]['status']
                    record['color'] = self.state_to_colour[result]

                    if visualise_alerts == False:
                        record['color'] = '#41a7c7'

                    data['marker'].append(record)
            except Exception as e:
                if self.logger:
                    self.logger.exception(inspect.currentframe(), e)

        return data

    def property_observedAt_prettyprint_mapview(self, device:unexeaqua3s.deviceinfo.DeviceSmartModel, prop:str=None):

            ts = device.property_observedAt(prop)
            text = ''

            if ts != unexeaqua3s.deviceinfo.invalid_string:
                dt = unexefiware.time.fiware_to_datetime(ts)

                text += str(dt.year) + '-' + str(dt.month).zfill(2) + '-' + str(dt.day).zfill(2)
                text += ' '
                text += str(dt.hour).zfill(2) + ':' + str(dt.minute).zfill(2)
            else:
                text += 'Date not available'

            return text

    def site_print_detail_as_html(self, site_name, controlled_property_type=None, visualise_alerts=False):
        text = ''

        text += '<style>'
        text += 'table {font-family: arial, sans-serif; border-collapse: collapse; width: 100%;}'

        text += 'td, th { border: 1px solid  #dddddd; text-align: left; padding: 12px;}'

        text += 'tr:nth-child(even){ background-color:  #dddddd;}'
        text += '</style>'

        text += '<h2>'
        text += site_name
        text += '</h2>'

        try:
            if self.site_list[site_name]['status'] == 'Red':
                text += '<span class="name" style="color:#ff0000">'
                text += '<h3>'
                text += "Device is offline"
                text += '</h3>'
                text += '</span>'

            if self.site_get_property_count(site_name) > 0:
                text += '<table>'
                text += '<tr>'
                text += '<th> Date Time </th>'
                text += '<th> ID </th>'
                text += '<th> Property </th>'
                text += '<th> Value </th>'
                text += '</tr>'


                sort_data = []

                for device_label in self.site_list[site_name]['devices']:

                    device = self.deviceInfo.get_smart_model(device_label)
                    prop_list = unexefiware.model.get_controlled_properties(device.get_fiware())

                    for prop in prop_list:
                        if controlled_property_type == None or prop == controlled_property_type:
                            data = {}
                            data['device_id'] = device_label
                            data['prop'] = prop
                            data['time'] = self.property_observedAt_prettyprint_mapview(device, prop)

                            sort_data.append(data)

                # sort data based on ....
                sort_data = sorted(sort_data, key=lambda d: d['time'], reverse=True)


                for entry in sort_data:
                    device_label = entry['device_id']

                    if 'MIR' in device_label:
                        print()

                    device = self.deviceInfo.get_smart_model(device_label)
                    prop = entry['prop']

                    text += '<tr>'
                    text += '<td text-align: center;>'

                    colour = '#000000'

                    alert_type_text = ''

                    if visualise_alerts == True:
                        if device.deviceState() == 'Red':
                            colour = self.state_to_colour['Red']
                            alert_type_text = '(ALERT)'
                        else:
                            if device.anomaly_isTriggered():
                                colour = self.state_to_colour['Anomaly']
                                alert_type_text = '(ANOMALY)'

                            if device.epanomaly_isTriggered():
                                colour = self.state_to_colour['EPAnomaly']
                                alert_type_text = '(EPANOMALY)'

                            if device.alert_isTriggered() == True:
                                colour = self.state_to_colour['Alert']
                                alert_type_text = '(ALERT)'

                    text += '<span class="name" style="color:' + colour + '">'

                    text += self.property_observedAt_prettyprint_mapview(device, prop)

                    text += '</td>'

                    text += '<td>'
                    text += '<span class="name" style="color:' + colour + '">'

                    text += device.sensorName()
                    text += '</td>'

                    text += '<td>'
                    text += '<span class="name" style="color:' + colour + '">'
                    text += device.property_prettyprint(prop)
                    text += '</td>'

                    text += '<td>'
                    text += '<span class="name" style="color:' + colour + '">'

                    if device.property_value(prop) != unexeaqua3s.deviceinfo.invalid_string:
                        text += device.property_value_prettyprint(prop)
                        text += device.property_unitCode_prettyprint(prop)
                    else:
                        text += 'N/A'

                    if visualise_alerts == True:
                        if len(alert_type_text):
                            text += alert_type_text

                    text += '</span>'
                    text += '<br>'
                    text += '</td>'

                    text += '</tr>'
            else:
                text += "No controlled property data"
                text += '</p>'
        except Exception as e:
            if self.logger:
                self.logger.exception(inspect.currentframe(), e)

        return text

    def get_puc_location(self):
        lat = 0
        lng = 0
        zoom = 12

        return [lat, lng, zoom]

class PilotSiteInfo(SiteInfo):
    def __init__(self, deviceInfo):
        super().__init__(deviceInfo)

    def devicename_to_markername(self, entry):
        # gareth -   WBL uses unique device names for all devices which leads to multiple devices in the same location
        #           if the first letter of the WBL device is 0, take the 4-digit code as the device group name
        #           once/if WBL fixes this, the code should still work (hopefully)

        device = self.deviceInfo.get_smart_model(entry)

        if self.deviceInfo.fiware_service == 'WBL':

            if 'UNEXE_TEST' in device.name():
                return device.name()[0:15]

            if device.name()[0] == '0':
                return device.name()[0:4]

        return device.name()

    def get_device_extended_data(self, controlled_property_type, visualise_alerts):
        data = {}
        data['marker'] = []
        data['leak_localisation'] = False

        for site_name in self.site_list:
            try:
                if UNEXE_visualise(self.deviceInfo.fiware_service, 'UNEXE_TEST' in site_name) and (controlled_property_type == 'device' or self.site_get_property_count(site_name, controlled_property_type) > 0):
                    record = {}
                    record['id'] = site_name
                    record['loc'] = self.site_list[site_name]['location']

                    if controlled_property_type == 'device':
                        record['detail'] = self.site_print_detail_as_html(site_name, controlled_property_type=None, visualise_alerts=visualise_alerts)
                    else:
                        record['detail'] = self.site_print_detail_as_html(site_name, controlled_property_type, visualise_alerts=visualise_alerts)

                    record['status'] = self.site_list[site_name]['status']
                    record['color'] = '#000000'

                    result = self.site_list[site_name]['status']
                    record['color'] = self.state_to_colour[result]

                    if visualise_alerts == False:
                        record['color'] = '#41a7c7'

                    data['marker'].append(record)
            except Exception as e:
                if self.logger:
                    self.logger.exception(inspect.currentframe(), e)

        try:
            data['leak_localisation'] = get_leak_localisation_visualisation(self.deviceInfo.fiware_service)
        except Exception as e:
            blueprints.debug.servicelog.exception(inspect.currentframe(), e)

        return data



    def get_puc_location(self):

        lat = 0
        lng = 0
        zoom = 12

        actual_site_list = 0

        if len(self.site_list) > 0:
            for site in self.site_list:

                if self.include_site_in_location(site):
                    lat = lat + self.site_list[site]['location'][0]
                    lng = lng + self.site_list[site]['location'][1]
                    actual_site_list += 1

        if actual_site_list > 0:
            lat = lat / actual_site_list
            lng = lng / actual_site_list
        else:
            if self.deviceInfo.fiware_service == 'AAA':
                lat = 13.56
                lng = 45.8

            if self.deviceInfo.fiware_service == 'SOF':
                lng = 42.691
                lat = 23.330

            if self.deviceInfo.fiware_service == 'SVK':
                lng = 42.691
                lat = 23.330

            if self.deviceInfo.fiware_service == 'WBL':
                lng = 34.70
                lat = 33.01

            if self.deviceInfo.fiware_service == 'EYA':
                lng = 40.637
                lat = 22.932

            if self.deviceInfo.fiware_service == 'GT':
                lng = 50.954
                lat = -4.137

            if self.deviceInfo.fiware_service == 'WIS':
                lng = 50.814
                lat = -4.257

            if self.deviceInfo.fiware_service == 'TTT':
                lat = 13.56
                lng = 45.8

            if self.deviceInfo.fiware_service == 'P2B':
                lat = 13.56
                lng = 45.8
                zoom = 10

            if self.deviceInfo.fiware_service == 'VVQ':
                lng = 50.852
                lat = 4.395
                zoom = 10

        #custom zoom
        if self.deviceInfo.fiware_service == 'AAA':
            zoom = 10

        if self.deviceInfo.fiware_service == 'EYA':
            zoom = 10


        return [lat, lng, zoom]

    def include_site_in_location(self, site_name):

        if self.deviceInfo.fiware_service == 'WBL':
            if site_name == 'RISensor':
                return False

            if 'MIR' in site_name:
                return False

        return True

    def swap_lat_lng(self, site_name):
        if self.deviceInfo.fiware_service == 'WBL':
            return True

        if self.deviceInfo.fiware_service == 'SOF':
            return True

        if self.deviceInfo.fiware_service == 'EYA':
            return True

        if self.deviceInfo.fiware_service == 'VVQ':
            return True

        return False

    def modify_site_loc(self, site_name):

        if self.deviceInfo.fiware_service == 'WBL':
            if 'RISensor' in site_name:
                self.site_list[site_name]['location'][0] -= 0.01
                self.site_list[site_name]['location'][1] -= 0.01

        if self.deviceInfo.fiware_service == 'SOF':

            if 'RISensor' in site_name:
                self.site_list[site_name]['location'][0] -= 0.001
                self.site_list[site_name]['location'][1] -= 0.001

        if self.deviceInfo.fiware_service == 'AAA':
            if site_name == 'CAPTAZIONE TIMAVO - RAMO 2':
                self.site_list[site_name]['location'] = [13.59128, 45.78673]

            if site_name == 'CAPTAZIONE TIMAVO - RAMO 3':
                self.site_list[site_name]['location'] = [13.59228, 45.78773]

            if site_name == 'RISensor':
                self.site_list[site_name]['location'] = [13.587823, 45.791185]

def get_siteInfo(deviceInfo):
    return PilotSiteInfo(deviceInfo)



# -----------------------------------------------------------------------------------------------

# -----------------------------------------------------------------------------------------------
def orion_status_print_as_html(record):
    text = ''

    text += '<h3><b>'
    text += '<p style="color:#ff0000">'
    text += unexefiware.device.get_name(record)
    text += '</p>'
    text += '</h3></b>'

    return text

def device_print_detail_as_html(device, controlled_property_mask=None):
    text = ''

    text += '<style>'
    text += 'table {font-family: arial, sans-serif; border-collapse: collapse; width: 100%;}'

    text += 'td, th { border: 1px solid  #dddddd; text-align: left; padding: 8px;}'

    text += 'tr:nth-child(even){ background-color:  #dddddd;}'
    text += '</style>'

    text += '<h2>'
    text += unexefiware.device.get_name(device)
    text += '</h2>'

    try:
        if unexefiware.device.get_state(device) == 'Red':
            text += '<span class="name" style="color:#ff0000">'
            text += '<h3>'
            text += "A sensor is offline"
            text += '</h3>'
            text += '</span>'
        else:
            prop_list = unexefiware.device.get_controlled_properties(device)

            if len(prop_list) > 0:
                text += '<table>'
                text += '<tr>'
                text += '<th> Property </th>'
                text += '<th> Value </th>'
                text += '</tr>'

                for prop in prop_list:
                    if (controlled_property_mask == None) or (controlled_property_mask == prop):
                        text += '<tr>'
                        text += '<td>'
                        text += unexefiware.units.get_property_printname(prop)
                        text += '</td>'

                        text += '<td>'

                        colour = '#000000'

                        text += '<span class="name" style="color:' + colour + '">'

                        val = unexefiware.device.get_property_value(device, prop)
                        if isinstance(val, str):
                            text += val
                        else:
                            text += str(round(unexefiware.device.get_property_value(device, prop), 2))

                        uc = unexefiware.device.get_property_unitcode(device, prop)

                        text += unexefiware.units.get_property_unitcode_printname(uc)
                        text += '</span>'
                        text += '<br>'
                        text += '</td>'

                        text += '</tr>'
            else:
                text += "No controlled property data"
                text += '</p>'
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
    return text

def get_device_extended_data(deviceInfo, controlled_property_type,visualise_alerts=True):
    return get_siteInfo(deviceInfo).get_device_extended_data(controlled_property_type,visualise_alerts)

def get_puc_device_properties(loc):

    device_options = {}

    try:
        deviceInfo = get_deviceInfo(loc)

        for device_label in deviceInfo.deviceInfoList:

            if deviceInfo.is_UNEXETEST(device_label) == False:
                device = deviceInfo.device_get(device_label)

                device_id = unexefiware.device.get_id(device)
                device_options[device_id] = {}
                device_options[device_id]['name'] = unexefiware.device.get_name(device)
                device_options[device_id]['properties'] = []

                props = unexefiware.device.get_controlled_properties(device)

                device_options[device_id]['properties'] = {}
                for prop in props:
                    device_options[device_id]['properties'][prop] = unexefiware.units.get_property_printname(prop)
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )

    return device_options

def get_puc_unique_device_controlled_properties(deviceInfo):

    property_labels = {}

    for device_id in deviceInfo.deviceInfoList:
        device = deviceInfo.get_smart_model(device_id).get_fiware()

        props = unexefiware.device.get_controlled_properties(device)

        for prop in props:
            if prop not in property_labels:
                property_labels[prop] = 0

    try:
        raw_prop_list = list(property_labels.keys())
        raw_prop_list.sort()

        prop_list = []
        for prop in raw_prop_list:
            record = {}
            record['label'] = prop
            record['print_label'] = unexefiware.units.get_property_printname(prop)

            prop_list.append(record)

        record = {}
        record['label'] = 'device'
        record['print_label'] = 'Devices'

        prop_list.insert(0, record)
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )

    return prop_list

def get_puc_location(deviceInfo):

    return get_siteInfo(deviceInfo).get_puc_location()