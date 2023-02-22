import webdav3
from webdav3.client import Client
import urllib3
import pathlib
import os
import datetime
import dateutil
import glob
import shutil
import inspect
import unexefiware.base_logger
import unexefiware.file


class webdav:
    def __init__(self, options):

        urllib3.disable_warnings()

        self.options = options

        self.client = Client(self.options)
        self.client.verify = False  # To not check SSL certificates (Default = True)

        self.local_root = 'data/'
        self.remote_root = ''
        self.logger = unexefiware.base_logger.BaseLogger()

        self.perform_file_operations = False

    def is_remote_available(self):
        try:
            info = self.client.list(self.remote_root)
            return True
        except Exception as e:
            return False

    def print_remote_tree(self, root):
        if not self.isDir(root):
            raise Exception('Not a dir! ' + root)

        try:
            info = self.client.list(root)
            #info.pop(0)#remove current dir

            for entry in info:
                if entry[0] != '.':
                    if entry.endswith('/'):
                        try:
                            self.print_remote_tree(root+entry)
                        except Exception as e:
                            pass
                    else:
                        src  = root+entry
                        print(src)
        except Exception as e:
            pass



    def get_remote_filepath(self, local_filepath):
        return local_filepath.replace(self.local_root, self.remote_root)

    def get_local_filepath(self, remote_filepath):
        return remote_filepath.replace(self.remote_root, self.local_root )

    def clone_remote(self, root, local_root, copy_files=True):
        self.logger.log(inspect.currentframe(),'Clone: '+root)
        if not self.isDir(root):
            raise Exception('Not a dir! ' + local_root)

        if not self.isDir(local_root):
            raise Exception('Not a dir! ' + local_root)

        if not pathlib.Path(local_root).exists():
            unexefiware.file.buildfilepath(local_root)

        try:
            info = self.client.list(root)
            #info.pop(0)#remove current dir

            for entry in info:
                if entry[0] != '.':
                    if entry.endswith('/'):
                        try:
                            self.clone_remote(root+entry,local_root+entry,copy_files)
                        except Exception as e:
                            pass
                    else:
                        src  = root+entry
                        dst = local_root+entry

                        if copy_files == True:
                            self.download_file(filepath=src)
        except Exception as e:
            pass

    def upload_to_remote(self, remote_root, local_root):
        #go through all the files in the local root and work out where to stick them on the server ...
        files = self.get_local_files(local_root)

        for file in files:
            stuff = pathlib.Path(file)

            if stuff.stem[0] != '.':
                dst = file
                dst = dst.replace(local_root, remote_root)

                data = pathlib.Path(file).stat()

                print(file)
                print('C:' + str(datetime.datetime.fromtimestamp(data.st_ctime, tz=datetime.timezone.utc)))
                print('M:' + str(datetime.datetime.fromtimestamp(data.st_mtime, tz=datetime.timezone.utc)))
                print('A:' + str(datetime.datetime.fromtimestamp(data.st_atime, tz=datetime.timezone.utc)))

                if self.compare_webdav_with_local_date(dst, file) > 0:
                    print ('UPLOAD ' + file + ' TO ' + dst)
                    #self.client.upload_file(remote_path = dst, local_path=file)
                print()

    def get_local_files(self,root):
        filelist = []
        for path in pathlib.Path(root).rglob('*.*'):
            if not os.path.isdir(path):
                filelist.append(str(path))

        return filelist

    def isDir(self, path):
        return path.endswith('/')

    def isDeleted(self, path):
        return path.startswith('.')

    def compare_webdav_with_local_date(self, webdav_resource, local_resource):

        if os.path.isfile(local_resource) == False:
            return -1 #local file doesn't exist

        try:
            src_info = self.client.info(webdav_resource)
        except Exception as e:
            return -1 #file does not exist on server

        dst_info = datetime.datetime.fromtimestamp(pathlib.Path(local_resource).stat().st_mtime)

        src_info = dateutil.parser.parse(src_info['modified'])

        #sigh
        src_info = src_info.replace(tzinfo=None)

        diff = dst_info - src_info

        return diff.total_seconds()

    def compare_local_dates(self, file_1, file_2):

        if os.path.isfile(file_2) == False:
            return -1 #local file doesn't exist

        src_info = datetime.datetime.fromtimestamp(pathlib.Path(file_1).stat().st_mtime)
        dst_info = datetime.datetime.fromtimestamp(pathlib.Path(file_2).stat().st_mtime)


        diff = dst_info - src_info

        return diff.total_seconds()

    def local_file_exists(self, filename):
        return  pathlib.Path(filename).exists()

    def local_path_exists(self, path):
        return os.path.exists(path)

    def delete_local_dir(self, path):
        if self.local_path_exists(path):
            shutil.rmtree(path)

    def create_local_dir(self, path):
        if not self.local_path_exists(path):
            os.mkdir(path)

    def upload_file(self, filepath):
        print('DAVCOPY: ' + filepath + ' -> ' + self.get_remote_filepath(filepath) )

        remote_file_path = self.get_remote_filepath(filepath)
        self.dav_buildfilepath(os.path.dirname(remote_file_path))
        self.client.upload_file(remote_path=remote_file_path, local_path=filepath)

    def download_file(self, filepath):
        src = filepath
        dst = self.get_local_filepath(filepath)

        if src == dst:
            self.logger.log(inspect.currentframe(), 'duplicate paths!')
            raise Exception('duplicate paths!')

        if self.compare_webdav_with_local_date(src, dst) < 0:  # src is newer than dst -> update dst
            if self.perform_file_operations == True:
                self.logger.log(inspect.currentframe(), 'DAVCOPY: ' + src + ' -> ' + dst)

                try:
                    unexefiware.file.buildfilepath(os.path.dirname(dst))
                    self.client.download_file(src, dst)
                except Exception as e:
                    self.logger.log(inspect.currentframe(), 'NO DAVCOPY: ' + src + ' -> ' + dst + '- ' + str(e))
            else:
                self.logger.log(inspect.currentframe(), 'NO DAVCOPY: ' + src + ' -> ' + dst + '- No file operations')
        else:
            self.logger.log(inspect.currentframe(),'No DAVCOPY: ' + src + ' -> ' + dst + ' - Datestamp')

    def dav_buildfilepath(self, path):
        path = os.path.normpath(path)
        folders = path.split(os.sep)

        file_path = ''

        for i in range(0, len(folders)):
            file_path += folders[i] + os.sep

            if not os.path.exists(file_path):
                self.client.mkdir(file_path)