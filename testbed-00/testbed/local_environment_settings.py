import os
import platform

if 'DEVICE_BROKER' not in os.environ:
    print('No environ!')
    print(platform.system())

    target_enviroment = 'windows.box'
    target_enviroment = 'local.docker'
    target_enviroment = 'local.bench'

    my_broker = ''

    os.environ['FILE_VISUALISER_FOLDER'] = 'visualis3r'
    os.environ['PILOTS'] = 'AAA,GUW'

    if target_enviroment == 'local.bench':
        #this is my local daocker install on localhost
        ip = 'http://127.0.0.1'

        os.environ['DEVICE_BROKER'] = ip +':7111'
        os.environ['VISUALISER'] = ip + ':7110'

        os.environ['WEBDAV_URL'] = ip + ':7130'
        os.environ['WEBDAV_NAME'] = 'admin'
        os.environ['WEBDAV_PASS'] = 'admin'

        os.environ['REMOTE_LOGGING_URL'] = ''
        os.environ['REMOTE_LOGGING_ENABLED'] = 'False'

        path = '/docker/lotus-visualiser-local-bench/'

        if platform.system().lower() == 'windows':
            os.environ['FILE_PATH'] = 'c:' + path
        else:
            os.environ['FILE_PATH'] = path


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

        if platform.system().lower() == 'windows':
            os.environ['FILE_PATH'] = 'c:' + path
        else:
            os.environ['FILE_PATH'] = path


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

        if platform.system().lower() == 'windows':
            os.environ['FILE_PATH'] = 'c:' + path
        else:
            os.environ['FILE_PATH'] = path

    #historic broker division
    os.environ['DEVICE_HISTORIC_BROKER'] = os.environ['DEVICE_BROKER']
    os.environ['USERLAYER_BROKER'] = os.environ['DEVICE_BROKER']

    if False:
        os.environ['VISUALISER'] = 'http://localhost:21100'
        os.environ['VISUALISER'] = 'http://46.101.61.143:7100'


        if False: #USE_DEMO_SERVER
            my_broker = 'http://46.101.61.143:7101'
            os.environ['DEVICE_BROKER'] = my_broker
            os.environ['DEVICE_HISTORIC_BROKER'] = os.environ['DEVICE_BROKER']

            os.environ['VISUALISER'] = 'http://46.101.61.143:7100'
        else:
            my_broker = 'http://0.0.0.0:7101'

            #local docker broker
            #my_broker = 'http://0.0.0.0:21101'

            os.environ['DEVICE_BROKER'] = my_broker
            os.environ['DEVICE_HISTORIC_BROKER'] = my_broker
            os.environ['VISUALISER'] = 'http://0.0.0.0:7100'
            os.environ['VISUALISER'] = 'http://0.0.0.0:21100' #local testing

        os.environ['ALERT_BROKER'] = my_broker
        os.environ['PILOTS'] = 'GUW,AAA'

        os.environ['ALERT_HISTORIC_BROKER'] = my_broker
        os.environ['ALERT_SLEEP_TIME'] = '20'
        os.environ['ANOMALY_BROKER'] = my_broker
        os.environ['ANOMALY_HISTORIC_BROKER'] = my_broker
        os.environ['USERLAYER_BROKER'] = my_broker
        os.environ['OTHER_BROKER'] = my_broker
        os.environ['ANOMALY_SLEEP_TIME'] = '20'
        os.environ['AAANDC_SLEEP_TIME'] = '600'

        os.environ['REMOTE_LOGGING_URL'] = ''
        os.environ['REMOTE_LOGGING_ENABLED'] = 'False'

        os.environ['KEYROCK_ADMIN_NAME'] = 'None'
        os.environ['KEYROCK_ADMIN_PASS'] = 'None'


        os.environ['WEBDAV_URL'] = 'http://0.0.0.0:7120/'
        os.environ['WEBDAV_NAME'] = 'admin'
        os.environ['WEBDAV_PASS'] = 'admin'