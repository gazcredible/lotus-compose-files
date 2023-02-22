import requests
# import json
from requests.exceptions import HTTPError
from typing import Union


MAX_RETRIES = 20


def get_access_token(
        client_id: str, client_secret: str, auth_url: str) -> str:
    if not client_id or not client_secret or not auth_url:
        return None
    data_post = {'grant_type': 'client_credentials'}
    try:
        response = requests.post(
            auth_url,
            auth=(client_id, client_secret),
            data=data_post
            )
        response.raise_for_status()
    except HTTPError as http_err:
        raise RuntimeError('HTTP error occurred: {}'.format(http_err))
    except Exception as err:
        raise RuntimeError('Other error occurred: {}'.format(err))
    return response.json()['access_token']


def _initialise_session(
        access_token: Union[str, None],
        network_name: Union[str, None],
        header_link: Union[str, None]
        ) -> requests.sessions.Session:
    headers = {
        'Content-Type': 'application/ld+json',
        'Accept': 'application/ld+json'
        }
    if header_link:
        headers.update({'Link': header_link})
    if network_name:
        headers.update({'NGSILD-Tenant': network_name})
    if access_token:
        headers['Authorization'] = 'Bearer {}'.format(access_token)
    session = requests.Session()
    session.headers.update(headers)
    adapter = requests.adapters.HTTPAdapter(max_retries=MAX_RETRIES)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


def create_entities(access_token: Union[str, None],
                    data: list, gateway_server: str, network_name: str = None,
                    header_link: str = None):
    session = _initialise_session(access_token, network_name, header_link)
    for entity_data in data:
        create_entity(session, entity_data, gateway_server)


def create_entity(session: requests.sessions.Session,
                  entity_data: dict,
                  gateway_server: str):
    # print('\nCreating entity {}'.format(entity_data['id']))
    # print('using {}\n'.format(json.dumps(entity_data)))
    url = '{}/ngsi-ld/v1/entities'.format(gateway_server)
    try:
        response = session.post(url, json=entity_data)
        response.raise_for_status()
    except HTTPError as http_err:
        raise RuntimeError('HTTP error occurred: {}'.format(http_err))
    except Exception as err:
        raise RuntimeError('Other error occurred: {}'.format(err))
    # print('Entity {} created'.format(entity_data['id']))
    # print('using ', json.dumps(entity_data))
    return


def delete_entity(session: requests.sessions.Session, entity_id: str,
                  gateway_server: str):
    url = '{}/ngsi-ld/v1/entities/{}/'.format(gateway_server, entity_id)
    try:
        session.delete(url)
    except HTTPError as http_err:
        raise RuntimeError('HTTP error occurred: {}'.format(http_err))
    except Exception as err:
        raise RuntimeError(
            'Other error occurred deleting {}: {}'.format(entity_id, err))
    # print('{} deleted'.format(entity_id))
    return


def delete_network(access_token: Union[str, None], gateway_server: str,
                   network_name: str = None,
                   header_link: str = None):
    print('Deleting previously stored network entities')
    for entity_type in ['Junction', 'Reservoir', 'Tank', 'Pipe', 'Pump',
                        'Valve', 'Pattern', 'Curve']:
        _delete_entities(
            access_token, entity_type, gateway_server, network_name,
            header_link)


def _delete_entities(access_token: Union[str, None], entity_type: str,
                     gateway_server: str, network_name: str = None,
                     header_link: str = None):
    entities = retrieve_entities(access_token, entity_type,
                                 gateway_server, network_name,
                                 header_link)
    session = _initialise_session(access_token, network_name, header_link)
    for entity in entities:
        entity_id = entity['id']
        delete_entity(session, entity_id, gateway_server)


def retrieve_entity(access_token: Union[str, None], entity_id: str,
                    gateway_server: str, network_name: str = None,
                    queries: dict = None, temporal: bool = False,
                    header_link: str = None) -> list:
    session = _initialise_session(access_token, network_name, header_link)
    if temporal:
        url = '{}/ngsi-ld/v1/temporal/entities/{}'.format(
            gateway_server, entity_id)
    else:
        url = '{}/ngsi-ld/v1/entities/{}'.format(gateway_server, entity_id)
    try:
        if queries:
            params_str = "&".join("%s=%s" % (k, v) for k, v in queries.items())
            response = session.get(
                url,
                params=params_str
            )
        else:
            response = session.get(url)
        response.raise_for_status()
    except HTTPError as http_err:
        raise RuntimeError('HTTP error occurred: {}'.format(http_err))
    except Exception as err:
        raise RuntimeError('Other error occurred: {}'.format(err))
    # print('{} retrieved'.format(entity_id))
    return response.json()


def retrieve_entities(access_token: Union[str, None],
                      entity_type: str, gateway_server: str,
                      network_name: str = None,
                      queries: dict = None, temporal: bool = False,
                      header_link: str = None) -> list:
    session = _initialise_session(access_token, network_name, header_link)
    if temporal:
        url = '{}/ngsi-ld/v1/temporal/entities'.format(gateway_server)
    else:
        url = '{}/ngsi-ld/v1/entities'.format(gateway_server)
    params = {
            'type': entity_type,
        }
    if queries:
        params.update(queries)
    try:
        response = session.get(
            url,
            params=params
        )
        response.raise_for_status()
    except HTTPError as http_err:
        raise RuntimeError('HTTP error occurred: {}'.format(http_err))
    except Exception as err:
        raise RuntimeError('Other error occurred: {}'.format(err))
    return response.json()
