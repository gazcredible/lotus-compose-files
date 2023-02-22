import os
import platform

if 'DEVICE_BROKER' not in os.environ:
    print('No environ!')
    print(platform.system())

    my_broker = ''

    if False:  # USE_DEMO_SERVER (Yorgos)
        os.environ['DEVICE_BROKER'] = 'https://platform.aqua3s.eu/orion'
        os.environ['DEVICE_HISTORIC_BROKER'] = 'https://platform.aqua3s.eu/api_cygnus'
        my_broker = 'http://52.50.143.202:8101'
        #my_broker = 'http://0.0.0.0:10101'

        os.environ['VISUALISER'] = 'http://52.50.143.202:8100/'
        os.environ['CYGNUS_HACK_ADDRESS'] = 'http://52.50.143.202:1337'

        #os.environ['VISUALISER'] = 'http://localhost:10100'

        os.environ['WORKHOUSE_BROKER'] = 'http://52.50.143.202:81102'
    else:
        my_broker = 'http://localhost:10101'
        my_broker = 'http://0.0.0.0:10101'

        #my_broker = 'http://46.101.61.143:8101'

        os.environ['DEVICE_BROKER'] = my_broker
        os.environ['DEVICE_HISTORIC_BROKER'] = my_broker
        os.environ['VISUALISER'] = 'http://localhost:10100'
        #use my visualiser
        #os.environ['VISUALISER'] = 'http://46.101.61.143:8100'


    os.environ['PROCESSOR_SERVER'] = 'http://localhost:10103'


    os.environ['ALERT_BROKER'] = my_broker
    os.environ['PILOTS'] = 'AAA,SVK,WBL,SOF,BDI'
    os.environ['PILOTS'] = 'P2B'
    os.environ['PILOTS'] = 'AAA,SOF,SVK,WBL,EYA'
    os.environ['PILOTS'] = 'AAA,SVK,SOF,EYA,WBL,BDI'

    os.environ['ALERT_HISTORIC_BROKER'] = my_broker
    #os.environ['ALERT_SLEEP_TIME'] = '20'
    os.environ['ANOMALY_BROKER'] = my_broker
    os.environ['ANOMALY_HISTORIC_BROKER'] = my_broker
    os.environ['USERLAYER_BROKER'] = my_broker
    os.environ['OTHER_BROKER'] = my_broker
    os.environ['ANOMALY_SLEEP_TIME'] = '20'
    os.environ['AAANDC_SLEEP_TIME'] = '600'

    os.environ['REMOTE_LOGGING_URL'] = 'https://platform.aqua3s.eu/logging_api_dev/'
    os.environ['REMOTE_LOGGING_ENABLED'] = 'False'

    os.environ['KEYROCK_ADMIN_NAME'] = 'admin@aqua3s.eu'
    os.environ['KEYROCK_ADMIN_PASS'] = 'a28d7736b648515d'

    # os.environ['WEBDAV_URL']='https://platform.aqua3s.eu/intrf_webdav'
    os.environ['WEBDAV_URL'] = 'http://52.50.143.202:8443/webdav'
    os.environ['WEBDAV_URL'] = 'http://46.101.61.143:8220'
    os.environ['WEBDAV_NAME'] = 'unexe'
    os.environ['WEBDAV_PASS'] = 'Jufglw3252G92'

    path = '/docker/aqua3s-brett-test/'

    if platform.system().lower() == 'windows':
        os.environ['FILE_PATH'] = 'c:' + path
    else:
        os.environ['FILE_PATH'] = path
