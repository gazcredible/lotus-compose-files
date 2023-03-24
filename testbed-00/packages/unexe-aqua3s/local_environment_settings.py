import os
import platform

if 'DEVICE_BROKER' not in os.environ:
    print('No environ!')
    print(platform.system())

    target_enviroment = 'windows.box'
    target_enviroment = 'local.docker'
    target_enviroment = 'local.bench'

    my_broker = ''
    path = ''

    os.environ['FILE_VISUALISER_FOLDER'] = 'visualis3r'
    #os.environ['PILOTS'] = 'AAA,GUW'
    os.environ['PILOTS'] = 'GUW'

    if target_enviroment == 'local.bench':
        #this is my local daocker install on localhost
        ip = 'http://127.0.0.1'

        os.environ['PILOTS'] = 'TTT'

        os.environ['DEVICE_BROKER'] = ip +':7111'
        os.environ['VISUALISER'] = ip + ':7110'

        os.environ['WEBDAV_URL'] = ip + ':7120' #this is the docker image!
        os.environ['WEBDAV_NAME'] = 'admin'
        os.environ['WEBDAV_PASS'] = 'admin'

        os.environ['REMOTE_LOGGING_URL'] = ''
        os.environ['REMOTE_LOGGING_ENABLED'] = 'False'

        path = '/docker/lotus-visualiser-local-bench/'

    if target_enviroment == 'local.docker':
        #this is my local daocker install on localhost
        ip = 'http://0.0.0.0'

        os.environ['DEVICE_BROKER'] = ip +':7101'
        os.environ['VISUALISER'] = ip + ':7100'

        os.environ['WEBDAV_URL'] = ip + ':7120'
        os.environ['WEBDAV_NAME'] = 'admin'
        os.environ['WEBDAV_PASS'] = 'admin'

        os.environ['REMOTE_LOGGING_URL'] = ''
        os.environ['REMOTE_LOGGING_ENABLED'] = 'False'

        path = '/docker/lotus-visualiser-local-docker/'

    if target_enviroment == 'windows.box':
        #this is my test pc with windows & docker
        ip = 'http://192.168.0.18'

        os.environ['DEVICE_BROKER'] = ip +':7101'
        os.environ['DEVICE_HISTORIC_BROKER'] = os.environ['DEVICE_BROKER']

        os.environ['VISUALISER'] = ip + ':7100'

        os.environ['WEBDAV_URL'] = ip + ':7120'
        os.environ['WEBDAV_NAME'] = 'admin'
        os.environ['WEBDAV_PASS'] = 'admin'

        os.environ['REMOTE_LOGGING_URL'] = ''
        os.environ['REMOTE_LOGGING_ENABLED'] = 'False'

        path = '/docker/lotus-visualiser-windows-box/'

    if path == '':
        raise Exception('Data path not set')

    if platform.system().lower() == 'windows':
        os.environ['FILE_PATH'] = 'c:' + path
    else:
        os.environ['FILE_PATH'] = path

    #historic broker division
    os.environ['DEVICE_HISTORIC_BROKER'] = os.environ['DEVICE_BROKER']
    os.environ['USERLAYER_BROKER'] = os.environ['DEVICE_BROKER']

    os.environ['ALERT_MAIL'] = 'False'
    os.environ['CERTH_ALERT_DATA'] = 'False'