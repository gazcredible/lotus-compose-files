import requests
import inspect
import unexefiware.ngsildv1
import unexefiware.base_logger
import json


class fiwareWrapper:
    def __init__(self, url=None, historic_url=None):
        self.is_available = True

        self.url = url
        self.link = 'https://schema.lab.fiware.org/ld/context'
        self.logger = None
        # gareth -   this is for aqua3s
        self.historic_url = self.url

        if historic_url != None:
            self.historic_url = historic_url

        self.link = '<https://smartdatamodels.org/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
        self.name = str(self.url) + ' fiware Broker'

    def init(self, logger=None):
        if logger:
            self.logger = logger

    def subscriptions_enable(self):
        headers = {}
        headers['Content-Type'] = 'application/ld+json'

        session = requests.session()

        path = self.url + '/ngsi-ld/v1/enable_subscriptions'

        try:
            r = session.post(path, data=json.dumps([]), headers=headers, timeout=10)
            return unexefiware.ngsildv1.return_response(r)

        except Exception as e:
            return [-1, str(e)]

    def erase_broker(self):

        headers = {}
        headers['Content-Type'] = 'application/ld+json'

        session = requests.session()

        path = self.url + '/ngsi-ld/v1/erase_broker'

        try:
            r = session.post(path, data=json.dumps([]), headers=headers, timeout=10)
            return unexefiware.ngsildv1.return_response(r)

        except Exception as e:
            return [-1, str(e)]

    def create_instance(self, entity_json, service, link=None):
        try:
            session = requests.session()
            result = unexefiware.ngsildv1.create_instance(session, self.url, json.dumps(entity_json), fiware_service=service)

            if result[0] != 201:
                if self.logger:
                    self.logger.fail(inspect.currentframe(), str(result[1]))

            return result

        except Exception as e:
            if self.logger:
                self.logger.fail(inspect.currentframe(), str(e))

            return [-1, str(e)]

        return [-1, '']

    def delete_instance(self, entity_id, service, link=None):
        try:
            session = requests.session()
            result = unexefiware.ngsildv1.delete_instance(session, self.url, entity_id, link=link if link else self.link, fiware_service=service)

            if result[0] != 200:
                if self.logger:
                    self.logger.fail(inspect.currentframe(), str(result[1]))

            return result

        except Exception as e:
            if self.logger:
                self.logger.fail(inspect.currentframe(), str(e))

            return [-1, str(e)]

        return [-1, '']

    def get_entity(self, entity_id, service, link=None):
        try:
            session = requests.session()
            result = unexefiware.ngsildv1.get_instance(session, self.url, entity_id, link=link if link else self.link, fiware_service=service)

            if result[0] == 200:
                return result[1]
            else:
                if self.logger:
                    self.logger.fail(inspect.currentframe(), str(result[1]))
        except Exception as e:
            if self.logger:
                self.logger.fail(inspect.currentframe(), str(e))

            return [-1, str(e)]

        return []

    def get_instance(self, entity_id, service, link=None):
        try:
            session = requests.session()
            result = unexefiware.ngsildv1.get_instance(session, self.url, entity_id, link=link if link else self.link, fiware_service=service)

            if result[0] != 200:
                if self.logger:
                    self.logger.fail(inspect.currentframe(), str(result[1]))

            return result

        except Exception as e:
            if self.logger:
                self.logger.fail(inspect.currentframe(), str(e))

            return [-1, str(e)]

        return []

    def patch_entity(self, entity_id, json_data, service, link=None):
        try:
            session = requests.session()

            result = unexefiware.ngsildv1.patch_instance_orion(session, self.url, entity_id, json.dumps(json_data), link=link if link else self.link, fiware_service=service)

            if result[0] != 204:
                if self.logger:
                    self.logger.fail(inspect.currentframe(), str(result[1]))

            return result


        except Exception as e:
            if self.logger:
                self.logger.fail(inspect.currentframe(), str(e))

            return [-1, str(e)]

        return [-1, '']

    def get_entities(self, entity_type, service, link=None):
        try:
            session = requests.session()
            result = unexefiware.ngsildv1.get_type(session, self.url, entity_type, link=link if link else self.link, fiware_service=service)

            if result[0] == 200:
                return result
            else:
                if self.logger:
                    self.logger.fail(inspect.currentframe(), str(result[1]))
        except Exception as e:
            if self.logger:
                self.logger.fail(inspect.currentframe(), str(e))

            return [-1, str(e)]

        return [-1, '']

    def get_temporal_orion(self, service, entity_id, fiware_start_time, fiware_end_time, link=None):
        try:
            session = requests.session()
            result = unexefiware.ngsildv1.get_temporal_orion(session,
                                                             self.historic_url,
                                                             entity_id,
                                                             link=link if link else self.link,
                                                             start_date=fiware_start_time,
                                                             end_date=fiware_end_time,
                                                             fiware_service=service)
            if result[0] == 200:
                return result[1]
            else:
                if self.logger:
                    self.logger.fail(inspect.currentframe(), str(result[1]))

                return result
        except Exception as e:
            if self.logger:
                self.logger.fail(inspect.currentframe(), str(e))

            return [-1, str(e)]

        return [-1, '']

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

    def isAvailable(self):
        return self.is_available

    def get_name(self):
        return self.name