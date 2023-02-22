import requests
import json

default_timeout = 9999

def return_response(r):
    if r.ok:
        if len(r.text) > 0:
            try:
                return [r.status_code, json.loads(r.text)]
            except Exception as e:
                return [-1, str(e)] #something bad happened
        else:
            return [r.status_code, '']

    return [r.status_code, r.text]


# ------------------------------------------------------------------------------------------------------------------------------------------
# orion style methods
def create_instance(session, url, data, fiware_service=None):
    headers = {}
    headers['Content-Type'] = 'application/ld+json'

    if fiware_service != None:
        headers['fiware-service'] = fiware_service

    path = url + '/ngsi-ld/v1/entities'

    try:
        r = session.post(path, data=data, headers=headers, timeout=default_timeout)

        return return_response(r)

    except Exception as e:
        return [-1, str(e)]


def get_instance(session, url, id, link, fiware_service=None):
    headers = {}

    if link[0] == '<':
        headers['Link'] = link
    else:
        headers['Link'] = '<' + link + '>'

    if fiware_service != None:
        headers['fiware-service'] = fiware_service

    try:
        r = session.get(url + '/ngsi-ld/v1/entities/' + id, headers=headers, timeout=default_timeout)

        return return_response(r)

    except Exception as e:
        return [-1, str(e)]


def delete_instance(session, url, id, link, fiware_service=None):
    headers = {}

    if link[0] == '<':
        headers['Link'] = link
    else:
        headers['Link'] = '<' + link + '>'

    if fiware_service != None:
        headers['fiware-service'] = fiware_service

    try:
        r = session.delete(url + '/ngsi-ld/v1/entities/' + id, headers=headers, timeout=default_timeout)

        return return_response(r)

    except Exception as e:
        return [-1, str(e)]


def patch_instance_orion(session, url, id, data, link, fiware_service):
    try:
        headers = {}
        headers['Content-Type'] = 'application/json'

        if link[0] == '<':
            headers['Link'] = link
        else:
            headers['Link'] = '<' + link + '>'

        if fiware_service != None:
            headers['fiware-service'] = fiware_service

        r = session.patch(url + '/ngsi-ld/v1/entities/' + id + '/attrs', data=data, headers=headers)

        return return_response(r)

    except Exception as e:
        return [-1, str(e)]



def get_type(session, url, type, link, fiware_service=None):
    headers = {}
    if link[0] == '<':
        headers['Link'] = link
    else:
        headers['Link'] = '<' + link + '>'

    if fiware_service != None:
        headers['fiware-service'] = fiware_service

    params = {}
    params['type'] = type

    try:
        r = session.get(url + '/ngsi-ld/v1/entities', params=params, headers=headers, timeout=default_timeout)

        return return_response(r)

    except Exception as e:
        return [-1, str(e)]


def get_type_keyvalues(session, url, type, link, fiware_service=None):
    headers = {}
    headers['Link'] = link

    if fiware_service != None:
        headers['fiware-service'] = fiware_service

    params = {}
    params['type'] = type
    params['options'] = 'keyValues'

    try:
        r = session.get(url + '/ngsi-ld/v1/entities', params=params, headers=headers, timeout=default_timeout)

        return return_response(r)

    except Exception as e:
        return [-1, str(e)]


def get_type_count_orionld(session, url, type, link=None, fiware_service=None):
    headers = {}
    headers = {}
    headers['Accept'] = 'application/ld+json'

    if link != None:
        if link[0] == '<':
            headers['Link'] = link
        else:
            headers['Link'] = '<' + link + '>'
    else:
        headers['Content-Type'] = 'application/ld+json'

    if fiware_service != None:
        headers['fiware-service'] = fiware_service

    try:
        r = session.get(url + '/ngsi-ld/v1/types/' + type, headers=headers, timeout=default_timeout)
        return return_response(r)

    except Exception as e:
        return [-1, str(e)]


def get_type_by_index_orionld(session, url, type, index, link=None, fiware_service=None, limit=1):
    # this is for orion-ld, stellio does this differently :S
    try:
        params = {'type': type,
                  'limit': limit,
                  'offset': index
                  }

        headers = {}
        headers['Accept'] = 'application/ld+json'

        if link != None:
            if link[0] == '<':
                headers['Link'] = link
            else:
                headers['Link'] = '<' + link + '>'
        else:
            headers['Content-Type'] = 'application/ld+json'

        if fiware_service != None:
            headers['fiware-service'] = fiware_service

        r = session.get(url + '/ngsi-ld/v1/entities', headers=headers, params=params, timeout=default_timeout)
        return return_response(r)

    except Exception as e:
        return [-1, str(e)]


def get_temporal_orion(session, url, id, link, start_date, end_date, fiware_service=None):
    try:
        headers = {}
        #gareth -   do we need this for orion-ld?
        # headers['Link'] = link

        if fiware_service != None:
            headers['fiware-service'] = fiware_service


        params = {}
        params['timerel'] = 'between'
        params['time'] = start_date
        params['endTime'] = end_date

        r = session.get(url + '/ngsi-ld/v1/temporal/entities/' + id, params=params, headers=headers, timeout=default_timeout)

        return return_response(r)
    except Exception as e:
        return [-1, str(e)]



def get_all_orion(session, url, label, link, fiware_service=None):
    try:
        result = get_type_count_orionld(session, url, label, link, fiware_service)

        if result[0] == 200:
            if 'entityCount' in result[1]:
                entityCount = int(result[1]['entityCount'])

                return get_type_by_index_orionld(session, url, label, 0, link, fiware_service=fiware_service, limit=entityCount)

        return result

    except Exception as e:
        return [-1, str(e)]


# ------------------------------------------------------------------------------------------------------------------------------------------
# Stellio-style methods
def create_instance_stellio(session, url, json_data, fiware_service=None):
    try:
        headers = {}
        headers['Content-Type'] = 'application/ld+json'

        if fiware_service:
            headers['fiware-service'] = fiware_service

        path = url + '/ngsi-ld/v1/entities/' + json_data['id']

        r = session.post(path, data=json.dumps(json_data), headers=headers, timeout=default_timeout)

        return return_response(r)

    except Exception as e:
        return [-1, str(e)]


def get_instance_stellio(session, url, id, link, fiware_service=None):
    try:
        headers = {}
        headers['Link'] = link

        if fiware_service:
            headers['fiware-service'] = fiware_service

        r = session.get(url + '/ngsi-ld/v1/entities/' + id, headers=headers, timeout=default_timeout)

        return return_response(r)

    except Exception as e:
        return [-1, str(e)]


def delete_instance_stellio(session, url, id, link, fiware_service=None):
    try:
        headers = {}
        headers['Link'] = link

        if fiware_service:
            headers['fiware-service'] = fiware_service

        r = session.delete(url + '/ngsi-ld/v1/entities/' + id, headers=headers, timeout=default_timeout)

        return return_response(r)

    except Exception as e:
        return [-1, str(e)]


def patch_instance_stellio(session, url, id, link, data):
    try:
        headers = {}
        headers['Content-Type'] = 'application/json'
        headers['Link'] = link

        r = session.patch(url + '/ngsi-ld/v1/entities/' + id + '/attrs', data=data, headers=headers)

        return return_response(r)

    except Exception as e:
        return [-1, str(e)]


def get_all_type_stellio(session, url, type, link, fiware_service=None):
    try:
        headers = {}
        headers['Link'] = link

        if fiware_service:
            headers['fiware-service'] = fiware_service

        params = {}
        params['type'] = type

        r = session.get(url + '/ngsi-ld/v1/entities', params=params, headers=headers, timeout=default_timeout)

        return return_response(r)

    except Exception as e:
        return [-1, str(e)]


def get_type_count_stellio(session, url, type, link, fiware_service=None):
    try:
        headers = {}
        headers['Accept'] = 'application/ld+json'
        headers['Content-Type'] = 'application/ld+json'

        headers['link'] = link

        if fiware_service:
            headers['fiware-service'] = fiware_service

        r = session.get(url + '/ngsi-ld/v1/types/' + type, headers=headers, timeout=default_timeout)

        return return_response(r)

    except Exception as e:
        return [-1, str(e)]


def get_type_by_index_stellio(session, url, type, link, index, fiware_service=None, limit=1):
    try:
        params = {'type': type,
                  'limit': 1,
                  'count': True,
                  'page': index,  # this may use offset too :S
                  'offset': index - 1
                  }

        headers = {}
        headers['Accept'] = 'application/ld+json'
        headers['Content-Type'] = 'application/ld+json'
        headers['Link'] = link

        if fiware_service:
            headers['fiware-service'] = fiware_service

        r = session.get(url + '/ngsi-ld/v1/entities', headers=headers, params=params, timeout=default_timeout)

        return return_response(r)

    except Exception as e:
        return [-1, str(e)]


def get_temporal_stellio(session, url, id, link, properties, start_date, end_date, fiware_service=None):
    try:
        headers = {}
        headers['Link'] = link

        attributes = ''

        for request_property in properties:

            attributes += request_property

            if request_property is not properties[len(properties) - 1]:
                attributes += ','

        params = {}
        params['timerel'] = 'between'
        params['time'] = start_date
        params['endTime'] = end_date
        params['attrs'] = attributes
        params['options'] = 'temporalValues'

        r = session.get(url + '/ngsi-ld/v1/temporal/entities/' + id, params=params, headers=headers, timeout=default_timeout)

        return return_response(r)
    except Exception as e:
        return [-1, str(e)]