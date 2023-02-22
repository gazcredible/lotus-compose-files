import unexefiware.debug
import inspect

def get_entity_from_orion_list(list_data, id):
    for entity in list_data:
        if entity['id'] == id:
            return entity

    return None


def get_property_from_label(model, property):
    try:
        if property in model:
            return model[property]

        for label in model:
            if property in label:
                return model[label]

        #GARETH - don't do this
        # raise Exception('Not found')
    except Exception as e:
        print(unexefiware.debug.formatmsg(inspect.currentframe(), str(e)))

    return None

def has_property_from_label(model, property):
    if property in model:
        return model[property]

    for label in model:
        if property in label:
            return model[label]

    return None


def get_property_value(model, property):
    try:
        data = get_property_from_label(model, property)
        if data != None:
            return data['value']

        raise Exception('Not found')
    except Exception as e:
        print(unexefiware.debug.formatmsg(inspect.currentframe(), str(e)))

    return 0


def has_property_observedAt(model, property):

    if has_property_from_label(model,property):
        data = get_property_from_label(model, property)
        if data != None:
            return 'observedAt' in data

    return False

def get_property_observedAt(model, property):
    try:
        data = get_property_from_label(model, property)
        if data != None:
            return data['observedAt']

        raise Exception('Not found')
    except Exception as e:
        print(unexefiware.debug.formatmsg(inspect.currentframe(), str(e)))

    return 0


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


def get_property_unitcode(model, property):
    try:
        data = get_property_from_label(model, property)
        if data != None:
            if 'unitCode' in data:
                return data['unitCode']

        raise Exception('Not found')

    except Exception as e:
        print(unexefiware.debug.formatmsg(inspect.currentframe(), str(e)))

    return 'n/a'


def add(data, key, value):
    if key in data:
        raise Exception('Duplicate Key: ' + key)

    data[key] = value


def create(key, value):
    data = {}
    data[key] = value

    return data


def add_property(data, name, value):
    prop = {}
    add(prop, "type", "Property")
    add(prop, "value", value)

    add(data, name, prop)
