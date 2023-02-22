import unexefiware.fiwarewrapper
import unexefiware.base_logger
import datetime
import time

import threading
import requests
import inspect
import unexefiware.ngsildv1

import blueprints.globals
import blueprints.logger



class physicalWrapper(unexefiware.fiwarewrapper.fiwareWrapper):
    def __init__(self):
        super().__init__()
        self.is_available = True
        self.url = blueprints.globals.fiware_resources_url

        #giorgos server(s)
        self.url = 'http://147.102.5.27:1026'
        self.historic_url ='http://147.102.5.27:1337'


        self.url = 'https://platform.aqua3s.eu/orion/'
        self.historic_url ='http://52.50.143.202:1337'


        #my server
        #self.url = 'http://46.101.61.143:8200/'
        #self.historic_url ='http://46.101.61.143:8200/'

        # my test server
        self.url = 'http://localhost:9200/'
        self.historic_url ='http://localhost:9200/'

        self.name = 'Broker: ' + str(self.historic_url)




