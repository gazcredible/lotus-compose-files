import os

def buildfilepath(path):
    path = os.path.normpath(path)
    folders = path.split(os.sep)

    file_path = folders[0] +os.sep

    for i in range(1, len(folders)):
        file_path += folders[i] +os.sep

        if not os.path.exists(file_path):
            os.mkdir(file_path)