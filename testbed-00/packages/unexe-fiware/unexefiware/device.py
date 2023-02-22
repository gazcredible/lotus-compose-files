
def get_device_from_orion_data(device_data, device_name):
    for device in device_data:
        if device['id'] == device_name:
            return device


def get_short_id(device):
    return get_id(device)[19:]

def get_id(device):
    try:
        return device['id']
    except Exception as e:
        print('get_id()-' + str(e))

    return 'NO ID'

def get_state(device):
    try:
        for key in device:
            if 'controlledProperty' in key:
                return device[key]['value']
    except Exception as e:
        print('get_state()-' + str(e))

    return 'NO ID'

def get_name(device):
    try:
        return device['name']['value']
    except Exception as e:
        print('get_name()-' + str(e))

    return 'NO ID'

def get_controlled_properties(device):
    controlled_props = []

    controlled_property_label = ''
    for key in device:
        if 'controlledProperty' in key:
            controlled_property_label = key

    if isinstance(device[controlled_property_label]['value'], str) == True:
        controlled_props.append(device[controlled_property_label]['value'])
    else:
        for prop in device[controlled_property_label]['value']:
            controlled_props.append(prop)

    return controlled_props

def _get_property_from_label(device, property):
    try:
        if property in device:
            return device[property]

        for label in device:
            if property in label:
                return device[label]

        return None
    except Exception as e:
        print('_get_property_from_label()-' + str(e))


def get_property_value(device, property):
    try:
        data = _get_property_from_label(device, property)
        if data != None:
            return data['value']

        print('get_property_value()-' + 'no property:' + property)
        return 0
    except Exception as e:
        print('get_property_value()-' + str(e))

    return 0

def get_property_observedAt(device, property):
    try:
        data = _get_property_from_label(device, property)
        if data != None:
            return data['observedAt']

        print('get_property_value()-' + 'no property:' + property)
        return 0
    except Exception as e:
        print('get_property_value()-' + str(e))

    return 0



def get_property_unitcode(device, property):
    try:
        data = _get_property_from_label(device, property)
        if data != None:
            return data['unitCode']

    except Exception as e:
        print('get_property_unitcode()-' + str(e))

    print('get_property_unitcode()-' + 'no property:' + property)
    return 'n/a'
