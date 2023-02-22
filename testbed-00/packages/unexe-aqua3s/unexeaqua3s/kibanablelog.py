import inspect
import traceback

import datetime

import unexefiware.base_logger
import unexefiware.time
import os.path
import os
import requests
import unexeaqua3s.json

class KibanableLog(unexefiware.base_logger.BaseLogger):
    def __init__(self,component):
        super().__init__()
        self.component = component

    def fail(self, cf, text):
        self.log(cf, 'FAIL:'+str(text), level = 'ERROR')

    def log(self, cf, msg, level = 'INFO'):
        head, tail = os.path.split(cf.f_code.co_filename)

        op = tail + ' ' + cf.f_code.co_name +'(' +str(cf.f_lineno) + ')'
        timestamp = unexefiware.time.datetime_to_fiware(datetime.datetime.utcnow())

        if 'REMOTE_LOGGING_ENABLED' in os.environ and os.environ['REMOTE_LOGGING_ENABLED'].lower() == 'true':
            params = {'time': timestamp,
                      'lvl': level,
                      'comp': self.component,
                      'op': op,
                      'msg': msg
                      }

            if 'REMOTE_LOGGING_URL' in os.environ:
                try:
                    r = requests.post(os.environ['REMOTE_LOGGING_URL'], data=unexeaqua3s.json.dumps(params))
                    if r.ok == False:
                        self.log_to_stdout('Failed to remote log: ' + timestamp + ' ' + self.component + ' ' + level + ' ' + op + ' ' + msg)

                except Exception as e:
                    self.log_to_stdout('Failed to remote log: ' + timestamp + ' ' + self.component + ' ' + level + ' ' + op + ' ' + msg)
                    return

        self.log_to_stdout(timestamp + ' ' + level + ' ' + op + ' ' + msg)

    def log_to_stdout(self, text):
        print(str(text))
