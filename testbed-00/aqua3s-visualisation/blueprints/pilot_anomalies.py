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

blueprint = Blueprint('anomalies_blueprint', __name__, template_folder='templates')
@blueprint.route('/pilot_anomalies')
def pilot_dashboard():
    try:
        access_token = request.args.get('access_token')

        if blueprints.keyrock_blueprint.ok(access_token):

            if blueprints.globals.is_service_available():
                return render_template("pilot_anomalies.html", access_token=access_token)
            else:
                return render_template("data_processing.html", access_token=access_token)

        return render_template("invalid.html")

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
    return "Record not found", 400

#get_current_anomalies
@blueprint.route('/get_current_anomalies', methods=['GET'])
def get_current_anomalies():
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
            device = deviceInfo.get_smart_model(device_id)

            if blueprints.orion_device.UNEXE_visualise(loc, device.is_UNEXETEST() ):
                #test code here
                if device.anomaly_isTriggered() == True:
                    record = {}
                    record['time'] = unexefiware.time.prettyprint_fiware(device.anomaly_observedAt())

                    record['device_id']   = device.model['id']
                    record['device_name'] = device.name()
                    record['print_name']  = device.sensorName()

                    record['property'] = device.property_prettyprint()
                    record['reason'] = device.anomalystatus_reason_prettyprint()
                    data.append(record)

                # test code here

        data = sorted(data, key=lambda k: k['print_name'])

        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return unexeaqua3s.json.dumps(data)

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return 'failed' + str(e), 500


@blueprint.route('/get_historic_anomalies', methods=['GET'])
def get_historic_anomalies():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')
        if blueprints.keyrock_blueprint.ok(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        data = []
        loc = blueprints.keyrock_blueprint.get_location(request.args.get('access_token'))

        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return unexeaqua3s.json.dumps(data)

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return 'failed' + str(e), 500

#get_anomaly_ranges
@blueprint.route('/get_anomaly_ranges', methods=['GET'])
def get_anomaly_ranges():
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
            device = deviceInfo.get_smart_model(device_id)

            if blueprints.orion_device.UNEXE_visualise(loc, device.is_UNEXETEST() ):
                # test code here
                record = {}
                record['device_name'] = device.name()
                record['device_id'] = device.model['id']
                record['print_name'] = device.sensorName()

                record['property'] = device.property_prettyprint()
                record['lower_limit'] = 'N/A'
                record['upper_limit'] = 'N/A'

                if device.property_hasvalue('whatever'):
                    fiware_datetime = device.property_observedAt()
                    if fiware_datetime != unexeaqua3s.deviceinfo.invalid_string:
                        date = unexefiware.time.fiware_to_datetime(fiware_datetime)
                        index = 0
                        index = int(date.strftime('%w')) * 3
                        index += int(date.hour / 8)

                    setting_data = device.anomalysetting_get()
                    if setting_data != None:
                        result = device.get_anomaly_raw_values(device.property_observedAt(), lerp=True)

                        record['lower_limit'] = result['min']
                        record['upper_limit'] = result['max']

                data.append(record)

                # test code here

        data = sorted(data, key=lambda k: k['print_name'])
        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return unexeaqua3s.json.dumps(data)

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return 'failed' + str(e), 500


@blueprint.route('/get_anomaly_settings', methods=['GET'])
def get_anomaly_settings():
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
            device = deviceInfo.get_smart_model(device_id)

            if blueprints.orion_device.UNEXE_visualise(loc, device.is_UNEXETEST()):
                # test code here
                record = {}
                record['device_name'] = device.name()
                record['device_id'] = device.model['id']

                record['prop_name'] = device.property_prettyprint()
                record['prop_units'] = device.property_unitCode_prettyprint()
                record['graph_title'] = record['device_name'] + ':' + record['prop_name']
                record['graph_subtitle'] = device.sensorName()

                record['series'] = []

                setting_data = device.anomalysetting_get()

                charting_support = unexeaqua3s.chartingsupport.ChartingSupport()

                min = []
                max = []
                average = []

                if setting_data != None:
                    for entry in setting_data['ranges']:
                        min.append(float(entry['min']))
                        max.append(float(entry['max']))
                        average.append(float(entry['average']))

                        charting_support.add_value(float(entry['min']))
                        charting_support.add_value(float(entry['max']))
                        charting_support.add_value(float(entry['average']))

                record['series'].append({'name': 'min', 'data': min})
                record['series'].append({'name': 'max', 'data': max})
                record['series'].append({'name': 'mean', 'data': average})

                record['xaxis-labels'] = []

                day= ['SUN','MON','TUE','WED','THU','FRI','SAT']

                for i in range(0, 21):
                    record['xaxis-labels'].append([ day[int(i/3)] + ' ' + str(((i % 3) * 8)).zfill(2) + ':00'])

                record['y_plotlines'] = [];

                if device.alertsetting_get_entry('current_max') != None:
                    record['y_plotlines'].append({'color': '#FF0000', 'width': 2, 'value': float(device.alertsetting_get_entry('current_max'))})
                    record['y_plotlines'].append({'color': '#FF00FF', 'width': 2, 'value': float(device.alertsetting_get_entry('current_min'))})

                    charting_support.add_value(device.alertsetting_get_entry('current_max'), is_limit=True)
                    charting_support.add_value(device.alertsetting_get_entry('current_min'), is_limit=True)
                else:
                    record['y_plotlines'].append({'color': '#FF0000', 'width': 2, 'value': float(0)})
                    record['y_plotlines'].append({'color': '#FF00FF', 'width': 2, 'value': float(0)})

                    charting_support.add_value(0, is_limit=True)
                    charting_support.add_value(0, is_limit=True)

                record['graph_range'] = charting_support.get_range()

                data.append(record)
                # test code here
        data = sorted(data, key=lambda k: k['graph_title'])

        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return unexeaqua3s.json.dumps(data)

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return 'failed' + str(e), 500
