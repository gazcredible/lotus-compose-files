from flask import request
from flask_cors import  cross_origin
from flask import Blueprint, render_template

import unexeaqua3s.json
import datetime
import inspect
import os

import blueprints.globals
import blueprints.keyrock_blueprint
import blueprints.debug
import unexeaqua3s.service_chart

import blueprints.orion_device
blueprint = Blueprint('analytics_blueprint', __name__, template_folder='templates')


def init():
    pass

@blueprint.route('/analytics')
def analytics_page():
    blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
    access_token = request.args.get('access_token')

    if blueprints.keyrock_blueprint.ok(access_token) and blueprints.keyrock_blueprint.get_is_analtyics_available(access_token):
        global chart_processor
        if blueprints.globals.is_service_available():
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return render_template("analytics.html", access_token=access_token)
        else:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return render_template("data_processing.html", access_token=access_token)

    return render_template("invalid.html")


#for a give property, return all the sensors (and data) that have that prop
@blueprint.route('/get_chart_sensor_by_prop', methods=['GET'])
@cross_origin()
def get_chart_sensor_by_prop():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')
        if blueprints.keyrock_blueprint.ok(access_token) == False or blueprints.keyrock_blueprint.get_is_analtyics_available(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        loc = blueprints.keyrock_blueprint.get_location(request.args.get('access_token'))
        prop = request.args.get('property')
        time_mode = request.args.get('time_mode')

        chartingService = unexeaqua3s.service_chart.ChartService()
        data = chartingService.get_sensor_by_properties(blueprints.orion_device.get_deviceInfo(loc), time_mode, prop, visualiseUNEXE = blueprints.orion_device.UNEXE_visualise_enabled(loc))

        payload = unexeaqua3s.json.dumps(data)
        blueprints.debug.dump_payload_to_disk('get_chart_sensor_by_prop(' + loc + ')', payload)

        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return payload

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return 'failed' + str(e), 500


@blueprint.route('/get_chart_prop_by_sensor', methods=['GET'])
@cross_origin()
def get_chart_prop_by_sensor():
    try:

        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')
        if blueprints.keyrock_blueprint.ok(access_token) == False or blueprints.keyrock_blueprint.get_is_analtyics_available(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        loc = blueprints.keyrock_blueprint.get_location(request.args.get('access_token'))
        time_mode = request.args.get('time_mode')

        chartingService = unexeaqua3s.service_chart.ChartService()
        data = chartingService.get_properties_by_sensor(blueprints.orion_device.get_deviceInfo(loc), time_mode, visualiseUNEXE = blueprints.orion_device.UNEXE_visualise_enabled(loc))

        payload = unexeaqua3s.json.dumps(data)
        blueprints.debug.dump_payload_to_disk('get_chart_prop_by_sensor('+loc+')', payload)

        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return payload
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return 'failed' + str(e), 500