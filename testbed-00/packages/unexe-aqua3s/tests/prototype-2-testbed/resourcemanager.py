import unexeaqua3s.fiwareresources
import threading
import os

class ResouceManager(unexeaqua3s.fiwareresources.FiwareResources):
    def __init__(self,options = None):

        if options == None:
            webdav_options = {
                'webdav_hostname': os.environ['WEBDAV_URL'],
                'webdav_login': os.environ['WEBDAV_NAME'],
                'webdav_password': os.environ['WEBDAV_PASS']
            }

            super().__init__(options = webdav_options)
        else:
            super().__init__(options)
        self.has_loaded_content = False


    def launch(self, fiware_service_list=None):
        self.thread = threading.Thread(target = self._loadingthread, args=fiware_service_list)
        self.thread.start()

    def _loadingthread(self, fiware_service_list):

        self.init(url=os.environ['USERLAYER_BROKER'], file_root=os.environ['FILE_PATH'] + os.sep + os.environ['FILE_VISUALISER_FOLDER'] , fiware_service_list=fiware_service_list)
        self.has_loaded_content = True

    def log(self, cf, msg):
        if self.logger:
            self.logger.add(cf,msg)

    def isAvailable(self):
        return self.has_loaded_content


fiware_resources = None

def init(file_root, logger = None):
    global fiware_resources
    fiware_resources = ResouceManager()
    fiware_resources.logger = logger
    fiware_resources.launch()

