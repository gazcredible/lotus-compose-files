from flask import Flask
from flask import render_template
from flask import request
from flask_cors import CORS, cross_origin
from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

import unexeaqua3s.json
import time
from functools import cmp_to_key

import blueprints.globals
import blueprints.debug
import blueprints.orion_device
import blueprints.keyrock_blueprint
import blueprints.resourcemanager
import blueprints.analytics_blueprint
import inspect
import unexefiware.model
import unexefiware.time
import requests
import datetime
import unexeaqua3s.deviceinfo
import unexeaqua3s.epanomalies
import unexeaqua3s.chartingsupport

blueprint = Blueprint('epanetanomalies_blueprint', __name__, template_folder='templates')

@blueprint.route('/get_current_epanetanomalies', methods=['GET'])
def get_current_epanetanomalies():
    try:

        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')

        if blueprints.keyrock_blueprint.ok(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        data = []

        loc = blueprints.keyrock_blueprint.get_location(request.args.get('access_token'))

        deviceInfo = blueprints.orion_device.get_deviceInfo(loc)

        for device_id in deviceInfo.deviceInfoList:
            # test code here
            device = deviceInfo.get_smart_model(device_id)

            if device.epanomaly_isTriggered() == True:
                record = {}
                record['time'] = device.epanomaly_observedAt_prettyprint()

                record['device_id'] = device_id
                record['device_name'] = device.name()
                record['print_name'] = device.sensorName()

                record['property'] = device.property_prettyprint()
                record['reason'] = device.epanomalystatus_reason_prettyprint()
                data.append(record)

            # test code here

        data = sorted(data, key=lambda k: k['print_name'])

        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return unexeaqua3s.json.dumps(data)

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return 'failed' + str(e), 500


@blueprint.route('/get_historic_epanetanomalies', methods=['GET'])
def get_historic_epanetanomalies():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')
        if blueprints.keyrock_blueprint.ok(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        data = []
        loc = blueprints.keyrock_blueprint.get_location(request.args.get('access_token'))

        deviceInfo = blueprints.orion_device.get_deviceInfo(loc)

        if False:
            for device_id in deviceInfo.deviceInfoList:
                device = deviceInfo.device_get(device_id)

                record = {}
                record['time'] = unexefiware.time.datetime_to_fiware(datetime.datetime.now())
                record['time'] = record['time'].replace('Z' ,' ')
                record['time'] = record['time'].replace('T', ' ')

                record['device_id'] = device['id']
                record['device_name'] = device['name']['value']

                record['print_name'] = deviceInfo.sensorName(device_id)
                record['property'] = deviceInfo.property_prettyprint(device_id)

                index = 0

                if deviceInfo.property_hasvalue(device_id, 'whatever'):

                    fiware_datetime = deviceInfo.property_observedAt(device_id)

                    if fiware_datetime != deviceInfo.invalid_string():
                        date = unexefiware.time.fiware_to_datetime(fiware_datetime)

                        index = int(date.strftime('%w')) * 3
                        index += int(date.hour / 8)

                setting_data = deviceInfo._get_value_data(device_id, 'anomalySetting')

                record['reason'] = 'limitType'
                record['reason'] += ' value:'
                record['reason'] += deviceInfo.property_value(device_id)
                record['reason'] += ' limit:'

                if setting_data != None:
                    record['reason'] += str(round(setting_data[index]['min'],2))
                    record['reason'] += '-'
                    record['reason'] += str(round(setting_data[index]['max'],2))
                    record['reason'] += ' '
                    record['reason'] += deviceInfo.property_unitCode_prettyprint(device_id)
                else:
                    record['reason'] += ' N/A'
                data.append(record)

        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return unexeaqua3s.json.dumps(data)

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return 'failed' + str(e), 500


@blueprint.route('/get_current_epanomaly_readings', methods=['GET'])
def get_current_epanomaly_readings():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')
        if blueprints.keyrock_blueprint.ok(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        data = []
        loc = blueprints.keyrock_blueprint.get_location(request.args.get('access_token'))

        deviceInfo = blueprints.orion_device.get_deviceInfo(loc)

        for device_id in deviceInfo.deviceModelList:
            device = deviceInfo.get_smart_model(device_id)

            if device.isEPANET():
                for prop in unexefiware.model.get_controlled_properties(device.model):
                    record = {}
                    record['device_id'] = device.model['id']
                    record['device_name'] = device.sensorName()
                    record['property'] = prop
                    record['property_print_name'] = device.property_prettyprint(prop)

                    if record['property_print_name'] != '' and device.property_unitCode_prettyprint(prop) != '' and device.property_unitCode_prettyprint(prop) != ' ':
                        record['property_print_name'] += '<br>'
                        record['property_print_name'] += ' (' + device.property_unitCode_prettyprint(prop) + ')'

                    record['time'] = device.epanomaly_observedAt_prettyprint()
                    #current state data
                    record['current_print_value'] = device.property_value_prettyprint()
                    record['current_print_value'] += ' ' + device.property_unitCode_prettyprint()

                    data.append(record)

        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return unexeaqua3s.json.dumps(data)

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return 'failed' + str(e), 500

@blueprint.route('/get_epanomaly_settings', methods=['GET'])
def get_epanomaly_settings():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')
        if blueprints.keyrock_blueprint.ok(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        data = []

        loc = blueprints.keyrock_blueprint.get_location(request.args.get('access_token'))

        deviceInfo = blueprints.orion_device.get_deviceInfo(loc)

        epanomalies = unexeaqua3s.epanomalies.EPAnomalies(loc)
        epanomalies.load_data()

        for device_id in deviceInfo.deviceInfoList:
            device = deviceInfo.get_smart_model(device_id)

            if blueprints.orion_device.UNEXE_visualise(loc, device.is_UNEXETEST()) and device.isEPANET():
                # test code here
                record = {}
                record['device_name'] = device.name()
                record['device_id'] = device.model['id']

                record['prop_name'] = device.property_prettyprint()
                record['prop_units'] = device.property_unitCode_prettyprint()
                record['graph_title'] = record['device_name'] + ':' + record['prop_name']
                record['graph_subtitle'] = device.sensorName()
                record['tick_interval'] = 10;

                record['series'] = []

                avg_valuesDB = epanomalies.anomaly_modelData['avg_values_DB'][epanomalies.anomaly_modelData['avg_values_DB'].Sensor_ID == device.EPANET_id()]

                min = []
                max = []
                average = []

                charting_support = unexeaqua3s.chartingsupport.ChartingSupport()

                record['xaxis-labels'] = []
                in_range = True

                date = datetime.datetime(2022,8,7)
                while in_range:
                    week_time = date.strftime("%A-%H:%M")
                    avg_value = avg_valuesDB.Read_avg[avg_valuesDB.timestamp == week_time].iloc[0]

                    charting_support.add_value(avg_value)

                    record['xaxis-labels'].append([str(week_time)])
                    average.append(avg_value)

                    date += datetime.timedelta(minutes=60)

                    in_range = not (date.day > 13)

                record['series'].append({'name': 'mean', 'data': average})

                record['y_plotlines'] = [];
                if device.alertsetting_get_entry('current_max') is not None:
                    record['y_plotlines'].append({'color': '#FF0000','width': 2,'value': float(device.alertsetting_get_entry('current_max'))})

                if device.alertsetting_get_entry('current_min') is not None:
                    record['y_plotlines'].append({'color': '#FF00FF', 'width': 2, 'value': float(device.alertsetting_get_entry('current_min'))})

                #charting_support.add_value(device.alertsetting_get_entry('current_max'),is_limit=True)
                #charting_support.add_value(device.alertsetting_get_entry('current_min'), is_limit=True)

                record['graph_range'] = charting_support.get_range()

                data.append(record)
                # test code here
        data = sorted(data, key=lambda k: k['graph_title'])

        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return unexeaqua3s.json.dumps(data)

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return 'failed' + str(e), 500
