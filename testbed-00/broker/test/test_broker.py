import os
os.environ['FILE_PATH'] = 'test/'

import unexefiware.base_logger
import unexebroker.broker_flask

unexebroker.broker_flask.init(stellio_style=True, drop_all_tables=False, logger=unexefiware.base_logger.BaseLogger() )

def test_version_command():
    result = unexebroker.broker_globals.contextbroker.get_broker_data()

    assert len(result) == 2
    assert(result[0] == 200)
