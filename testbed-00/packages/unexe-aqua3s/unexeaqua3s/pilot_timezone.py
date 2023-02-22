import pytz

def get(fiware_service):
    if fiware_service == 'AAA':
        return pytz.timezone('Europe/Rome')

    if fiware_service == 'SOF':
        return pytz.timezone('Europe/Sofia')

    if fiware_service == 'SVK':
        return pytz.timezone('Europe/Sofia')

    if fiware_service == 'EYA':
        return pytz.timezone('Europe/Athens')


    return pytz.timezone('CET')

    raise Exception('No TZ for service:'+fiware_service)
