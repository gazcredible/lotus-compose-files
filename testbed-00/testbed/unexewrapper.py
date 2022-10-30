import inspect

import unexefiware.fiwarewrapper
import unexefiware.ngsildv1
import requests
import json
import inspect
import unexefiware.base_logger

class unexewrapper(unexefiware.fiwarewrapper.fiwareWrapper):
    def __init__(self, url=None):
        super().__init__(url)

        self.logger = unexefiware.base_logger.BaseLogger()

    def version(self):
        headers = {}
        headers['Content-Type'] = 'application/ld+json'

        session = requests.session()

        path = self.url + '/unexe-broker/v1/version'

        try:
            r = session.get(path, data=json.dumps([]), headers=headers, timeout=10)
            return unexefiware.ngsildv1.return_response(r)

        except Exception as e:
            return [-1, str(e)]

    def is_model_temporal(self, service: str, model: str) -> dict:
        instance = self.get_entity(model, service)

        results = {'temporal': False, 'attribs': []}

        for key in instance:
            if isinstance(instance[key], dict):
                if 'observedAt' in instance[key]:
                    results['attribs'].append(key)
                    results['temporal'] = True

        return results

    def delete_type(self, fiware_service:str, types:list):
        try:
            session = requests.session()

            if not isinstance(types, list):
                types = [types]

            for label in types:
                result = unexefiware.ngsildv1.get_type(session, self.url, label, link=self.link, fiware_service=fiware_service)

                if result[0] == 200:
                    for entity in result[1]:
                        unexefiware.ngsildv1.delete_instance(session, self.url, entity['id'], self.link, fiware_service=fiware_service)
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)


    def get_all_type(self, fiware_service:str, entity_type:str):
        try:
            session = requests.session()
            return unexefiware.ngsildv1.get_all_orion(session, self.url, entity_type, link=self.link, fiware_service=fiware_service)

        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

    def get_temporal(self, fiware_service:str, entity_id:str, properties:list, start_date:str, end_date:str):
        session = requests.session()
        try:
            headers = {}
            headers['Link'] = self.link
            headers['fiware_service'] = fiware_service

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
            #params['options'] = 'temporalValues'

            r = session.get(self.url + '/ngsi-ld/v1/temporal/entities/' + entity_id, params=params, headers=headers, timeout=unexefiware.ngsildv1.default_timeout)

            return unexefiware.ngsildv1.return_response(r)
        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)
            return [-1, str(e)]