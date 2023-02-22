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

blueprint = Blueprint('imm_blueprint', __name__, template_folder='templates')

import blueprints.imm_processor

imm_processor = blueprints.imm_processor.IMMProcessor()

def one_time_init():
    global imm_processor

    imm_processor.init(logger = blueprints.debug.servicelog)

@blueprint.route('/imm')
def imm_page():
    access_token = request.args.get('access_token')

    if blueprints.keyrock_blueprint.ok(access_token) and blueprints.keyrock_blueprint.get_is_mapview_available(access_token):

        if blueprints.globals.is_service_available():
            return render_template("imm.html", access_token=access_token)
        else:
            return render_template("data_processing.html", access_token=access_token)

    return render_template("invalid.html")


@blueprint.route('/get_imm_data')
def get_imm_data():

    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')

        if blueprints.keyrock_blueprint.ok(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        loc = blueprints.keyrock_blueprint.get_location(request.args.get('access_token'))

        global imm_processor
        if imm_processor.has_epanet(loc) == False:
            #load epanet ...
            imm_processor.load_epanet(loc, blueprints.globals.fiware_resources.resources[loc]['epanet'])

        data = imm_processor.get_client_data(loc)

        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return unexeaqua3s.json.dumps(data)

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e)
        return 'failed' + str(e), 500


@blueprint.route('/post_imm_start', methods=['POST'])
@cross_origin()
def post_imm_start():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))

        request_data = unexeaqua3s.json.loads(request.data)
        access_token = request_data['access_token']

        if blueprints.keyrock_blueprint.ok(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        request_data = unexeaqua3s.json.loads(request.data)
        loc = blueprints.keyrock_blueprint.get_location(access_token)

        #do stuff here!
        global imm_processor
        if imm_processor.start(loc, request_data['selected_pipe'], request_data['repair_duration'], request_data['max_number_of_solutions']) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        data = imm_processor.get_client_data(loc)

        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return unexeaqua3s.json.dumps(data)

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e)
        return 'failed' + str(e), 500

    return 'failed', 500


@blueprint.route('/post_imm_reset', methods=['POST'])
@cross_origin()
def post_imm_reset():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))

        request_data = unexeaqua3s.json.loads(request.data)
        access_token = request_data['access_token']

        if blueprints.keyrock_blueprint.ok(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        request_data = unexeaqua3s.json.loads(request.data)
        loc = blueprints.keyrock_blueprint.get_location(access_token)

        #do stuff here!
        global imm_processor
        if imm_processor.reset(loc) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        data = imm_processor.get_client_data(loc)
        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return unexeaqua3s.json.dumps(data)

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e)
        return 'failed' + str(e), 500

    return 'failed', 500
