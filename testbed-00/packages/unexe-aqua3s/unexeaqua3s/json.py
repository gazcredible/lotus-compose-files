import json
import inspect

import unexefiware.base_logger

def loads(s):
    try:
        return json.loads(s)
    except Exception as e:
        pass

    try:
        s = s.replace('\\', '')
        return json.loads(s)

    except Exception as e:
        logger = unexefiware.base_logger.BaseLogger()
        logger.exception(inspect.currentframe(), e)

    return ''

def load(s):
    return json.load(s)

def dumps(s,indent=None):
    return json.dumps(s,indent=indent)
