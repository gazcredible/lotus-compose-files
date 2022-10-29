from flask import Blueprint, render_template
from flask import jsonify
from flask import request
from flask_cors import  cross_origin
import inspect
import  unexefiware.base_logger
import json

import unexebroker.broker



blueprint = Blueprint('unexe_broker', __name__, template_folder='templates')

@blueprint.route('/unexe-broker/v1/version', methods=['GET'])
@cross_origin()
def unexebroker_version():


    try:
        result = unexebroker.broker_globals.contextbroker.get_broker_data()
        return jsonify(result[1]), result[0]

        return '',200

    except Exception as e:
        unexebroker.broker_globals.contextbroker.logger.exception(inspect.currentframe(),e)
        return unexebroker.broker_globals.contextbroker.logger.formatmsg(inspect.currentframe(), str(e)), 500

    return unexebroker.broker_globals.logger.formatmsg(inspect.currentframe(), ''), 500

@blueprint.route('/unexe-broker/v1/erase_broker', methods=['POST'])
@cross_origin()
def erase_broker():

    try:
        unexebroker.broker_globals.contextbroker.init(drop_all_tables=True)
        unexebroker.broker_globalscontextbroker.logger.print_request(request, 200)
        return '',200

    except Exception as e:
        unexebroker.broker_globals.contextbroker.logger.fail(inspect.currentframe(), str(e))
        return unexebroker.broker_globals.contextbroker.logger.formatmsg(inspect.currentframe(), str(e)), 500

    return unexebroker.broker_globals.contextbroker.logger.formatmsg(inspect.currentframe(), ''), 500
