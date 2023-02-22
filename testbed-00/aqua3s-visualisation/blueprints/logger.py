from flask import request

from flask_cors import  cross_origin
from flask import Blueprint, render_template,  send_file

import unexeaqua3s.json
import blueprints.debug

import inspect
import datetime
import sqlite3
import os
import orjson

import unexefiware.base_logger
import unexefiware.time

blueprint = Blueprint('logger', __name__, template_folder='templates')

#--------------------------------------------------------------------------------------------------------------------------------------------------
@blueprint.route('/logging')
def analytics_page():
    access_token = request.args.get('access_token')

    return render_template("logging.html", access_token=access_token)

@blueprint.route('/get_log_data', methods=['GET'])
@cross_origin()
def get_log_data():
    try:
        data = []
        global logger

        for entry in logger.get_log_data():
            record = {}
            record['time'] = str(entry['time'])
            record['message'] = entry['message']
            if entry['line_no'] > 0:
                record['file'] = entry['file']+':'+str(entry['line_no'])
            else:
                record['file'] = ''

            data.append(record)

        payload = unexeaqua3s.json.dumps(data);
        blueprints.debug.dump_payload_to_disk('get_log_data()', payload)
        return payload
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return 'failed' + str(e), 500



