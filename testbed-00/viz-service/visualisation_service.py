import local_environment_settings
import os
import blueprints.debug
import blueprints.globals

import inspect

blueprints.debug.servicelog.log(inspect.currentframe(), 'PILOTS:' +os.environ['PILOTS'])
pilots = os.environ['PILOTS'].split(',')
for pilot in pilots:
    blueprints.globals.fiware_service_list.append(pilot.replace(' ',''))




import logging

from flask import Flask
from flask import request
from flask_cors import cross_origin
from flask import Blueprint, render_template,  send_file


from waitress import serve

import unexeaqua3s.json

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True

#from werkzeug.middleware.profiler import ProfilerMiddleware
#app.wsgi_app = ProfilerMiddleware(app.wsgi_app)

#import flask_monitoringdashboard as dashboard
#dashboard.bind(app)

#global settings of chaos
import blueprints.globals
import blueprints.mapview_blueprint
import blueprints.analytics_blueprint
import blueprints.keyrock_blueprint
import blueprints.resourcemanager


app.register_blueprint(blueprints.analytics_blueprint.blueprint)
app.register_blueprint(blueprints.mapview_blueprint.blueprint)
app.register_blueprint(blueprints.keyrock_blueprint.blueprint)

import blueprints.alerts_blueprint
app.register_blueprint(blueprints.alerts_blueprint.blueprint)

import blueprints.pilot_anomalies
app.register_blueprint(blueprints.pilot_anomalies.blueprint)

import blueprints.orion_device
app.register_blueprint(blueprints.orion_device.blueprint)

import blueprints.epanetanomalies_blueprint
app.register_blueprint(blueprints.epanetanomalies_blueprint.blueprint)


import blueprints.imm_blueprint
app.register_blueprint(blueprints.imm_blueprint.blueprint)

blueprints.debug.init() #start fiware
blueprints.orion_device.init()

blueprints.analytics_blueprint.init() #start charting
blueprints.resourcemanager.ResourceManager.one_time_init() #start resources

blueprints.imm_blueprint.one_time_init()

#-----------------------------------------------------------------------------------------------

@app.route('/userlayer')
def analytics_page():
    access_token = request.args.get('access_token')

    return render_template("userlayer.html", access_token=access_token)


@app.route('/timeout')
def timeout_test_page():
    access_token = 0

    return render_template("userlayer.html", access_token=access_token)

@app.route('/add_log', methods=['POST'])
@cross_origin()
def add_log():
    try:
        data = unexeaqua3s.json.loads(request.data)
        #brokerage.get().add_log_message(data['loc'],data['mode'], data['device'],data['property'],data['message'])
        return 'OK', 200
    except Exception as e:
        print('add_log()-'+str(e))
        return unexeaqua3s.json.dumps({"error": str(e)}), 500


blueprints.debug.servicelog.log(inspect.currentframe(), 'Server ready!')

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8100, url_scheme='https')
