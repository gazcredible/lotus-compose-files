import datetime
import os

import unexefiware.time
from flask import request
from flask_cors import CORS, cross_origin
from flask import Blueprint, render_template, abort, send_file

import inspect
import requests
import unexeaqua3s.json
import requests_oauthlib
from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import LegacyApplicationClient

import blueprints.debug
import blueprints.globals

blueprint = Blueprint('keyrock_blueprint', __name__, template_folder='templates')

url = 'https://platform.aqua3s.eu/keyrock/'

@blueprint.route('/nokeyrock')
def default_page_no_keyrock():
    blueprints.debug.debugControl.disableKeyrock = True
    return build_debug_page(enable_keyrock = False)

@blueprint.route('/keyrock')
def default_page_keyrock():
    blueprints.debug.debugControl.disableKeyrock = False
    return default_page()

@blueprint.route('/')
def default_page():
    return build_debug_page(enable_keyrock = (blueprints.debug.debugControl.disableKeyrock == False) )

def build_debug_page(enable_keyrock = True):
    client_id = r'310fd9ba-6151-4689-bc18-aa135eaacdfa'
    client_secret = r'9c07fb25-ef04-4368-b1ea-89f2bc56e4ad'

    user_data = {}

    if 'AAA' in blueprints.globals.fiware_service_list:
        if 'KEYROCK_ADMIN_NAME' not in os.environ or 'KEYROCK_ADMIN_PASS' not in os.environ:
            user_data['AAA'] = {'token': 'AAA'}
        else:
            user_data['aawa_user1'] = {'username': 'user1@aawa.com', 'password': 'kPxN3tbqURjctvrk', 'token': 'AAA'}
            user_data['lha2_user1'] = {'username': 'user1@lha2.com', 'password': 'YzJrF53sCaDbAL4a', 'token': 'AAA'}
            user_data['aaa_main_user1'] = {'username': 'mainuser1@aaa.com', 'password': 'TEfja4FjT7N3khTk', 'token': 'AAA'}
            user_data['aaa_rest_files_user1'] = {'username': 'restricted1@aaa.com', 'password': 'Bt5xLtJ4zF7xdHmy', 'token': 'AAA'}
            user_data['aaa_rest_alerts_user1'] = {'username': 'restricted2@aaa.com', 'password': 'SJNa4yV2YSvF4pxB', 'token': 'AAA'}

    if 'EYA' in blueprints.globals.fiware_service_list:
        user_data['eyath_main_user1'] = {'username': 'mainuser1@eyath.gr', 'password': 'XxzR88R3FnuHsyhx', 'token':'EYA'}
        user_data['eyath_external_user1'] = {'username': 'external1@eyath.gr', 'password': 'XJp4S6aszagXM8bf', 'token':'EYA'}
        user_data['rcm_user1'] = {'username': 'user1@rcm.gr', 'password': 'JkhyyFvs4Rwt8MZV', 'token':'EYA'}

    if 'SOF' in blueprints.globals.fiware_service_list:
        user_data['sofiyska_user_1'] = {'username': 'user1@sofiyska.com', 'password': 'm4LTxS5M3EeVzryu', 'token':'SOF'}

    if 'SVK' in blueprints.globals.fiware_service_list:
        user_data['svk_user1'] = {'username': 'user1@svk.com', 'password': 'BNDj9DytCpXA4ugq', 'token':'SVK'}

    if 'WBL' in blueprints.globals.fiware_service_list:
        user_data['wbl_user1'] = {'username': 'user1@wbl.com', 'password': 'RsWQpFg2wnTRNNDU', 'token':'WBL'}

    if 'VVQ' in blueprints.globals.fiware_service_list:
        user_data['vvq_main_user1'] = {'username': 'mainuser1@vvq.com', 'password': 'JZqz7w8t2V2n57JN', 'token':'VVQ'}



    if blueprints.debug.debugControl.allowUNEXEPilots == True:

        if 'GT' in blueprints.globals.fiware_service_list:
            user_data['GT'] = {'token':'GT'}

        if 'WIS' in blueprints.globals.fiware_service_list:
            user_data['WIS'] = {'token':'WIS'}

        if 'TTT' in blueprints.globals.fiware_service_list:
            user_data['TTT'] = {'token':'TTT'}

        if 'P2B' in blueprints.globals.fiware_service_list:
            user_data['P2B'] = {'token':'P2B'}

        if 'GUW' in blueprints.globals.fiware_service_list:
            user_data['GUW'] = {'token':'GUW'}

    data = {}
    data['links'] = []

    for current_pilot in user_data:
        try:
            links = {}
            links['map'] = 'Map'
            links['analytics'] = 'Charts'
            links['alerts'] = 'Devices'
            #links['imm']

            for link in links:
                link_record ={}

                link_record['print_name'] = current_pilot + '_' + links[link]
                link_record['link'] = link

                if ('username' in user_data[current_pilot]) and enable_keyrock:
                    username = user_data[current_pilot]['username']
                    password = user_data[current_pilot]['password']

                    oauth = OAuth2Session(client=LegacyApplicationClient(client_id=client_id))
                    token = oauth.fetch_token(token_url=url + '/oauth2/token', username=username, password=password, client_id=client_id, client_secret=client_secret, verify=False,time=2)

                    link_record['access_token'] = token['access_token']
                else:
                    link_record['access_token'] = user_data[current_pilot]['token']

                data['links'].append(link_record)

        except Exception as e:
            blueprints.debug.servicelog.exception(inspect.currentframe(), e )

    if False:
        current_pilot= 'FAIL'
        token = 0
        data['links'].append({'print_name': current_pilot + '_map', 'link': 'map', 'access_token': token})
        data['links'].append({'print_name': current_pilot + '_analytics', 'link': 'analytics', 'access_token': token})
        data['links'].append({'print_name': current_pilot + '_alerts', 'link': 'analytics', 'access_token': token})

        data['links'].append({'print_name': 'timeout', 'link': 'timeout', 'access_token': token})

        data['links'].append({'print_name': 'Control', 'link': 'control', 'access_token': token})
        data['links'].append({'print_name': 'Logging', 'link': 'logging', 'access_token': token})


    return render_template("keyrock_test.html", payload = data)

keyrock_userdata = {}

def ok(access_token):
    if blueprints.debug.debugControl.disableKeyrock == True:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'Keyrock disabled' + ' ' + str(access_token))

        if access_token == None:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'Keyrock-denied no token' + ' ' + str(access_token))
            return False
        return True

    #gareth - my back door
    if access_token == 'GT':
        return True

    if access_token == 'WIS':
        return True

    try:
        if 'KEYROCK_ADMIN_NAME' not in os.environ or 'KEYROCK_ADMIN_PASS' not in os.environ:
            blueprints.debug.servicelog.fail(inspect.currentframe(), 'Keyrock: Details not present')
            return False

        if access_token in keyrock_userdata:
            #is it valid?
            if 'token_data' in keyrock_userdata[access_token] and 'token' in keyrock_userdata[access_token]['token_data']:
                if 'expires_at' in keyrock_userdata[access_token]['token_data']['token']:
                    keyrock_timestamp = unexefiware.time.fiware_to_datetime(keyrock_userdata[access_token]['token_data']['token']['expires_at'])

                    if keyrock_timestamp < datetime.datetime.utcnow():
                        del keyrock_userdata[access_token]
    except Exception as e:
        #oops, bad things happened - remove to force a re-validation
        if access_token in keyrock_userdata:
            del keyrock_userdata[access_token]
    try:
        if access_token not in keyrock_userdata:
            keyrock_userdata[access_token] = {'access_token':access_token, 'user_data' : None, 'token_data': None, 'user_data_record' : None, 'user_role_data' : None}

            data = {}
            data['access_token'] = access_token
            r = requests.get(os.environ['KEYROCK_URL'] + '/user', params=data, verify=False)

            if r.ok:
                keyrock_userdata[access_token]['user_data'] = unexeaqua3s.json.loads(r.text)

                admin_tokendata = requests.post(os.environ['KEYROCK_URL'] + '/v1/auth/tokens', json={'name': os.environ['KEYROCK_ADMIN_NAME'], 'password': os.environ['KEYROCK_ADMIN_PASS']}, verify=False)

                if admin_tokendata.ok:
                    keyrock_userdata[access_token]['token_data'] = unexeaqua3s.json.loads(admin_tokendata.text)

                    data = {}
                    data['access_token'] = access_token
                    r = requests.get(os.environ['KEYROCK_URL'] + '/user', params=data, verify=False)

                    if r.ok:
                        keyrock_userdata[access_token]['user_data_record'] = unexeaqua3s.json.loads(r.text)

                        if 'organizations' in keyrock_userdata[access_token]['user_data_record'] and len(keyrock_userdata[access_token]['user_data_record']['organizations']) > 0:
                            r = requests.get(url + 'v1/applications/' + keyrock_userdata[access_token]['user_data_record']['app_id'] + '/roles/' + keyrock_userdata[access_token]['user_data_record']['organizations'][0]['roles'][0]['id'] + '/permissions', headers={'X-Auth-token': admin_tokendata.headers['x-subject-token']})

                            if r.ok:
                                keyrock_userdata[access_token]['user_role_data'] = unexeaqua3s.json.loads(r.text)
                            else:
                                blueprints.debug.servicelog.log(inspect.currentframe(), 'user_role_data FAIL')

                    else:
                        blueprints.debug.servicelog.log(inspect.currentframe(), 'user_data_record FAIL')
                else:
                    blueprints.debug.servicelog.log(inspect.currentframe(), 'admin_token FAIL')
        else:
            pass
            #blueprints.debug.servicelog.log(inspect.currentframe(), 'keyrock.ok() - cache entry')

        if access_token in keyrock_userdata and 'user_data' in keyrock_userdata[access_token] and keyrock_userdata[access_token]['user_data'] is not None and len(keyrock_userdata[access_token]['user_data']['organizations']) > 0:
            return True

    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )

    blueprints.debug.servicelog.log(inspect.currentframe(), 'Keyrock denied! - ' + str(access_token))
    return False


def _get_location_from_keyrock(access_token):
    try:
        if ok(access_token) and access_token in keyrock_userdata:
            if len(keyrock_userdata[access_token]['user_data']['organizations']) > 0:
                return keyrock_userdata[access_token]['user_data']['organizations'][0]['description']

            raise Exception('Invalid Org Data')
        else:
            return 'Invalid'

        data = {}
        data['access_token'] = access_token

        r = requests.get(url + '/user', params=data, verify=False)

        if r.ok:
            stuff = unexeaqua3s.json.loads(r.text)
            if len(stuff['organizations']) > 0:
                return stuff['organizations'][0]['description']

            raise Exception('Invalid Org Data')
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )

    return 'Invalid'


def get_location(access_token):

    if blueprints.debug.debugControl.disableKeyrock == True:
        if access_token in blueprints.globals.fiware_service_list:
            return access_token

    if blueprints.debug.debugControl.allowUNEXEPilots == True:
        if access_token == 'GT' and 'GT' in blueprints.globals.fiware_service_list:
            return access_token

        if access_token == 'WIS' and 'WIS' in blueprints.globals.fiware_service_list:
            return access_token

        if access_token == 'TTT' and 'TTT' in blueprints.globals.fiware_service_list:
            return access_token

    location = _get_location_from_keyrock(access_token)

    if location == 'Trieste' and 'AAA' in blueprints.globals.fiware_service_list:
        return 'AAA'

    if location == 'Thessaloniki' and 'EYA' in blueprints.globals.fiware_service_list:
        return 'EYA'

    if location == 'Sofia' and 'SOF' in blueprints.globals.fiware_service_list:
        return 'SOF'

    if location == 'Botevgrad' and 'SVK' in blueprints.globals.fiware_service_list:
        return 'SVK'

    if location == 'Lemesos' and 'WBL' in blueprints.globals.fiware_service_list:
        return 'WBL'

    if location == 'Brussels' and 'VVQ' in blueprints.globals.fiware_service_list:
        return 'VVQ'


    blueprints.debug.servicelog.log(inspect.currentframe(), 'Keyrock-unknown role/location' + ' ' + str(access_token))

    raise Exception('Keyrock-unknown role/location')

def _get_has_role(access_token, label):

    try:
        if ok(access_token):
            for entry in keyrock_userdata[access_token]['user_role_data']['role_permission_assignments']:
                if entry['id'] == label:

                    if label == '81a98ebf-767e-451e-b70e-0a43a16efac8' and keyrock_userdata[access_token]['user_data_record']['organizations'][0]['name'] == 'RCM User':
                        return False

                    return True
            return False

        raise Exception('Keyrock-unknown role/location:' + access_token + ' ' + str(label))
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(),e)

    return False

    try:
        if 'KEYROCK_ADMIN_NAME' in os.environ and 'KEYROCK_ADMIN_PASS' in os.environ:
            admin_tokendata = requests.post(url + '/v1/auth/tokens', json={'name': os.environ['KEYROCK_ADMIN_NAME'], 'password': os.environ['KEYROCK_ADMIN_PASS']}, verify=False)

            if admin_tokendata.ok:
                data = {}
                data['access_token'] = access_token

                print(url+'/user-har_role')
                r = requests.get(url + '/user', params=data, verify=False)

                if r.ok:
                    user_data_record = unexeaqua3s.json.loads(r.text)

                    if 'organizations' in user_data_record and len(user_data_record['organizations']) > 0:
                        print(url + 'v1/applications/' + user_data_record['app_id'] + '/roles/' + user_data_record['organizations'][0]['roles'][0]['id'] + '/permissions')
                        r = requests.get(url + 'v1/applications/' + user_data_record['app_id'] + '/roles/' + user_data_record['organizations'][0]['roles'][0]['id'] + '/permissions', headers={'X-Auth-token': admin_tokendata.headers['x-subject-token']})

                        if r.ok:
                            user_role_data = unexeaqua3s.json.loads(r.text)
                            for entry in user_role_data['role_permission_assignments']:
                                if entry['id'] == label:

                                    if label == '81a98ebf-767e-451e-b70e-0a43a16efac8' and user_data_record['organizations'][0]['name'] == 'RCM User':
                                        return  False

                                    return True
    except Exception as e:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'Keyrock-unknown role/location' + ' ' + str(access_token))


    return False

def get_is_userlayer_available(access_token):
    if blueprints.debug.debugControl.disableKeyrock == True:
        return True

    if get_location(access_token) == 'AAA':
        # ad7ff0f5-4e0f-484d-b614-d92fad9e6392 Flood risk and hazard maps
        return _get_has_role(access_token, 'ad7ff0f5-4e0f-484d-b614-d92fad9e6392')

    if get_location(access_token) == 'EYA':
        return _get_has_role(access_token, 'a7ff6ab0-afcc-4140-bfae-a9c323afc0a9')

    return True


def get_is_epanet_available(access_token):
    if blueprints.debug.debugControl.disableKeyrock == True:

        if access_token == 'AAA':
            return True

        if access_token == 'GUW':
            return True


        return False

    # 84671c33-3bc2-4b0c-a0f8-7086292f9d25 Hydraulic model on a map
    return _get_has_role(access_token, '84671c33-3bc2-4b0c-a0f8-7086292f9d25')


def get_is_mapview_alerts_available(access_token):
    if blueprints.debug.debugControl.disableKeyrock == True:
        return True

    # 8e25d7b1-0143-4e73-b3be-51d3712130e1 Abnormal functioning of the sensors on map
    return _get_has_role(access_token,'8e25d7b1-0143-4e73-b3be-51d3712130e1')


def get_is_mapview_available(access_token):
    if blueprints.debug.debugControl.disableKeyrock == True:
        return True

    #81a98ebf-767e-451e-b70e-0a43a16efac8 Show maps component
    return _get_has_role(access_token, '81a98ebf-767e-451e-b70e-0a43a16efac8')


def get_is_analtyics_available(access_token):
    if blueprints.debug.debugControl.disableKeyrock == True:
        return True

    #f8ffb8e9-ed08-4942-8698-0a324fc49763 Show analytics component
    return _get_has_role(access_token, 'f8ffb8e9-ed08-4942-8698-0a324fc49763')

pilot_functionality_lookup ={}

pilot_functionality_lookup['AAA'] = {'epanomalies': 'true', 'devices': 'true', 'satellite': 'true', 'social_media': 'true', 'cctv': 'false', 'drones': 'true'}
pilot_functionality_lookup['EYA'] = {'epanomalies': 'false', 'devices': 'true', 'satellite': 'true', 'social_media': 'false', 'cctv': 'true', 'drones': 'true'}
pilot_functionality_lookup['WBL'] = {'epanomalies': 'false', 'devices': 'true', 'satellite': 'true', 'social_media': 'true', 'cctv': 'false', 'drones': 'false'}
pilot_functionality_lookup['SOF'] = {'epanomalies': 'false', 'devices': 'true', 'satellite': 'true', 'social_media': 'true', 'cctv': 'false', 'drones': 'false'}
pilot_functionality_lookup['SVK'] = {'epanomalies': 'false', 'devices': 'true', 'satellite': 'true', 'social_media': 'false', 'cctv': 'false', 'drones': 'true'}
pilot_functionality_lookup['VVQ'] = {'epanomalies': 'false', 'devices': 'true', 'satellite': 'false', 'social_media': 'true', 'cctv': 'false', 'drones': 'false'}
pilot_functionality_lookup['BDI'] = {'epanomalies': 'false', 'devices': 'true', 'satellite': 'false', 'social_media': 'true', 'cctv': 'false', 'drones': 'false'}

pilot_functionality_lookup['GUW'] = {'epanomalies': 'true', 'devices': 'true'}


def get_alert_info(access_token):

    try:
        loc = get_location(access_token)
        return pilot_functionality_lookup[loc]
    except Exception as e:
        pass

    return {}