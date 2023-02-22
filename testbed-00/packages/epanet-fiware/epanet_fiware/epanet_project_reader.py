from typing import NamedTuple, List, Union
import math
import epanet.toolkit as en

import epanet_fiware.enumerations as enu


Count = NamedTuple('Count', [
    ('Nodes', int),
    ('Links', int),
    ('Patterns', int),
    ('Curves', int),
    ('Controls', int),
    ('Rules', int)
])


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
    ('VerticesX', Union[int, List[float]]),
    ('VerticesY', Union[int, List[float]]),
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


def get_node_position(proj, node_id: str, prop: None):
    node_index = en.getnodeindex(ph=proj, id=node_id)
    try:
        position = en.getcoord(ph=proj, index=node_index)
    except Exception:
        position = [0, 0]
    return position


def get_name(proj, node_or_link_id: sorted, prop: None):
    return node_or_link_id


def get_link_curve_name(proj, link_id: str, prop: int):
    curve_index = get_link_value(proj, link_id, prop)
    if curve_index in [0, None]:
        return None
    return en.getcurveid(ph=proj, index=int(curve_index))


def get_node_curve_name(proj, node_id: str, prop: int):
    curve_index = get_node_value(proj, node_id, prop)
    if curve_index in [0, None]:
        return None
    return en.getcurveid(ph=proj, index=int(curve_index))


def get_link_patten_name(proj, link_id: str, prop: int):
    pattern_index = get_link_value(proj, link_id, prop)
    if pattern_index in [0, None]:
        return None
    return en.getpatternid(ph=proj, index=int(pattern_index))


def get_node_patten_name(proj, node_id: str, prop: int):
    pattern_index = get_node_value(proj, node_id, prop)
    if pattern_index in [0, None]:
        return None
    return en.getpatternid(ph=proj, index=int(pattern_index))


def get_link_node_id(proj, link_id: str, location: int):
    link_index = en.getlinkindex(ph=proj, id=link_id)
    link_node_indices = en.getlinknodes(ph=proj, index=link_index)
    return en.getnodeid(proj, link_node_indices[location])


def get_link_vertices(proj, link_id: str, axis: int):
    link_index = en.getlinkindex(ph=proj, id=link_id)
    num_vertices = en.getvertexcount(proj, link_index)
    if num_vertices == 0:
        return None
    return [en.getvertex(proj, link_index, vertex)[axis]
            for vertex in range(1, num_vertices + 1)]


def get_link_type(proj, link_id: str, prop: int):
    link_index = en.getlinkindex(ph=proj, id=link_id)
    return en.getlinktype(ph=proj, index=link_index)


def get_node_type(proj, node_id: str, prop: int):
    node_index = en.getnodeindex(ph=proj, id=node_id)
    return en.getnodetype(ph=proj, index=node_index)


def get_link_value(proj, link_id: str, prop: int):
    link_index = en.getlinkindex(ph=proj, id=link_id)
    return en.getlinkvalue(ph=proj, index=link_index, property=prop)


def get_qual_info(proj, info: enu.QualityInfo):
    info = en.getqualinfo(ph=proj)
    return enu.QualityInfo(
        QualType=info[0],
        ChemName=info[1],
        ChemUnits=info[2],
        TraceNode=info[3])


def get_init_level(proj, node_id: str, prop: int):
    tank_index = en.getnodeindex(ph=proj, id=node_id)
    diameter = en.getnodevalue(
        ph=proj, index=tank_index, property=en.TANKDIAM)
    init_volume = en.getnodevalue(
        ph=proj, index=tank_index, property=en.INITVOLUME)
    vol_curve_index = en.getnodevalue(
        ph=proj, index=tank_index, property=en.VOLCURVE)
    if vol_curve_index not in [0, None]:
        raise RuntimeError(
            'ERROR: Tank init level cannot be retrieved')
    area = math.pi * (diameter / 2) ** 2
    init_level = init_volume / area
    return init_level


def get_node_value(proj, node_id: str, prop: int):
    node_index = en.getnodeindex(ph=proj, id=node_id)
    try:
        return en.getnodevalue(ph=proj, index=node_index, property=prop)
    except Exception:
        return None


def get_component_count(epanet_proj) -> Count:
    num_nodes = en.getcount(ph=epanet_proj, object=en.NODECOUNT)
    num_links = en.getcount(ph=epanet_proj, object=en.LINKCOUNT)
    num_patterns = en.getcount(ph=epanet_proj, object=en.PATCOUNT)
    num_curves = en.getcount(ph=epanet_proj, object=en.CURVECOUNT)
    num_controls = en.getcount(ph=epanet_proj, object=en.CONTROLCOUNT)
    num_rules = en.getcount(ph=epanet_proj, object=en.RULECOUNT)
    return Count(num_nodes, num_links, num_patterns,
                 num_curves, num_controls, num_rules)
