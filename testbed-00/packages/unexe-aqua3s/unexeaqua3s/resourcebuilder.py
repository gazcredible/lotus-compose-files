import unexeaqua3s.webdav
import unexeaqua3s.geojson2aqua3s
import unexefiware.ngsildv1
import unexefiware.time
import unexefiware.model
import os
import pathlib
import zipfile
import kml2geojson
import pyproj
import geopandas
import unexeaqua3s.json
import inspect
import shutil
import requests
import datetime

import epanet_fiware.waternetwork
import epanet.toolkit as en

class ResourceBuilder(unexeaqua3s.webdav.webdav):
    def __init__(self, options = None):
        super().__init__(options)
        self.convert_files = True
        self.fiware_service_list = []
        self.remote_root = 'kr_10/data/'

    def init(self, path_root=None, clone_remote=True, delete_local=False, pilot_list=None):
        print('Clone Remote')

        if pilot_list == None:
            self.fiware_service_list = ['WBL', 'SVK', 'SOF', 'EYA', 'AAA', 'GT', 'WIS']
        else:
            self.fiware_service_list = pilot_list

        if path_root == None:
            raise Exception('No path root')

        self.local_root = path_root + '/data/'

        if delete_local == True:
            self.delete_local_dir(self.local_root)

        if clone_remote == True:
            for fiware_service in self.fiware_service_list:
                self.clone_pilot(fiware_service)

    def clone_pilot(self, fiware_service):
        remote_pilot_root = self.remote_root + '/' + fiware_service + '/'
        # remote_pilot_root = os.path.normpath(remote_pilot_root)

        local_pilot_root = self.local_root + os.sep + fiware_service + os.sep
        # local_pilot_root = os.path.normpath(local_pilot_root)
        self.clone_remote(remote_pilot_root, local_pilot_root)

    def writeback_to_server(self):
        self.logger.log(inspect.currentframe(), 'Disabled' )
        return

        self.upload_to_remote(self.remote_root, self.local_root)

    def convert_kml_to_userlayer(self, source_filepath, dest_path):
        stuff = pathlib.Path(source_filepath)
        resource = stuff.stem.lower()
        parent = str(stuff.parent)

        client_file = dest_path + resource + '_client.zip'
        server_file = dest_path + resource + '_server.json'

        try:
            if self.convert_files == True:
                kmz = zipfile.ZipFile(source_filepath, 'r')
                for d in kmz.filelist:
                    if '.kml' in d.filename:
                        try:
                            kml = kmz.open(d.filename, 'r').read()

                            f = open(parent + os.sep + d.filename, 'wb')
                            f.write(kml)
                            f.close()

                            self.create_local_dir(parent + os.sep + resource)

                            result = kml2geounexeaqua3s.json.convert(parent + os.sep + d.filename)

                            stuff = pathlib.Path(d.filename)

                            result_file = parent + os.sep + resource+ os.sep + stuff.stem + '.geojson'

                            f = open(result_file, 'w')
                            unexeaqua3s.json.dump(result[0],f)
                            f.close()

                            unexeaqua3s.geojson2aqua3s.convert_file(result_file, resource, client_file, server_file, '#ff0000')
                        except Exception as e:
                            print('convert_kml_to_userlayer()-' + str(e))
                            return []

                        #self.delete_local_dir(parent + os.sep + 'resource')
            return ['UserLayer', resource, [client_file, server_file]]
        except Exception as e:
            return []

    def convert_shapefile_to_userlayer(self, source_filepath, dest_path, force_build_files = False):
        stuff = pathlib.Path(source_filepath)
        resource = stuff.stem.lower()
        parent = str(stuff.parent)

        client_file = dest_path + resource + '_client.zip'
        server_file = dest_path + resource + '_server.json'

        #need to see if the shp file has been unpacked into a greojson file previously
        #as the shp->geojson takes a 'while' and it's worth keeping the local results
        localdestfilepath = parent+'/'+ resource.lower() +'.geojson'


        build_output_files = False
        #extract geojson resource
        if self.local_file_exists(localdestfilepath) == False or self.compare_local_dates(source_filepath, localdestfilepath) < 0 or force_build_files:
            if not self.convert_files:
                print('SHP2USR:  Build geojson:' + source_filepath + ' -> ' +localdestfilepath )
            else:
                myshpfile = geopandas.read_file(source_filepath)
                myshpfile.to_file(localdestfilepath, driver='GeoJSON')

                f = open(localdestfilepath, 'r')
                json_data = unexeaqua3s.json.load(f)
                f.close()

                src_crs = 4326
                dst_crs = 4326
                flip_coords = False
                target_format = ''

                if "crs" in json_data:
                    if json_data['crs']['properties']['name'] == 'urn:ogc:def:crs:EPSG::32632':
                        src_crs = 32632
                        flip_coords = True
                        target_format = 'urn:ogc:def:crs:OGC:1.3:CRS84'

                    if json_data['crs']['properties']['name'] == 'urn:ogc:def:crs:EPSG::6708':
                        src_crs = 3065  # 6708
                        target_format = 'urn:ogc:def:crs:OGC:1.3:CRS84'
                        flip_coords = True

                    if json_data['crs']['properties']['name'] == 'urn:ogc:def:crs:EPSG::6312':
                        src_crs = 6312  # 6708
                        target_format = 'urn:ogc:def:crs:OGC:1.3:CRS84'
                        flip_coords = True

                    if json_data['crs']['properties']['name'] == 'urn:ogc:def:crs:EPSG::31370':
                        src_crs = 31370  # 6708
                        target_format = 'urn:ogc:def:crs:OGC:1.3:CRS84'
                        flip_coords = True
                else:
                    src_crs = 31370  # 6708
                    target_format = 'urn:ogc:def:crs:OGC:1.3:CRS84'
                    flip_coords = True


                if src_crs != dst_crs:
                    if 'crs' not in json_data:
                        json_data['crs'] = {}
                        json_data['crs']['properties'] = {}
                        json_data['crs']['properties']['name'] = ''

                    json_data['crs']['properties']['name'] = target_format

                    json_data = unexeaqua3s.geojson2aqua3s.transform_coords(json_data, src_crs, dst_crs, flip_coords)
                    f = open(localdestfilepath, 'w')
                    f.write(unexeaqua3s.json.dumps(json_data))
                    f.close()

            build_output_files = True

        if build_output_files != True:
            #are the output files present?
            if not self.local_file_exists(dest_path + resource + '_client.zip') or not self.local_file_exists(dest_path + resource + '_server.json'):
                build_output_files = True

            #is the localdestfilepath newer than the output files?
            if self.compare_local_dates(localdestfilepath, dest_path + resource + '_client.zip') < 0:
                build_output_files = True

            if self.compare_local_dates(localdestfilepath, dest_path + resource + '_server.json') < 0:
                build_output_files = True

        #convert resource to userlayer
        if build_output_files == True:
            self.geojson_to_userfile(resource,localdestfilepath,  client_file, server_file)

        return ['UserLayer', resource, [client_file, server_file]]

    def geojson_to_userfile(self, resource_name,geojson_file, client_filepath, server_filepath):
        if not self.convert_files:
            print('USERFILE build: ' + geojson_file + ' -> ' + client_filepath)
            print('USERFILE build: ' + geojson_file + ' -> ' + server_filepath)
        else:
            unexeaqua3s.geojson2aqua3s.convert_file(geojson_file,  resource_name, client_filepath, server_filepath, '#ff0000')

    def process_kmz_resources(self):
        resources = []
        for service in self.fiware_service_list:
            root = self.local_root+service+'/kmz/'
            if self.local_path_exists(root):
                kmz_files = self.get_local_files(root)

                for src in kmz_files:
                    if src.endswith('.kmz'):
                        dst = self.local_root+service+'/userlayer/'
                        resources.append(self.convert_kml_to_userlayer(src, dst))

        return resources

    def process_waternetwork_resources(self):
        #build waternetwork resources
        resources = []
        try:
            for service in self.fiware_service_list:
                #is there a file in the epanet/ folder?
                files = self.get_local_files(self.local_root + service + '/epanet/')
                for file in files:
                    if file.endswith('.inp'):
                        dst = self.local_root + service + '/waternetwork/epanet.inp'
                        if self.convert_files:
                            path = os.path.dirname(dst)
                            unexefiware.file.buildfilepath(path)
                            shutil.copy(file, dst)
                        else:
                            print('COPY ' +file + ' -> ' + dst)

                #is there one in the waternetwork/ folder?
                inp_file = self.local_root + service + '/waternetwork/epanet.inp'
                bin_file = self.local_root + service + '/waternetwork/epanet.bin'
                rpt_file = self.local_root + service + '/waternetwork/epanet.rpt'

                if self.local_file_exists(inp_file):
                    #build .bin file
                    if self.convert_files:
                        ph = en.createproject()
                        en.runproject(ph, inp_file, rpt_file, bin_file, None)
                    else:
                        print('EPANET SIM ' + inp_file + ' -> ' + bin_file)

                    resources.append(['WaterNetwork', 'epanet', [inp_file]])
                    resources.append(['SimulationResult', 'epanet', [bin_file]])

        except Exception as e:
            self.logger.fail(inspect.currentframe(), 'Error: ' + str(e) )

        return resources

    def process_shapefile_resources(self, force_build_files = False):
        resources = []

        for service in self.fiware_service_list:
            root = self.local_root + service + '/shapefile/'
            if self.local_path_exists(root):
                files = self.get_local_files(root)

                for src in files:
                    if src.endswith('.shp'):
                        dst = self.local_root + service + '/userlayer/'
                        resources.append(self.convert_shapefile_to_userlayer(src, dst,force_build_files))

        return resources

    def create_fiware_assets(self, url, resources, upload_files = False):
        #1.for each fiware_service, delete all the existing fiware assets (WaterNetwork, SimulationResult, UserLayer)

        session = requests.Session()
        types = ['WaterNetwork', 'SimulationResult', 'UserLayer']
        link = 'https://schema.lab.fiware.org/ld/context'

        print('Delete resources')
        for service in self.fiware_service_list:
            for model_type in types:
                result = unexefiware.ngsildv1.get_type_count_orionld(session, url, model_type,link=link, fiware_service=service)

                if result[0] == 200:
                    # delete all the existing entries
                    item_count = result[1]['entityCount']

                    for i in range(0, item_count):
                        text = str(i) + ': '
                        try:
                            # get first entry in the list, rather than ith one as it will move :S
                            result = unexefiware.ngsildv1.get_type_by_index_orionld(session, url, model_type, 0, link=link, fiware_service=service)
                            if result[0] == 200:
                                if len(result[1]) > 0:
                                    result = unexefiware.ngsildv1.delete_instance(session, url, result[1][0]['id'], link, service)

                                    if result[0] != 200:
                                        print('Deletion failed: ' + str(result) )
                            else:
                                print('Deletion Get failed: ' + str(result) )

                        except Exception as e:
                            print('Vague failure: ' + str(e))

        print('Deleted')
        #2.for each resource, add to fiware & copy to webdav
        #make something to hold item indicies for each model type by service
        id_lookups = {}

        for service in self.fiware_service_list:

            if service not in id_lookups:
                id_lookups[service] = {}

            for model_type in types:
                if model_type not in id_lookups[service]:
                    id_lookups[service][model_type] = 1

                for resource in resources:
                    if resource[0] == model_type and self.resource_belongs_to_service(service, resource):

                        assets = resource[2]

                        if model_type == 'UserLayer':
                            if len(assets) == 2:

                                item_id = 'urn:ngsi-ld:' + model_type + ':' + str(id_lookups[service][model_type]).zfill(2)
                                print('Building fiware: ' + resource[0] + ':' + resource[1] +' ->' + item_id)

                                userlayer_instance = {}

                                unexefiware.model.add(userlayer_instance, "@context", link)
                                unexefiware.model.add(userlayer_instance, "id", item_id)
                                unexefiware.model.add(userlayer_instance, "type", model_type)
                                unexefiware.model.add_property(userlayer_instance, "name", resource[1])
                                unexefiware.model.add_property(userlayer_instance, "dateCreated", unexefiware.time.datetime_to_fiware(datetime.datetime.now()))
                                unexefiware.model.add_property(userlayer_instance, "client_file_path", self.get_remote_filepath(assets[0]))
                                unexefiware.model.add_property(userlayer_instance, "server_file_path", self.get_remote_filepath(assets[1]))

                                result = unexefiware.ngsildv1.create_instance(session, url, unexeaqua3s.json.dumps(userlayer_instance), service)

                                if upload_files:
                                    for file_index in range(0, len(assets)):
                                        self.upload_file(assets[file_index])

                                if result[0] == 201:
                                    id_lookups[service][model_type] += 1
                                else:
                                    print('Failed: ' + result[1])

                        if model_type == 'WaterNetwork':
                            if len(assets) == 1:

                                item_id = 'urn:ngsi-ld:' + model_type + ':' + str(id_lookups[service][model_type]).zfill(2)
                                print('Building fiware: ' + resource[0] + ':' + resource[1] +' ->' + item_id)

                                userlayer_instance = {}

                                unexefiware.model.add(userlayer_instance, "@context", link)
                                unexefiware.model.add(userlayer_instance, "id", item_id)
                                unexefiware.model.add(userlayer_instance, "type", model_type)
                                unexefiware.model.add_property(userlayer_instance, "name", resource[1])
                                unexefiware.model.add_property(userlayer_instance, "dateCreated", unexefiware.time.datetime_to_fiware(datetime.datetime.now()))
                                unexefiware.model.add_property(userlayer_instance, "file_path", self.get_remote_filepath(assets[0]))

                                result = unexefiware.ngsildv1.create_instance(session, url, unexeaqua3s.json.dumps(userlayer_instance), service)

                                if upload_files:
                                    for file_index in range(0, len(assets)):
                                        self.upload_file(assets[file_index])

                                if result[0] == 201:
                                    id_lookups[service][model_type] += 1
                                else:
                                    print('Failed: ' + result[1])


                        if model_type == 'SimulationResult':
                            if len(assets) == 1:

                                item_id = 'urn:ngsi-ld:' + model_type + ':' + str(id_lookups[service][model_type]).zfill(2)
                                print('Building fiware: ' + resource[0] + ':' + resource[1] +' ->' + item_id)

                                userlayer_instance = {}

                                unexefiware.model.add(userlayer_instance, "@context", link)
                                unexefiware.model.add(userlayer_instance, "id", item_id)
                                unexefiware.model.add(userlayer_instance, "type", model_type)
                                unexefiware.model.add_property(userlayer_instance, "name", resource[1])
                                unexefiware.model.add_property(userlayer_instance, "dateCreated", unexefiware.time.datetime_to_fiware(datetime.datetime.now()))
                                unexefiware.model.add_property(userlayer_instance, "file_path", self.get_remote_filepath(assets[0]))

                                result = unexefiware.ngsildv1.create_instance(session, url, unexeaqua3s.json.dumps(userlayer_instance), service)

                                if upload_files:
                                    for file_index in range(0, len(assets)):
                                        self.upload_file(assets[file_index])

                                if result[0] == 201:
                                    id_lookups[service][model_type] += 1
                                else:
                                    print('Failed: ' + result[1])


    def resource_belongs_to_service(self, service, resource):
        if len(resource) < 3:
            return False

        assets = resource[2]

        if len(assets) > 0:
            for file in assets:
                if '/'+service+'/' not in file:
                    return False
            return True

        return False
