import os
import platform


if 'FILE_PATH' not in os.environ:
    print('No environ!')

    path = '/docker/lotus.local.bench.stellio/'

    if platform.system().lower() == 'windows':
        os.environ['FILE_PATH'] = 'c:' + path
    else:
        os.environ['FILE_PATH'] = path


from flask import Flask
from waitress import serve

import unexebroker.broker_flask
import unexebroker.unexe_broker
import  unexefiware.base_logger

app = Flask(__name__)
app.register_blueprint(unexebroker.broker_flask.blueprint)
app.register_blueprint(unexebroker.unexe_broker.blueprint)

unexebroker.broker_flask.init(stellio_style=True, drop_all_tables=False, logger=unexefiware.base_logger.BaseLogger() )

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8000, url_scheme='http')
