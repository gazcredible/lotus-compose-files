# flake8: noqa: W293,E303,501

from typing import NamedTuple, Union, List
import json
from enum import Enum
import numpy as np
from pyproj import CRS, Transformer
from datetime import timedelta
import epanet.toolkit as en

from epanet_fiware.enumerations import NodeTypes
import epanet_fiware.enumerations as enu

class transformer:
    def __init__(self, source, dest = CRS.from_epsg(4326)):
        self.source = source
        self.dest = dest

        self.transformer = Transformer.from_crs(self.source, self.dest)

    def transform(self, x,y):
        if self.transformer is not None:
            return self.transformer.transform(x,y)
        else:
            return [x,y]


class CoordinateSystem(Enum):
    undefined = CRS.from_epsg(4326)
    wgs84 = CRS.from_epsg(4326)
    osgb = CRS.from_epsg(27700)
    sp = CRS.from_epsg(2278)
    UTMzone32N = CRS.from_epsg(32632)


LinkCommonData = NamedTuple('LinkCommonData', [
    ('Name', str),
    ('StartNodeIndex', int),
    ('EndNodeIndex', int),
    ('StartNodeID', str),
    ('EndNodeID', str),
    ('StartNodeType', str),
    ('EndNodeType', str),
    ('InitStatus', int),
    ('KBulk', float),
    ('KWall', float),
    ('LinkType', int),
    ('Vertices', Union[None, List[List[float]]])
])


NodeCommonData = NamedTuple('NodeCommonData', [
    ('Name', str),
    ('Position', List[float]),
    ('Elevation', float),
    ('InitQuality', float),
    ('SourceQuality', float),
    ('SourcePattern', int),
    ('SourcePatternName', str),
    ('SourceType', int),
    ('NodeType', int)
])


Units = NamedTuple('Units', [
    ('Concentration', Union[str, float]),
    ('Demand', Union[str, float]),
    ('DiameterPipes', Union[str, float]),
    ('DiameterTanks', Union[str, float]),
    ('Efficiency', Union[str, float]),
    ('Elevation', Union[str, float]),
    ('EmitterCoeff', Union[str, float]),
    ('Energy', Union[str, float]),
    ('Flow', Union[str, float]),
    ('Frictionfactor', Union[str, float]),
    ('Head', Union[str, float]),
    ('Length', Union[str, float]),
    ('MinorLossCoeff', Union[str, float]),
    ('Power', Union[str, float]),
    ('Pressure', Union[str, float]),
    ('ReactionCoeffBulk', Union[str, float]),
    ('ReactionCoeffWall0Order', Union[str, float]),
    ('ReactionCoeffWall1Order', Union[str, float]),
    ('RoughnessCoeffDW', Union[str, float]),
    ('RoughnessCoeffOther', Union[str, float]),
    ('SourceMassInjection', Union[str, float]),
    ('Velocity', Union[str, float]),
    ('Volume', Union[str, float]),
    ('WaterAge', Union[str, float]),
])


CURVE_TYPES = {
    0: 'LEVEL-VOLUME',      # EPANET VOLUME_CURVE
    1: 'FLOW-HEAD',         # EPANET PUMP_CURVE
    2: 'FLOW-EFFICIANCY',   # EPANET EFFIC_CURVE
    3: 'FLOW-HEADLOSS',     # EPANET HLOSS_CURVE
}


MIXING_MODELS = {
    0: 'MIXED',     # EPANET MIX1 (Complete mix model)
    1: '2COMP',     # EPANET MIX2 (2-compartment model)
    2: 'FIFO',      # EPANET FIFO (First in, first out model)
    3: 'LIFO'       # EPANET LIFO (Last in, first out models)
}


VALVE_TYPES = {
    3: 'PRV',
    4: 'PSV',
    5: 'PBV',
    6: 'FCV',
    7: 'TCV',
    8: 'GPV',
}


STATUSES = {
    0: 'CLOSED',
    1: 'OPEN',
    2: 'CV'
}


STANDARD_UNITS = {
    'Concentration': 'M1',              # mg/l
    'Demand': 'G52',                    # m3/d
    'DiameterPipes': 'MMT',             # mm
    'DiameterTanks': 'MTR',             # meters
    'Efficiency': 'P1',                 # percent
    'Elevation': 'MTR',                 # meters
    'EmitterCoeff': 'G52',              # Currently m3/d...
    # ... Should be m2/d (demand units divided by one unit of pressure drop,
    #  i.e.m^3/d/m), but no CEFACT code for this
    'Energy': 'KWH',                    # kWh
    'Flow': 'G52',                      # m3/d
    'Frictionfactor': 'C62',            # unitless
    'Head': 'MTR',                      # meters
    'Length': 'MTR',                    # meters
    'MinorLossCoeff': 'C62',            # unitless
    'Power': 'KWT',                     # kW
    'Pressure': 'MTR',                  # meters
    'ReactionCoeffBulk': 'E91',         # 1/d
    'ReactionCoeffWall0Order': 'RRC',   # mg/m2/day (not a CEFACT unit...
    # ...code but proposed in spec)
    'ReactionCoeffWall1Order': 'xxx',   # m/day
    'RoughnessCoeffDW': 'MMT',          # mm
    'RoughnessCoeffOther': 'C62',       # unitless
    'SourceMassInjection': 'xxx',       # ...
    'Velocity': 'MTS',                  # m/s
    'Volume': 'MTQ',                    # m
    'WaterAge': 'HUR',                  # hours
}


def _metric(flow_units_int: int):
    if flow_units_int >= 5:
        return True
    return False


def _get_unit_conversion_factors(flow_units_int):
    if flow_units_int < 0 | flow_units_int > 9:
        raise ValueError(
            'Error: Invalid flow units')
    flow_conversions = {
        0: 2446.575545549,      # Cubic feet per second to m3/d
        1: 5.450992969,         # Gallons per minute to m3/d
        2: 3785.411784028,      # Million gallons per day to m3/d
        3: 4546.09,             # Imperial million gallons per day to m3/d
        4: 1233.481837547,      # Acre-feet per day to m3/d
        5: 86.4,                # Liters per second to m3/d
        6: 1.44,                # Liters per minute to m3/d
        7: 0.00000144,          # Million liters per day to m3/d
        8: 24,                  # Cubic meters per hour to m3/d
        9: 1,                   # Cubic meters per day to m3/d
    }
    if _metric(flow_units_int):
        diameter_pipes = 1
        diameter_tanks = 1
        elevation = 1
        head = 1
        length = 1
        power = 1
        pressure = 1
        reaction_coeff_wall_0order = 1
        reaction_coeff_wall_1order = 1
        roughness_coeff_dw = 1
        velocity = 1
        volume = 1
    else:
        diameter_pipes = 25.4               # inches to mm
        diameter_tanks = 0.3048             # feet to meters
        elevation = 0.3048                  # feet to meters
        head = 0.3048                       # feet to meters
        length = 0.3048                     # feet to meters
        power = 1 / 1.341                   # hp to kW
        pressure = 0.70324961490205         # psi to meters
        reaction_coeff_wall_0order = 1 / (0.3048 ** 2)  # mass/sq-ft/day...
        # ...to mass/sq-m/day
        reaction_coeff_wall_1order = 0.3048  # ft/day to m/day
        roughness_coeff_dw = 0.3048         # millifeet to mm
        velocity = 0.3048                   # ft/s to m/s
        volume = 0.3048 ** 3                # ft3 to m3

    return Units(
        Concentration=1,
        Demand=flow_conversions[flow_units_int],
        DiameterPipes=diameter_pipes,
        DiameterTanks=diameter_tanks,
        Efficiency=1,
        Elevation=elevation,
        EmitterCoeff=flow_conversions[flow_units_int] / pressure,  # Demand...
        # ...units divided byone unit of pressure drop. For example...
        # ...m^3/hr/m or MQS/MTR
        Energy=1,
        Flow=flow_conversions[flow_units_int],
        Frictionfactor=1,
        Head=head,
        Length=length,
        MinorLossCoeff=1,
        Power=power,
        Pressure=pressure,
        ReactionCoeffBulk=1,
        ReactionCoeffWall0Order=reaction_coeff_wall_0order,
        ReactionCoeffWall1Order=reaction_coeff_wall_1order,
        RoughnessCoeffDW=roughness_coeff_dw,
        RoughnessCoeffOther=1,
        SourceMassInjection=1,
        Velocity=velocity,
        Volume=volume,
        WaterAge=1
    )


def json_ld_pattern(proj) -> json:
    data_all_components = []
    num_patterns = en.getcount(ph=proj, object=en.PATCOUNT)
    for pattern in range(num_patterns):
        index = pattern + 1
        name = en.getpatternid(ph=proj, index=index)
        length = en.getpatternlen(ph=proj, index=index)
        values = [en.getpatternvalue(proj, index, step)
                  for step in range(1, length + 1)]
        pattern_step = en.gettimeparam(proj, en.PATTERNSTEP)
        start_time_sec = en.gettimeparam(proj, en.PATTERNSTART)
        data_model_dict = {
            'id': 'urn:ngsi-ld:Pattern:{}'.format(name),
            'type': 'Pattern',
            'multipliers': {
                'type': 'Property',
                'value': values,
                'unitCode': 'C62'   # C62 = no unit
                },
            'timeStep': {
                'type': 'Property',
                'value': pattern_step,
                'unitCode': 'SEC'
            },
            'startTime': {
                'type': 'Property',
                'value': str(timedelta(seconds=start_time_sec))
            },
            '@context': [
                'https://schema.lab.fiware.org/ld/context'
            ]
        }
        data_all_components.append(data_model_dict)
    return data_all_components


def json_ld_curve(proj) -> json:
    data_all_components = []
    num_curves = en.getcount(ph=proj, object=en.CURVECOUNT)
    for curve in range(num_curves):
        index = curve + 1
        name = en.getcurveid(ph=proj, index=index)
        length = en.getcurvelen(ph=proj, index=index)
        x_values = [en.getcurvevalue(proj, index, step)[0]
                    for step in range(1, length + 1)]
        y_values = [en.getcurvevalue(proj, index, step)[1]
                    for step in range(1, length + 1)]
        curve_type = en.getcurvetype(proj, index)
        if curve_type == 4:
            # Skip if curve is a generic type (i.e. unused)
            continue
        flow_units = en.getflowunits(proj)
        conversion_factors = _get_unit_conversion_factors(flow_units)
        x_array = np.asarray(x_values)
        y_array = np.asarray(y_values)
        if curve_type == 0:
            x_data = x_array * conversion_factors.Elevation
            x_unit = STANDARD_UNITS['Elevation']
            y_data = y_array * conversion_factors.Volume
            y_unit = STANDARD_UNITS['Volume']
        else:
            x_data = x_array * conversion_factors.Flow
            x_unit = STANDARD_UNITS['Flow']
            if curve_type == 3:
                y_data = y_array
                y_unit = 'C62'
            else:
                y_data = y_array * conversion_factors.Elevation
                y_unit = STANDARD_UNITS['Elevation']
        data_model_dict = {
            'id': 'urn:ngsi-ld:Curve:{}'.format(name),
            'type': 'Curve',
            'curveType': {
                'type': 'Property',
                'value': CURVE_TYPES[curve_type],
            },
            'xData': {
                'type': 'Property',
                'value': list(x_data),
                'unitCode': x_unit
            },
            'yData': {
                'type': 'Property',
                'value': list(y_data),
                'unitCode': y_unit
            },
            '@context': [
                'https://schema.lab.fiware.org/ld/context'
            ]
        }
        data_all_components.append(data_model_dict)
    return data_all_components


def _get_node_common_data(
        proj, index: int) -> NodeCommonData:
    try:
        source_quality = en.getnodevalue(proj, index, en.SOURCEQUAL)
        source_type = en.getnodevalue(proj, index, en.SOURCETYPE)
    except Exception:
        source_quality = None
        source_type = None
    try:
        source_pattern = int(en.getnodevalue(proj, index, en.SOURCEPAT))
        source_pattern_name = en.getpatternid(proj, source_pattern)
    except Exception:
        source_pattern = None
        source_pattern_name = None
    try:
        position = en.getcoord(proj, index)
    except Exception:
        position = [0, 0]
    return NodeCommonData(
        Name=en.getnodeid(proj, index),
        Position=position,
        Elevation=en.getnodevalue(proj, index, en.ELEVATION),
        InitQuality=en.getnodevalue(proj, index, en.INITQUAL),
        SourceQuality=source_quality,
        SourcePattern=source_pattern,
        SourcePatternName=source_pattern_name,
        SourceType=source_type,
        NodeType=en.getnodetype(proj, index)
    )


def json_ld_reservoir(proj, transformer) -> json:
    
    data_all_components = []
    num_nodes = en.getcount(ph=proj, object=en.NODECOUNT)
    for node in range(num_nodes):
        index = node + 1
        node_type = en.getnodetype(ph=proj, index=index)
        if node_type == en.RESERVOIR:
            common_data = _get_node_common_data(proj, index)
            flow_units = en.getflowunits(proj)
            conversion_factors = _get_unit_conversion_factors(flow_units)

            coordinates = transformer.transform(common_data.Position[0], common_data.Position[1])

            data_model_dict = {
                'id': 'urn:ngsi-ld:Reservoir:{}'.format(common_data.Name),
                'type': 'Reservoir',
                'location': {
                    'type': 'GeoProperty',
                    'value': {
                        'type': 'Point',
                        'coordinates': coordinates
                    }
                },
                'reservoirHead': {
                    'type': 'Property',
                    'value': common_data.Elevation *
                    conversion_factors.Elevation,
                    'unitCode': STANDARD_UNITS['Head']
                },
                'initialQuality': {
                    'type': 'Property',
                    'value': common_data.InitQuality *
                    conversion_factors.Concentration,
                    'unitCode': STANDARD_UNITS['Concentration']
                },
                '@context': [
                    # 'https://schema.lab.fiware.org/ld/context',
                    'http://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.' +
                    'jsonld'
                ]
            }
            if common_data.SourceType is not None:
                data_model_dict['sourceCategory'] = {
                    'type': 'Property',
                    'value': 'xxx',
                    'sourceType': {
                        'type': 'Property',
                        'value': enu.SourceTypes(common_data.SourceType).name
                    },
                    'sourceQuality': {
                        'type': 'Property',
                        'value': common_data.SourceQuality *
                        conversion_factors.Concentration,
                        'unitCode': STANDARD_UNITS['Concentration']
                    }
                }
                if common_data.SourcePattern:
                    data_model_dict['sourceCategory']['sourcePattern'] = {
                        'type': 'Relationship',
                        'object': 'urn:ngsi-ld:Pattern:{}'.format(
                            common_data.SourcePatternName)
                    }
            data_all_components.append(data_model_dict)
    return data_all_components


def json_ld_junction(proj, transformer) -> json:

    data_all_components = []

    num_nodes = en.getcount(ph=proj, object=en.NODECOUNT)
    for node in range(num_nodes):
        index = node + 1
        node_type = en.getnodetype(ph=proj, index=index)
        if node_type == en.JUNCTION:
            common_data = _get_node_common_data(proj, index)
            pattern_index = int(en.getnodevalue(
                proj, index, en.PATTERN))
            if pattern_index > 0:
                pattern_name = en.getpatternid(proj, pattern_index)
            else:
                pattern_name = None
            flow_units = en.getflowunits(proj)
            conversion_factors = _get_unit_conversion_factors(flow_units)
            coordinates = transformer.transform(common_data.Position[0], common_data.Position[1])
            base_demand = en.getnodevalue(proj, index, en.BASEDEMAND)
            emitter = en.getnodevalue(proj, index, en.EMITTER)
            data_model_dict = {
                'id': 'urn:ngsi-ld:Junction:{}'.format(common_data.Name),
                'type': 'Junction',
                'location': {
                    'type': 'GeoProperty',
                    'value': {
                        'type': 'Point',
                        'coordinates': coordinates
                    }
                },
                'elevation': {
                    'type': 'Property',
                    'value': common_data.Elevation *
                    conversion_factors.Elevation,
                    'unitCode': STANDARD_UNITS['Elevation']
                },
                'demandCategory': {
                    'type': 'Property',
                    'value': 'xxx',
                    'baseDemand': {
                        'type': 'Property',
                        'value': base_demand * conversion_factors.Demand,
                        'unitCode': STANDARD_UNITS['Demand']
                    }
                },
                'initialQuality': {
                    'type': 'Property',
                    'value': common_data.InitQuality *
                    conversion_factors.Concentration,
                    'unitCode': STANDARD_UNITS['Concentration']
                },
                'emitterCoefficient': {
                    'type': 'Property',
                    'value': emitter * conversion_factors.EmitterCoeff,
                    'unitCode': STANDARD_UNITS['EmitterCoeff']
                },
                '@context': [
                    # 'https://schema.lab.fiware.org/ld/context',
                    'http://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.' +
                    'jsonld'
                ]
            }
            if pattern_name:
                data_model_dict['demandCategory']['demandPattern'] = {
                    'type': 'Relationship',
                    'object': 'urn:ngsi-ld:Pattern:{}'.format(
                        pattern_name)
                }
            if common_data.SourceType is not None:
                data_model_dict['sourceCategory'] = {
                    'type': 'Property',
                    'value': 'xxx',
                    'sourceType': {
                        'type': 'Property',
                        'value': enu.SourceTypes(common_data.SourceType).name
                    },
                    'sourceQuality': {
                        'type': 'Property',
                        'value': common_data.SourceQuality *
                        conversion_factors.Concentration,
                        'unitCode': STANDARD_UNITS['Concentration']
                    }
                }
                if common_data.SourcePatternName is not None:
                    data_model_dict['sourceCategory']['sourcePattern'] = {
                        'type': 'Relationship',
                        'object': 'urn:ngsi-ld:Pattern:{}'.format(
                            common_data.SourcePatternName)
                    }
            data_all_components.append(data_model_dict)
    return data_all_components


def json_ld_tank(proj, transformer) -> json:
    data_all_components = []
    num_nodes = en.getcount(ph=proj, object=en.NODECOUNT)
    for node in range(num_nodes):
        index = node + 1
        node_type = en.getnodetype(ph=proj, index=index)
        if node_type == en.TANK:
            common_data = _get_node_common_data(proj, index)
            flow_units = en.getflowunits(proj)
            conversion_factors = _get_unit_conversion_factors(flow_units)

            coordinates = transformer.transform(common_data.Position[0], common_data.Position[1])

            init_level = en.getnodevalue(proj, index, en.TANKLEVEL)
            min_level = en.getnodevalue(proj, index, en.MINLEVEL)
            max_level = en.getnodevalue(proj, index, en.MAXLEVEL)
            min_volume = en.getnodevalue(proj, index, en.MINVOLUME)
            diameter = en.getnodevalue(proj, index, en.TANKDIAM)
            mix_model = en.getnodevalue(proj, index, en.MIXMODEL)
            mix_fraction = en.getnodevalue(proj, index, en.MIXFRACTION)
            k_bulk = en.getnodevalue(proj, index, en.TANK_KBULK)
            volume_curve_index = int(en.getnodevalue(proj, index, en.VOLCURVE))
            if volume_curve_index > 0:
                volume_curve_name = en.getcurveid(proj, volume_curve_index)
            else:
                volume_curve_name = None
            data_model_dict = {
                'id': 'urn:ngsi-ld:Tank:{}'.format(common_data.Name),
                'type': 'Tank',
                'location': {
                    'type': 'GeoProperty',
                    'value': {
                        'type': 'Point',
                        'coordinates': coordinates
                    }
                },
                'elevation': {
                    'type': 'Property',
                    'value': common_data.Elevation *
                    conversion_factors.Elevation,
                    'unitCode': STANDARD_UNITS['Elevation']
                },
                'initLevel': {
                    'type': 'Property',
                    'value': init_level * conversion_factors.Head,
                    'unitCode': STANDARD_UNITS['Head']
                },
                "minLevel": {
                    "type": "Property",
                    "value": min_level * conversion_factors.Head,
                    "unitCode": STANDARD_UNITS['Head']
                },
                "maxLevel": {
                    "type": "Property",
                    "value": max_level * conversion_factors.Head,
                    "unitCode": STANDARD_UNITS['Head']
                },
                "minVolume": {
                    "type": "Property",
                    "value": min_volume * conversion_factors.Volume,
                    "unitCode": STANDARD_UNITS['Volume']
                },
                "nominalDiameter": {
                    "type": "Property",
                    "value": diameter * conversion_factors.DiameterTanks,
                    "unitCode": STANDARD_UNITS['DiameterTanks']
                },
                'initialQuality': {
                    'type': 'Property',
                    'value': common_data.InitQuality *
                    conversion_factors.Concentration,
                    'unitCode': STANDARD_UNITS['Concentration']
                },
                'mixingModel': {
                    'type': 'Property',
                    'value': MIXING_MODELS[mix_model]
                },
                'mixingFraction': {
                    'type': 'Property',
                    'value': mix_fraction,
                    'unitCode': 'C62'
                },
                'bulkReactionCoefficient': {
                    'type': 'Property',
                    'value': k_bulk * conversion_factors.ReactionCoeffBulk,
                    'unitCode': STANDARD_UNITS['ReactionCoeffBulk']
                },
                '@context': [
                    # 'https://schema.lab.fiware.org/ld/context',
                    'http://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.' +
                    'jsonld'
                ]
            }
            if volume_curve_index != 0:
                data_model_dict['volumeCurve'] = {
                    'type': 'Relationship',
                    'object': 'urn:ngsi-ld:Curve:{}'.format(volume_curve_name)
                }
            if common_data.SourceType is not None:
                data_model_dict['sourceCategory'] = {
                    'type': 'Property',
                    'value': 'xxx',
                    'sourceType': {
                        'type': 'Property',
                        'value': enu.SourceTypes(common_data.SourceType).name
                    },
                    'sourceQuality': {
                        'type': 'Property',
                        'value': common_data.SourceQuality *
                        conversion_factors.Concentration,
                        'unitCode': STANDARD_UNITS['Concentration']
                    }
                }
                if common_data.SourcePatternName is not None:
                    data_model_dict['sourceCategory']['sourcePattern'] = {
                        'type': 'Relationship',
                        'object': 'urn:ngsi-ld:Pattern:{}'.format(
                            common_data.SourcePatternName)
                    }
            data_all_components.append(data_model_dict)
    return data_all_components


def _get_link_common_data(
        proj, index: int) -> LinkCommonData:
    link_node_indices = en.getlinknodes(proj, index)
    return LinkCommonData(
        Name=en.getlinkid(proj, index),
        StartNodeIndex=link_node_indices[0],
        EndNodeIndex=link_node_indices[1],
        StartNodeID=en.getnodeid(proj, link_node_indices[0]),
        EndNodeID=en.getnodeid(proj, link_node_indices[1]),
        StartNodeType=en.getnodetype(proj, link_node_indices[0]),
        EndNodeType=en.getnodetype(proj, link_node_indices[1]),
        InitStatus=en.getlinkvalue(proj, index, en.INITSTATUS),
        KBulk=en.getlinkvalue(proj, index, en.KBULK),
        KWall=en.getlinkvalue(proj, index, en.KWALL),
        LinkType=en.getlinktype(proj, index),
        Vertices=_get_link_vertices(proj, index)
    )


def json_ld_pipe(proj, transformer) -> json:
    
    data_all_components = []
    num_links = en.getcount(ph=proj, object=en.LINKCOUNT)
    for link in range(num_links):
        index = link + 1
        link_type = en.getlinktype(ph=proj, index=index)
        if link_type in [en.PIPE, en.CVPIPE]:
            common_data = _get_link_common_data(proj, index)
            flow_units = en.getflowunits(proj)
            conversion_factors = _get_unit_conversion_factors(flow_units)
            if common_data.LinkType == 0:
                init_status = 2
            else:
                init_status = common_data.InitStatus
            headloss_type = en.getoption(proj, en.HEADLOSSFORM)
            if headloss_type == 1:
                roughness_conversion = conversion_factors.RoughnessCoeffDW
                roughness_units = STANDARD_UNITS['RoughnessCoeffDW']
            else:
                roughness_conversion = conversion_factors.RoughnessCoeffOther
                roughness_units = STANDARD_UNITS['RoughnessCoeffOther']
            wall_order = en.getoption(proj, en.WALLORDER)
            if wall_order == 0:
                wall_coeff_conversion = \
                    conversion_factors.ReactionCoeffWall0Order
                wall_coeff_units = STANDARD_UNITS['ReactionCoeffWall0Order']
            else:
                wall_coeff_conversion = \
                    conversion_factors.ReactionCoeffWall1Order
                wall_coeff_units = STANDARD_UNITS['ReactionCoeffWall1Order']
            length = en.getlinkvalue(proj, index, en.LENGTH)
            diameter = en.getlinkvalue(proj, index, en.DIAMETER)
            roughness = en.getlinkvalue(proj, index, en.ROUGHNESS)
            minor_loss_coeff = en.getlinkvalue(proj, index, en.MINORLOSS)
            data_model_dict = {
                'id': 'urn:ngsi-ld:Pipe:{}'.format(common_data.Name),
                'type': 'Pipe',
                'initialStatus': {
                    'type': 'Property',
                    'value': STATUSES[init_status]
                    },
                'length': {
                    'type': 'Property',
                    'value': length * conversion_factors.Length,
                    'unitCode': STANDARD_UNITS['Length']
                    },
                'diameter': {
                    'type': 'Property',
                    'value': diameter * conversion_factors.DiameterPipes,
                    'unitCode': STANDARD_UNITS['DiameterPipes']
                    },
                'wallCoeff': {
                    'type': 'Property',
                    'value': common_data.KWall * wall_coeff_conversion,
                    'unitCode': wall_coeff_units
                    },
                'bulkCoeff': {
                    'type': 'Property',
                    'value': common_data.KBulk *
                    conversion_factors.ReactionCoeffBulk,
                    'unitCode': STANDARD_UNITS['ReactionCoeffBulk']
                    },
                'roughness': {
                    'type': 'Property',
                    'value': roughness * roughness_conversion,
                    'unitCode': roughness_units
                    },
                'minorLoss': {
                    'type': 'Property',
                    'value': minor_loss_coeff *
                    conversion_factors.MinorLossCoeff,
                    'unitCode': STANDARD_UNITS['MinorLossCoeff']
                    },
                'startsAt': {
                    'type': 'Relationship',
                    'object': 'urn:ngsi-ld:{}:{}'.format(
                        NodeTypes(common_data.StartNodeType).name,
                        common_data.StartNodeID),
                    },
                'endsAt': {
                    'type': 'Relationship',
                    'object': 'urn:ngsi-ld:{}:{}'.format(
                        NodeTypes(common_data.EndNodeType).name,
                        common_data.EndNodeID),
                    },
                '@context': [
                    'https://schema.lab.fiware.org/ld/context'
                ]
            }
            if common_data.Vertices:
                data_model_dict['vertices'] = _vertices_to_geoproperty(transformer, common_data.Vertices)
            data_all_components.append(data_model_dict)
    return data_all_components

def _vertices_to_geoproperty(transformer, input_vertices):
    data = {}

    data['type'] = 'GeoProperty'
    data['value'] = {}
    data['value']['type'] = 'Point'
    data['value']['coordinates'] = []

    if len(input_vertices) > 1:
        data['value']['type'] = 'LineString'
        for coordinates in input_vertices:
            result = transformer.transform(coordinates[0], coordinates[1])
            data['value']['coordinates'].append([result[0], result[1]])
    else:
        data['value']['type'] = 'Point'
        result = transformer.transform(input_vertices[0][0], input_vertices[0][1])
        data['value']['coordinates'].append(result[0])
        data['value']['coordinates'].append(result[1])

    return data

def json_ld_pump(proj, transformer) -> json:
    data_all_components = []
    num_links = en.getcount(ph=proj, object=en.LINKCOUNT)
    for link in range(num_links):
        index = link + 1
        link_type = en.getlinktype(ph=proj, index=index)
        if link_type == en.PUMP:
            common_data = _get_link_common_data(proj, index)
            flow_units = en.getflowunits(proj)
            conversion_factors = _get_unit_conversion_factors(flow_units)
            pattern_index = int(en.getlinkvalue(proj, index, en.LINKPATTERN))
            if pattern_index > 0:
                pattern_name = en.getpatternid(proj, pattern_index)
            else:
                pattern_name = None
            h_curve_index = int(en.getlinkvalue(proj, index, en.PUMP_HCURVE))
            if h_curve_index > 0:
                h_curve_name = en.getcurveid(proj, h_curve_index)
            else:
                h_curve_name = None
            e_curve_index = int(en.getlinkvalue(proj, index, en.PUMP_ECURVE))
            if e_curve_index > 0:
                e_curve_name = en.getcurveid(proj, e_curve_index)
            else:
                e_curve_name = None
            e_pattern_index = int(en.getlinkvalue(proj, index, en.PUMP_EPAT))
            if e_pattern_index > 0:
                e_pattern_name = en.getpatternid(proj, e_pattern_index)
            else:
                e_pattern_name = None
            init_setting = en.getlinkvalue(proj, index, en.INITSETTING)
            e_cost = en.getlinkvalue(proj, index, en.PUMP_ECOST)
            power_rating = en.getlinkvalue(proj, index, en.PUMP_POWER)
            data_model_dict = {
                'id': 'urn:ngsi-ld:Pump:{}'.format(common_data.Name),
                'type': 'Pump',
                'initialStatus': {
                    'type': 'Property',
                    'value': STATUSES[common_data.InitStatus]
                    },
                'speed': {
                    'type': 'Property',
                    'value': init_setting,
                    'unitCode': 'C62'
                    },
                'startsAt': {
                    'type': 'Relationship',
                    'object': 'urn:ngsi-ld:{}:{}'.format(
                        NodeTypes(common_data.StartNodeType).name,
                        common_data.StartNodeID)
                    },
                'endsAt': {
                    'type': 'Relationship',
                    'object': 'urn:ngsi-ld:{}:{}'.format(
                        NodeTypes(common_data.EndNodeType).name,
                        common_data.EndNodeID)
                    },
                'energyPrice': {
                    'type': 'Property',
                    'value': e_cost,
                    'unitCode': 'C62'
                    },
                '@context': [
                    'https://schema.lab.fiware.org/ld/context'
                ]
            }
            if power_rating > 0:
                data_model_dict['power'] = {
                    'type': 'Property',
                    'value': power_rating * conversion_factors.Power,
                    'unitCode': STANDARD_UNITS['Power']
                }
            if pattern_name:
                data_model_dict['pumpPattern'] = {
                    'type': 'Relationship',
                    'object': 'urn:ngsi-ld:Pattern:{}'.format(pattern_name)
                }
            if h_curve_name:
                data_model_dict['pumpCurve'] = {
                    'type': 'Relationship',
                    'object': 'urn:ngsi-ld:Curve:{}'.format(h_curve_name)
                }
            if e_curve_name:
                data_model_dict['efficCurve'] = {
                    'type': 'Relationship',
                    'object': 'urn:ngsi-ld:Curve:{}'.format(e_curve_name)
                }
            if e_pattern_name:
                data_model_dict['energyPattern'] = {
                    'type': 'Relationship',
                    'object': 'urn:ngsi-ld:Pattern:{}'.format(e_pattern_name)
                }
            if common_data.Vertices:
                data_model_dict['vertices'] = _vertices_to_geoproperty(transformer, common_data.Vertices)
            data_all_components.append(data_model_dict)
    return data_all_components


def json_ld_valve(proj, transformer) -> json:
    
    data_all_components = []
    num_links = en.getcount(ph=proj, object=en.LINKCOUNT)
    for link in range(num_links):
        index = link + 1
        link_type = en.getlinktype(ph=proj, index=index)
        if link_type == en.GPV:
            raise RuntimeError(
                'Error: Input file contains a general purpose valve (GPV).'
                ' GPVs cannot be handled as EPANET lacks the functionality '
                'to assign a curve to a valve programatically. ')
        if link_type >= en.PRV:
            common_data = _get_link_common_data(proj, index)
            flow_units = en.getflowunits(proj)
            conversion_factors = _get_unit_conversion_factors(flow_units)
            diameter = en.getlinkvalue(proj, index, en.DIAMETER)
            minor_loss_coeff = en.getlinkvalue(proj, index, en.MINORLOSS)
            init_setting = en.getlinkvalue(proj, index, en.INITSETTING)
            if link_type <= en.PBV:
                setting_value = init_setting * conversion_factors.Pressure
                setting_units = STANDARD_UNITS['Pressure']
            elif link_type == en.FCV:
                setting_value = init_setting * conversion_factors.Flow
                setting_units = STANDARD_UNITS['Flow']
            else:
                setting_value = init_setting
                setting_units = 'C62'
            data_model_dict = {
                'id': 'urn:ngsi-ld:Valve:{}'.format(common_data.Name),
                'type': 'Valve',
                'initialStatus': {
                    'type': 'Property',
                    'value': STATUSES[common_data.InitStatus]
                    },
                'diameter': {
                    'type': 'Property',
                    'value': diameter * conversion_factors.DiameterPipes,
                    'unitCode': STANDARD_UNITS['DiameterPipes']
                    },
                'valveType': {
                    'type': 'Property',
                    'value': VALVE_TYPES[link_type]
                    },
                'setting': {
                    'type': 'Property',
                    'value': setting_value,
                    'unitCode': setting_units
                    },
                'minorLoss': {
                    'type': 'Property',
                    'value': minor_loss_coeff *
                    conversion_factors.MinorLossCoeff,
                    'unitCode': STANDARD_UNITS['MinorLossCoeff']
                    },
                'startsAt': {
                    'type': 'Relationship',
                    'object': 'urn:ngsi-ld:{}:{}'.format(
                        NodeTypes(common_data.StartNodeType).name,
                        common_data.StartNodeID),
                    },
                'endsAt': {
                    'type': 'Relationship',
                    'object': 'urn:ngsi-ld:{}:{}'.format(
                        NodeTypes(common_data.EndNodeType).name,
                        common_data.EndNodeID),
                    },
                '@context': [
                    'https://schema.lab.fiware.org/ld/context'
                ]
            }
            if link_type == 8:
                data_model_dict['valveCurve'] = {
                    'type': 'Relationship',
                    'object': 'urn:ngsi-ld:Curve:{}'.format(setting_value)
                }
            if common_data.Vertices:
                data_model_dict['vertices'] = _vertices_to_geoproperty(transformer, common_data.Vertices)

            data_all_components.append(data_model_dict)
    return data_all_components


def _get_link_vertices(proj, link_index: int):
    num_vertices = en.getvertexcount(proj, link_index)
    if num_vertices == 0:
        return None
    vertices = [en.getvertex(proj, link_index, vertex)
                for vertex in range(1, num_vertices + 1)]
    return vertices
