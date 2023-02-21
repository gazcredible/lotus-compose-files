import copy
import datetime
import json
import os
os.environ['FILE_PATH'] = 'test/'

import unexefiware.time
import unexefiware.base_logger
import unexebroker.broker_flask


unexebroker.broker_flask.init(stellio_style=True, drop_all_tables=True, logger=unexefiware.base_logger.BaseLogger() )

def test_version_command():
    result = unexebroker.broker_globals.contextbroker.get_broker_data()

    assert len(result) == 2
    assert(result[0] == 200)

    payload = {"@context": "https://schema.lab.fiware.org/ld/context",
        "controlledProperty": {
            "type": "Property",
            "value": "flow"
        },
        "deviceState": {
            "type": "Property",
            "value": "Green"
        },
        "epanet_reference": {
            "type": "Property",
            "value": "{\"urn\": \"urn:ngsi-ld:Pipe:GP308\", \"epanet_id\": \"GP308\", \"epanet_type\": \"pipe\"}"
        },
        "flow": {
            "observedAt": "2022-08-18T16:45:00Z",
            "type": "Property",
            "unitCode": "G51",
            "value": "-0.0"
        },
        "id": "urn:ngsi-ld:Device:4C-flow",
        "location": {
            "type": "GeoProperty",
            "value": {
                "coordinates": [
                    91.67930695917889,
                    26.162501600397732
                ],
                "type": "Point"
            }
        },
        "name": {
            "type": "Property",
            "value": "4C"
        },
        "type": "Device"
    }

    fiware_service = 'TEST'

    entity_count = 1

    #create some entities
    for i in range(1,entity_count+1):
        payload["id"] =  "urn:ngsi-ld:Device:" + str(i)
        result = unexebroker.broker_globals.contextbroker.create_instance(payload,fiware_service)

        assert len(result) == 2
        assert (result[0] == 201)

    fiware_type = 'Device'
    inst_count = unexebroker.broker_globals.contextbroker.get_type(fiware_type, fiware_service)

    assert (entity_count == entity_count)

    result = unexebroker.broker_globals.contextbroker.get_by_index(fiware_type, 0, inst_count, fiware_service)

    assert len(result) == 2
    assert (result[0] == 200)
    assert(len(result[1]) == entity_count)

    #patch data
    patch_payload = copy.deepcopy({'flow':payload['flow']})
    patch_url = "urn:ngsi-ld:Device:1"
    patch_payload['flow']['observedAt'] = unexefiware.time.datetime_to_fiware(datetime.datetime.now())

    unexebroker.broker_globals.contextbroker.update_instance(patch_url, patch_payload, fiware_service)
    #update doesn't return, defaults to [204,'']
    #result = unexebroker.broker_globals.contextbroker.update_instance(patch_url ,patch_payload, fiware_service)
    #assert len(result) == 2
    #assert (result[0] == 200)

    #get temporal data
    fiware_start_time = '1970-01-01T00:00:00Z'
    fiware_end_time = unexefiware.time.datetime_to_fiware(datetime.datetime.now())
    fiware_attrs = 'flow'
    result = unexebroker.broker_globals.contextbroker.get_temporal_instance_stellio(fiware_service, patch_url, fiware_start_time, fiware_end_time, fiware_attrs)

    print()

    result = unexebroker.broker_globals.contextbroker.get_temporal_instance_orion(fiware_service, patch_url, fiware_start_time, fiware_end_time)

    print()