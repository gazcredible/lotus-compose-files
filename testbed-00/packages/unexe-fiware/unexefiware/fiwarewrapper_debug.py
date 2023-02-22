import requests
import inspect
import unexefiware.ngsildv1
import unexefiware.base_logger
import json

import unexefiware.fiwarewrapper

class fiwareWrapperDebug(unexefiware.fiwarewrapper.fiwareWrapper):
    def __init__(self):
        super().__init__()

    def create_instance(self, entity_json, service, link=None):
        self.logger.log(inspect.currentframe(),'create_instance:' + service + ' ' + entity_json['id'])

    def patch_entity(self, entity_id, json_data, service, link=None):
        self.logger.log(inspect.currentframe(), 'patch_entity')