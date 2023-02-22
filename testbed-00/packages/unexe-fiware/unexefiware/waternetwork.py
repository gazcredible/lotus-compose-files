import json
import unexefiware.ngsildv1
import unexefiware.workertask
import epanet_fiware.waternetwork

class DeleteRequest(unexefiware.workertask.WorkerTask):
    def __init__(self):
        unexefiware.workertask.WorkerTask.__init__(self)
        self.worklist = []

    def add(self, url, id, link, fiware_service):
        self.worklist.append({'url':url, 'id':id, 'link': link, 'fiware-service': fiware_service })

    def start(self):
        for entity in self.worklist:
            self.doWork(self.threadtask, entity)

    def threadtask(self, args):
        try:
            if unexefiware.ngsildv1.delete_instance(args['url'], args['id'], args['link'], args['fiware-service']) == False:
                print('DeleteRequest: not ok' + args['id'])

        except Exception as e:
            print(str(e))

        self.finish_task()


class CreateRequest(unexefiware.workertask.WorkerTask):
    def __init__(self):
        unexefiware.workertask.WorkerTask.__init__(self)
        self.worklist = []

    def add(self, url, data, fiware_service):
        self.worklist.append({'url':url, 'data':data, 'fiware-service': fiware_service })

    def start(self):
        for entity in self.worklist:
            self.doWork(self.threadtask, entity)

    def threadtask(self, args):
        try:
            if unexefiware.ngsildv1.create_instance(args['url'], args['data'], args['fiware-service']) == False:
                data = json.loads(args['data'])
                print('CreateRequest - not ok ' + data['id'])

        except Exception as e:
            print(str(e))

        self.finish_task()


def create_instance(url, inst, fiware_service):

    fiware_waternetwork = inst.fiware_waternetwork['WaterNetwork']

    # delete all the old stuff that's in the broker
    existing_instance = unexefiware.ngsildv1.get_instance(url, fiware_waternetwork['id'], fiware_waternetwork['@context'], fiware_service)
    
    if existing_instance != []:
        delete_instance_from_model(url, existing_instance,fiware_service)

    # add shiny new stuff
    create_water_components_task = CreateRequest()
    create_water_components_task.add(url, json.dumps(fiware_waternetwork),fiware_service)

    for component in fiware_waternetwork['components']['value']:
        for entity in inst.fiware_component[component]:
            create_water_components_task.add(url, json.dumps(entity), fiware_service)

    create_water_components_task.start()
    create_water_components_task.wait_to_finish()

    return

def delete_instance_from_model(url, existing_instance, fiware_service):

    delete_water_components_task = DeleteRequest()

    delete_water_components_task.add(url, existing_instance['id'], existing_instance['@context'], fiware_service)

    for component in existing_instance['components']['value']:
        print(component +' ' + str(len(existing_instance[component]['value'])))

        if isinstance(existing_instance[component]['value'], list) == True:
            for entity in existing_instance[component]['value']:
                delete_water_components_task.add(url, entity, epanet_fiware.waternetwork.link_lookup[component], fiware_service)
        else:
            entity = existing_instance[component]['value']
            delete_water_components_task.add(url, entity, epanet_fiware.waternetwork.link_lookup[component], fiware_service)


    delete_water_components_task.start()
    delete_water_components_task.wait_to_finish()