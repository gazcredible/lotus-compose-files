from flask import Blueprint, render_template
from flask import jsonify
from flask import request
from flask_cors import  cross_origin
import inspect
import json
import unexebroker.broker_globals

blueprint = Blueprint('broker_flask', __name__, template_folder='templates')

import unexebroker.broker

def init(stellio_style = False, drop_all_tables=False, logger = None):

    unexebroker.broker_globals.global_drop_all_tables = drop_all_tables
    unexebroker.broker_globals.global_stellio_style = stellio_style

    if logger:
        unexebroker.broker_globals.global_logger = logger

    unexebroker.broker_globals.contextbroker = unexebroker.broker.ContextBroker(stellio_style=unexebroker.broker_globals.global_stellio_style)
    unexebroker.broker_globals.contextbroker.logger = unexebroker.broker_globals.global_logger
    unexebroker.broker_globals.contextbroker.init(drop_all_tables=unexebroker.broker_globals.global_drop_all_tables)


#-------------------------------------------------------------------------------------------------------------------------------------
#my shonky commands
@blueprint.route('/unexe-broker/v1/erase_broker', methods=['POST'])
@cross_origin()
def erase_broker():
    try:
        unexebroker.broker_globals.contextbroker = unexebroker.broker.ContextBroker(stellio_style=unexebroker.broker_globals.global_stellio_style)
        unexebroker.broker_globals.contextbroker.init(drop_all_tables=True)
        return '',200

    except Exception as e:
        unexebroker.broker_globals.contextbroker.logger.fail(inspect.currentframe(), str(e))
        return unexebroker.broker_globals.contextbroker.logger.formatmsg(inspect.currentframe(), str(e)), 500

#gareth - use this to start processing subscriptions once the backlog has been built
@blueprint.route('/ngsi-ld/v1/enable_subscriptions', methods=['POST'])
@cross_origin()
def enable_subscriptions():
    try:

        unexebroker.broker_globals.contextbroker.logger.log(inspect.currentframe(), 'Subscription Processing ENABLED!')
        unexebroker.broker_globals.contextbroker.process_subscriptions = True
        return '',200

    except Exception as e:
        unexebroker.broker_globals.contextbroker.logger.fail(inspect.currentframe(), str(e))
        return unexebroker.broker_globals.contextbroker.logger.formatmsg(inspect.currentframe(), str(e)), 500

@blueprint.route('/ngsi-ld/v1/disable_subscriptions', methods=['POST'])
@cross_origin()
def disable_subscriptions():
    try:

        unexebroker.broker_globals.contextbroker.logger.log(inspect.currentframe(), 'Subscription Processing DISABLED!')
        unexebroker.broker_globals.contextbroker.process_subscriptions = False
        return '',200

    except Exception as e:
        unexebroker.broker_globals.contextbroker.logger.fail(inspect.currentframe(), str(e))
        return unexebroker.broker_globals.contextbroker.logger.formatmsg(inspect.currentframe(), str(e)), 500

#-------------------------------------------------------------------------------------------------------------------------------------
# proper ngsildv1 commands
@blueprint.route('/ngsi-ld/v1/entities', methods=['GET','POST'])
@cross_origin()
def entities():

    try:
        fiware_service = 'default'
        if 'fiware-service' in request.headers:
            fiware_service = request.headers['fiware-service']

        if request.method == 'POST':
            payload = json.loads(request.data)
            result = unexebroker.broker_globals.contextbroker.create_instance(payload, fiware_service)
            return result[1], result[0]

        if request.method == 'GET':
            fiware_type = request.args['type']
            limit  = int(request.args.get('limit',-1))
            offset = int(request.args.get('offset',-1))

            if limit!=-1 and offset !=-1:
                result = unexebroker.broker_globals.contextbroker.get_by_index(fiware_type,offset, limit, fiware_service)
                return jsonify(result[1]), result[0]

            inst_count = unexebroker.broker_globals.contextbroker.get_type(fiware_type, fiware_service)
            result = unexebroker.broker_globals.contextbroker.get_by_index(fiware_type, 0, inst_count, fiware_service)
            return jsonify(result[1]), result[0]

    except Exception as e:
        unexebroker.broker_globals.contextbroker.logger.fail(inspect.currentframe(), str(e))
        return unexebroker.broker_globals.contextbroker.logger.formatmsg(inspect.currentframe(), str(e)), 500

    return unexebroker.broker_globals.contextbroker.logger.formatmsg(inspect.currentframe(), ''), 500


@blueprint.route('/ngsi-ld/v1/entities/<urn>', methods=['GET','DELETE'])
@cross_origin()
def entities_urn(urn):
    try:
        global contextbroker
        if request.method == 'GET':
            fiware_service = 'default'
            if 'fiware-service' in request.headers:
                fiware_service = request.headers['fiware-service']

            result = unexebroker.broker_globals.contextbroker.get_instance(urn,fiware_service)

            return jsonify(result[1])

        if request.method == 'DELETE':
            fiware_service = 'default'
            if 'fiware-service' in request.headers:
                fiware_service = request.headers['fiware-service']

            result = unexebroker.broker_globals.contextbroker.delete_instance(urn,fiware_service)

            return result[1], result[0]
    except Exception as e:
        unexebroker.broker_globals.contextbroker.logger.fail(inspect.currentframe(), str(e))
        return unexebroker.broker_globals.contextbroker.logger.formatmsg(inspect.currentframe(), str(e)), 500

    return unexebroker.broker_globals.contextbroker.logger.formatmsg(inspect.currentframe(), ''), 500

@blueprint.route('/ngsi-ld/v1/entities/<urn>/attrs', methods=['PATCH'])
@cross_origin()
def patch_entities_urn(urn):
    try:
        global contextbroker
        fiware_service = 'default'
        if 'fiware-service' in request.headers:
            fiware_service = request.headers['fiware-service']

        payload_data = json.loads(request.data)

        if isinstance(payload_data, list):
            unexebroker.broker_globals.contextbroker.update_instances(urn, json.loads(request.data), fiware_service)
        else:
            unexebroker.broker_globals.contextbroker.update_instance(urn, json.loads(request.data), fiware_service)

        return '',204
    except Exception as e:
        unexebroker.broker_globals.contextbroker.logger.fail(inspect.currentframe(), str(e))
        return unexebroker.broker_globals.contextbroker.logger.formatmsg(inspect.currentframe(), str(e)), 500

@blueprint.route('/ngsi-ld/v1/temporal/entities/<urn>', methods=['GET'])
@cross_origin()
def temporal_entities(urn):

    try:
        fiware_service = 'default'
        if 'fiware-service' in request.headers:
            fiware_service = request.headers['fiware-service']

        device_id = urn
        fiware_start_time = request.args['time']
        fiware_end_time = request.args['endTime']

        fiware_attrs = []

        if 'attrs' in request.args:
            fiware_attrs = request.args['attrs']

            return jsonify(unexebroker.broker_globals.contextbroker.get_temporal_instance_stellio(fiware_service, device_id, fiware_start_time, fiware_end_time,fiware_attrs))
        else:
            return jsonify(unexebroker.broker_globals.contextbroker.get_temporal_instance_orion(fiware_service, device_id, fiware_start_time, fiware_end_time))

    except Exception as e:
        unexebroker.broker_globals.contextbroker.logger.fail(inspect.currentframe(), str(e))
        return unexebroker.broker_globals.contextbroker.logger.formatmsg(inspect.currentframe(), str(e)), 500

@blueprint.route('/ngsi-ld/v1/types/<entity_type>', methods=['GET'])
@cross_origin()
def do_types(entity_type):
    try:
        fiware_service = 'default'
        if 'fiware-service' in request.headers:
            fiware_service = request.headers['fiware-service']

        inst_count = unexebroker.broker_globals.contextbroker.get_type(entity_type, fiware_service)

        return jsonify({'entityCount': inst_count})

    except Exception as e:
        unexebroker.broker_globals.contextbroker.logger.fail(inspect.currentframe(), str(e))
        return unexebroker.broker_globals.contextbroker.logger.formatmsg(inspect.currentframe(), str(e)), 500

