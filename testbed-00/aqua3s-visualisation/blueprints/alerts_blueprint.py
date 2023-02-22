from flask import request
from flask import Flask
from flask import render_template
from flask import request
from flask_cors import CORS, cross_origin
from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound


import unexeaqua3s.json
import time
import requests
import inspect
import datetime
import os

import unexefiware.ngsildv1
import unexefiware.time

import unexeaqua3s.deviceinfo
import unexeaqua3s.workhorse_backend

import blueprints.debug
import blueprints.orion_device
import blueprints.keyrock_blueprint
import blueprints.resourcemanager
import blueprints.analytics_blueprint
import blueprints.globals

def my_float(val:float):
    try:
        return float(val)
    except Exception as e:
        return 0.0


blueprint = Blueprint('alerts_blueprint', __name__, template_folder='templates')


@blueprint.route('/alerts')
def alerts_page():
    blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
    access_token = request.args.get('access_token')

    if blueprints.keyrock_blueprint.ok(access_token) and blueprints.keyrock_blueprint.get_is_analtyics_available(access_token):

        if blueprints.globals.is_service_available():
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            #GARETH - to do! set epanomalies tag here for alerts screen
            return render_template("alerts.html", access_token=access_token, epa_pilot_data=blueprints.keyrock_blueprint.get_alert_info(access_token))
        else:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return render_template("data_processing.html", access_token=access_token)

    return render_template("invalid.html")

@blueprint.route('/get_alert_data', methods=['GET'])
def get_alert_data():
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

            if device_id == 'UNEXE_TEST_76':
                print()

            if blueprints.orion_device.UNEXE_visualise(loc, device.is_UNEXETEST()):
                #test code here
                for prop in unexefiware.model.get_controlled_properties(device.model):
                    record = {}
                    record['device_id'] = device.model['id']
                    record['device_name'] = device.sensorName()
                    record['property'] = prop
                    record['property_print_name'] = device.property_prettyprint(prop)

                    if record['property_print_name'] != '' and device.property_unitCode_prettyprint(prop) != '' and device.property_unitCode_prettyprint(prop) != ' ':
                        record['property_print_name'] += '<br>'
                        record['property_print_name'] += ' (' + device.property_unitCode_prettyprint(prop) + ')'

                    record['current_prop_reading'] = device.property_observedAt_prettyprint(prop)
                    record['time'] = device.alert_observedAt_prettyprint()

                    record['min'] = my_float(device.alertsetting_get_entry('min'))
                    record['max'] = my_float(device.alertsetting_get_entry('max'))
                    record['step'] = my_float(device.alertsetting_get_entry('step'))
                    try:
                        record['current_min'] = my_float(device.alertsetting_get_entry('current_min'))
                        record['current_max'] = my_float(device.alertsetting_get_entry('current_max'))
                    except Exception as e:

                        record['current_min'] = -9999
                        record['current_max'] = 9999

                    if device.alertsetting_get_entry('active') is not None:
                        record['active'] = device.alertsetting_get_entry('active').lower() == 'true'
                    else:
                        record['active'] = True

                    #current state data
                    record['triggered'] =device.alert_isTriggered()
                    record['alert_reason'] = device.alertstatus_reason_prettyprint()

                    record['current_print_value'] = device.property_value_prettyprint(prop)
                    record['current_print_value'] += ' ' + device.property_unitCode_prettyprint(prop)

                    data.append(record)
                # test code here

        data = sorted(data, key=lambda k: k['device_name'])
        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return 'failed' + str(e), 500

    return unexeaqua3s.json.dumps(data)

@blueprint.route('/set_alert', methods=['POST'])
@cross_origin()
def post_alert():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))

        request_data = unexeaqua3s.json.loads(request.data.decode("utf-8") )
        access_token = request_data['access_token']

        if blueprints.keyrock_blueprint.ok(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid',403

        loc = blueprints.keyrock_blueprint.get_location(access_token)

        deviceInfo = blueprints.orion_device.get_deviceInfo(loc)

        if request_data['item']['device_id'] in deviceInfo.deviceInfoList:
            device_model = deviceInfo.get_smart_model(request_data['item']['device_id'])
            device_model.alertsettings_update_and_patch(loc, request_data['item']['current_min'], request_data['item']['current_max'], request_data['item']['active'])

            unexeaqua3s.workhorse_backend.device_update(loc, device_model.model['id'], logger = blueprints.debug.servicelog)

            blueprints.orion_device.force_update(loc)

        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return 'OK', 200

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return 'failed' + str(e), 500

    return 'failed', 500


@blueprint.route('/get_historic_alert_data', methods=['GET'])
def get_historic_alert_data():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')

        if blueprints.keyrock_blueprint.ok(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid',403

        data = []
        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return unexeaqua3s.json.dumps(data)

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e)
        return 'failed' + str(e), 500


@blueprint.route('/get_giota_data', methods=['GET'])
def get_giota_data():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')

        if blueprints.keyrock_blueprint.ok(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid',403

        loc = blueprints.keyrock_blueprint.get_location(request.args.get('access_token'))
        deviceInfo = blueprints.orion_device.get_deviceInfo(loc)

        data = deviceInfo.get_alert_data_for_giota()
        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return unexeaqua3s.json.dumps(data)

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e)
        return 'failed' + str(e), 500


@blueprint.route('/get_certh_alert_data', methods=['GET'])
def get_certh_alert_data():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')

        if blueprints.keyrock_blueprint.ok(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid',403

        loc = blueprints.keyrock_blueprint.get_location(request.args.get('access_token'))
        return unexeaqua3s.json.dumps(blueprints.orion_device.get_certh_alert(loc))

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e)
        return 'failed' + str(e), 500




