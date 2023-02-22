fiware_service_list = []

fiware_resources = None

def is_service_available():

    if fiware_resources != None:
        return fiware_resources.isAvailable()

    raise Exception('Calling fiware resources before initialised')