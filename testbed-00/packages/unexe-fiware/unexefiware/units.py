import json
import pkg_resources


def get_property_printname(prop):
    if prop == 'level':
        return 'Level'

    if prop.lower() == 'ph':
        return 'pH'

    if prop == 'turbidity':
        return 'Turbidity'

    if prop == 'conductibility' or prop == 'conducibility':
        return 'Conductibility'

    if prop.lower() == 'uv':
        return 'UV'

    if prop == 'discharge':
        return 'Discharge'

    if prop == 'pressure':
        return 'Pressure'

    if prop == 'refractive index':
        return 'Refractive Index'

    if prop.lower() == 'freechlorine':
        return 'Residual Chlorine'

    if prop.lower() == 'conductivity':
        return 'Conductivity'

    if prop.lower() == 'orp':
        return 'ORP'

    if prop.lower() == 'toc':
        return 'TOC'

    if prop.lower() == 'temperature':
        return 'Temperature'

    if prop.lower() == 'uv254':
        return 'UV'

    return prop
    return '?prop:' + prop


unitcode_lookup = None


def get_property_unitcode_printname(unitCode):
    global unitcode_lookup
    if unitcode_lookup == None:
        json_file = pkg_resources.resource_stream(__name__, 'data/unitcodes.json')
        unitcode_lookup = json.load(json_file)

    if unitCode == 'TUR' or unitCode == 'NTU':
        return 'NTU'

    if unitCode == 'UV':
        return ''  # 'UV'

    if unitCode == 'm3/h':
        unitCode = 'MQH'

    if unitCode == 'Q30': #pH
        return ''

    try:
        return unitcode_lookup[unitCode]
    except Exception as e:

        if unitCode.lower() == 'E-12'.lower():
            return 'pm'

        if unitCode.lower() == 'E-11'.lower():
            return 'pm'

        if unitCode.lower() == '59'.lower():
            return 'ppm'

        if unitCode.lower() == 'P1'.lower():
            return '%'

        return unitCode
        return '?' + unitCode

    try:
        if unitCode == 'CND':
            return 'mS/cm'

        if unitCode == 'DIS' or unitCode == 'm3/h':
            return 'm<sup>3</sup>/h'

        if unitCode == 'LVL' or unitCode == 'MTR':
            return 'm'

        if unitCode == 'PH' or unitCode == 'Q30':
            return ''  # 'pH'

        if unitCode == 'PSR':
            return 'mH<sub>2</sub>0'
        if unitCode == 'TUR' or unitCode == 'NTU':
            return 'NTU'
        if unitCode == 'UV':
            return ''  # 'UV'
        if unitCode == 'RI':
            return 'ppm'

        if unitCode == 'N23':
            return 'N23'

        if unitCode == 'H61':
            return 'H61'

        return '?' + unitCode
    except Exception as e:
        print('get_property_unitcode_printname()-' + str(e))

    return unitCode
    return '??' + unitCode