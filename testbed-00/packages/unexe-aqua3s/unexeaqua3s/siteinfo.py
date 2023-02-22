import inspect
import unexeaqua3s.deviceinfo
import unexefiware.model
import unexefiware.base_logger


class SiteInfo():

    def __init__(self, deviceInfo):
        self.site_list = {}
        self.deviceInfo = deviceInfo

        self.state_to_colour = {}
        self.state_to_colour['Red'] = '#ff0000'
        self.state_to_colour['Green'] = '#00ff00'
        self.state_to_colour['Alert'] = '#9c9900'
        self.state_to_colour['Anomaly'] = '#c03ec7'

        self.logger = unexefiware.base_logger.BaseLogger()

        self.run()

    def run(self):
        self.site_list = {}
        self.build_site_list()

    def devicename_to_markername(self, entry):
        return self.deviceInfo.device_name(entry)

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
            print('pt-1 ' + str(e))

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
                    device = self.deviceInfo.device_get(device_id)

                    if self.deviceInfo.device_status(device_id) == 'Red':
                        self.site_list[site]['status'] = 'Red'

                if self.site_list[site]['status'] != 'Red':
                    # gareth -   also need to something about anomalies_screen & alerts_screen ...
                    #           so, will return Green if everything is fine
                    #           or Alert if there's an alert
                    #           or Anomaly if there's an anomaly but no alerts

                    for device_id in self.site_list[site]['devices']:

                        if self.site_list[site]['status'] != 'Alert':
                            if self.deviceInfo.anomaly_isTriggered(device_id) == True or self.deviceInfo.anomalyEPAnet_isTriggered(device_id):
                                self.site_list[site]['status'] = 'Anomaly'

                            if self.deviceInfo.alert_isTriggered(device_id) == True:
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

                if True:
                    sort_data = []

                    for device_label in self.site_list[site_name]['devices']:

                        device = self.deviceInfo.device_get(device_label)
                        prop_list = unexefiware.model.get_controlled_properties(device)

                        for prop in prop_list:
                            if controlled_property_type == None or prop == controlled_property_type:
                                data = {}
                                data['device_id'] = device_label
                                data['prop'] = prop
                                data['time'] = self.deviceInfo.property_observedAt_prettyprint_mapview(device_label, prop)

                                sort_data.append(data)

                    # sort data based on ....
                    sort_data = sorted(sort_data, key=lambda d: d['time'], reverse=True)

                    for entry in sort_data:
                        device_label = entry['device_id']
                        device = self.deviceInfo.device_get(device_label)
                        prop = entry['prop']

                        text += '<tr>'
                        text += '<td text-align: center;>'

                        colour = '#000000'

                        if visualise_alerts == True:
                            if unexefiware.model.get_property_value(device, 'deviceState') == 'Red':
                                colour = self.state_to_colour['Red']
                            else:
                                if self.deviceInfo.anomaly_isTriggered(device_label) == True or self.deviceInfo.anomalyEPAnet_isTriggered(device_label):
                                    colour = self.state_to_colour['Anomaly']

                                if self.deviceInfo.alert_isTriggered(device_label) == True:
                                    colour = self.state_to_colour['Alert']

                        text += '<span class="name" style="color:' + colour + '">'

                        text += self.deviceInfo.property_observedAt_prettyprint_mapview(device_label, prop)

                        text += '</td>'

                        text += '<td>'
                        text += '<span class="name" style="color:' + colour + '">'

                        text += self.deviceInfo.sensorName(device_label)
                        text += '</td>'

                        text += '<td>'
                        text += '<span class="name" style="color:' + colour + '">'
                        text += self.deviceInfo.property_prettyprint(device_label, prop)
                        text += '</td>'

                        text += '<td>'
                        text += '<span class="name" style="color:' + colour + '">'

                        if self.deviceInfo.property_hasvalue(device_label, prop) == True:
                            text += self.deviceInfo.property_value_prettyprint(device_label, prop)
                            text += self.deviceInfo.property_unitCode_prettyprint(device_label, prop)
                        else:
                            text += 'N/A'

                        if visualise_alerts == True:
                            if colour == self.state_to_colour['Anomaly']:
                                if self.deviceInfo.anomalyEPAnet_isTriggered(device_label):
                                    text += '(EPA ANOMALY)'
                                else:
                                    text += '(ANOMALY)'

                            if colour == self.state_to_colour['Alert']:
                                text += '(ALERT)'

                        text += '</span>'
                        text += '<br>'
                        text += '</td>'

                        text += '</tr>'
                else:
                    for device_label in self.site_list[site_name]['devices']:

                        device = self.deviceInfo.device_get(device_label)
                        prop_list = unexefiware.model.get_controlled_properties(device)

                        for prop in prop_list:
                            if controlled_property_type == None or prop == controlled_property_type:

                                text += '<tr>'
                                text += '<td text-align: center;>'

                                colour = '#000000'

                                if visualise_alerts == True:
                                    if unexefiware.model.get_property_value(device, 'deviceState') == 'Red':
                                        colour = self.state_to_colour['Red']
                                    else:
                                        if self.deviceInfo.anomaly_isTriggered(device_label) == True or self.deviceInfo.anomalyEPAnet_isTriggered(device_label):
                                            colour = self.state_to_colour['Anomaly']

                                        if self.deviceInfo.alert_isTriggered(device_label) == True:
                                            colour = self.state_to_colour['Alert']

                                text += '<span class="name" style="color:' + colour + '">'

                                text += self.deviceInfo.property_observedAt_prettyprint_mapview(device_label, prop)

                                text += '</td>'

                                text += '<td>'
                                text += '<span class="name" style="color:' + colour + '">'

                                text += self.deviceInfo.sensorName(device_label)
                                text += '</td>'

                                text += '<td>'
                                text += '<span class="name" style="color:' + colour + '">'
                                text += self.deviceInfo.property_prettyprint(device_label, prop)
                                text += '</td>'

                                text += '<td>'
                                text += '<span class="name" style="color:' + colour + '">'

                                if self.deviceInfo.property_hasvalue(device_label, prop) == True:
                                    text += self.deviceInfo.property_value_prettyprint(device_label, prop)
                                    text += self.deviceInfo.property_unitCode_prettyprint(device_label, prop)
                                else:
                                    text += 'N/A'

                                if visualise_alerts == True:
                                    if colour == self.state_to_colour['Anomaly']:
                                        text += '(ANOMALY)'

                                    if colour == self.state_to_colour['Alert']:
                                        text += '(ALERT)'

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
