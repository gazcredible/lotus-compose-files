from typing import Union, Optional
import math
import numpy as np
from datetime import datetime, timedelta
import epanet.toolkit as en

import epanet_fiware.fiware_connection as fc
from epanet_fiware.enumerations import LinkTypes, SourceTypes
import epanet_fiware.ngsi_ld_writer as nlw


def _volume(diameter: float, level: float,
            volume_curve: Optional[np.array] = None):
    # Need to update to use volume curve if provided
    radius = diameter / 2
    area = math.pi * radius**2
    return area * level


def _init_volume(tank_ngsi_ld: list) -> float:
    # Need to update to use volume curve if provided
    diameter = tank_ngsi_ld['nominalDiameter']['value']
    init_level = tank_ngsi_ld['initLevel']['value']
    return _volume(diameter, init_level)


def _name_from_id(entity_id: list) -> str:
    return entity_id.split(':')[3]


def _type_from_id(entity_id: list) -> str:
    return entity_id.split(':')[2]


def _pipe_type_from_entity(pipe_ngsi_ld: list) -> list:
    init_status = pipe_ngsi_ld['initialStatus']['value']
    if init_status == 'CV':
        return [0, 'CheckValvePipe']
    return [1, 'Pipe']


def _link_status_from_entity(link_ngsi_ld: list) -> list:
    status_ngsi_ld = link_ngsi_ld['initialStatus']['value']
    statuses_ngsi_ld_rev = {v: k for k, v in nlw.STATUSES.items()}
    status_index = statuses_ngsi_ld_rev[status_ngsi_ld]
    return status_index


def _valve_type_from_entity(valve_ngsi_ld: list) -> list:
    type_ngsi_ld = valve_ngsi_ld['valveType']['value']
    types_ngsi_ld_rev = {v: k for k, v in nlw.VALVE_TYPES.items()}
    type_index = types_ngsi_ld_rev[type_ngsi_ld]
    type_name = LinkTypes(type_index).name
    return [type_index, type_name]


def _source_type_from_entity(node_ngsi_ld: list) -> Union[int, None]:
    type_ngsi_ld = _value_if_exists(
            node_ngsi_ld, 'sourceType', 'sourceCategory')
    if type_ngsi_ld:
        return getattr(SourceTypes, type_ngsi_ld).value
    else:
        return type_ngsi_ld


def _mix_model_from_entity(tank_ngsi_ld: list) -> int:
    model_ngsi_ld = tank_ngsi_ld['mixingModel']['value']
    models_ngsi_ld_rev = {v: k for k, v in nlw.MIXING_MODELS.items()}
    model_index = models_ngsi_ld_rev[model_ngsi_ld]
    return model_index


def _object_name_if_exists(
        entity: dict, name: str, category: Union[None, str] = None
        ) -> Union[None, 'str']:
    if category and category in entity:
        data = entity[category]
    else:
        data = entity
    if name in data:
        object_id = data[name]['object']
        return _name_from_id(object_id)
    return None


def _value_if_exists(
        entity: dict, name: str, category: Union[None, str] = None
        ) -> Union[None, 'str']:
    if category and (category in entity):
        data = entity[category]
    else:
        data = entity
    if name in data:
        return data[name]['value']
    return None


def _headloss_type_from_pipe(pipe_ngsi_ld: dict) -> int:
    roughness_units = pipe_ngsi_ld['roughness']['unitCode']
    if roughness_units == 'MMT':
        return en.DW    # EN_DW (Darcy-Weisbach)
    else:
        # Could be 0 (EN_HW) or 2 (EN_CM), but can't distinguish
        return en.HW    # EN_HW (Hazen-Williams)


def _wall_order_from_pipe(pipe_ngsi_ld: dict) -> int:
    wall_coeff_units = pipe_ngsi_ld['wallCoeff']['unitCode']
    if wall_coeff_units == 'RRC':
        return 0
    else:
        return 1


def project_from_fiware(network_name: str,
                        rpt_file: str,
                        out_file: str,
                        gateway_server: str,
                        client_id: Optional[str] = None,
                        client_secret: Optional[str] = None,
                        auth_url: Optional[str] = None):
    print('Reading NGSI-LD network data from FIWARE')
    access_token = fc.get_access_token(client_id, client_secret, auth_url)
    ngsi_ld_data = {}

    ngsi_ld_data['Patterns'] = fc.retrieve_entities(
        access_token, 'Pattern', gateway_server, network_name)
    ngsi_ld_data['Curves'] = fc.retrieve_entities(
        access_token, 'Curve', gateway_server, network_name)
    ngsi_ld_data['Pipes'] = fc.retrieve_entities(
        access_token, 'Pipe', gateway_server, network_name)
    ngsi_ld_data['Pumps'] = fc.retrieve_entities(
        access_token, 'Pump', gateway_server, network_name)
    ngsi_ld_data['Valves'] = fc.retrieve_entities(
        access_token, 'Valve', gateway_server, network_name)
    ngsi_ld_data['Reservoirs'] = fc.retrieve_entities(
        access_token, 'Reservoir', gateway_server, network_name)
    ngsi_ld_data['Tanks'] = fc.retrieve_entities(
        access_token, 'Tank', gateway_server, network_name)
    ngsi_ld_data['Junctions'] = fc.retrieve_entities(
        access_token, 'Junction', gateway_server, network_name)

    print('Generating EPANET project from NGSI-LD data')
    units_type = en.CMD  # All flows converted to EN_CMD (Cubic meters per day)
    head_loss_type = _headloss_type_from_pipe(ngsi_ld_data['Pipes'][0])
    proj = en.createproject()
    en.init(ph=proj,
            rptFile=rpt_file, outFile='',
            unitsType=units_type, headLossType=head_loss_type)
    en.setqualtype(ph=proj,
                   qualType=en.CHEM,
                   chemName='chemical',
                   chemUnits='chemical units',
                   traceNode='')  # Default to a 'chemical' quality analysis
    en.setoption(ph=proj,
                 option=en.WALLORDER,
                 value=_wall_order_from_pipe(ngsi_ld_data['Pipes'][0]))
    for component_type in ['Patterns', 'Curves', 'Junctions', 'Reservoirs',
                           'Tanks', 'Pipes', 'Pumps', 'Valves']:
        proj = _generate_components(proj, component_type, ngsi_ld_data)
    return proj


def _generate_components(proj, component_type: str, ngsi_ld_data: dict):
    method_names = {
        # 'Times': '_set_times',
        # 'Options': '_set_options',
        'Junctions': '_generate_junctions',
        'Reservoirs': '_generate_reservoirs',
        'Tanks': '_generate_tanks',
        'Pipes': '_generate_pipes',
        'Pumps': '_generate_pumps',
        'Valves': '_generate_valves',
        'Patterns': '_generate_patterns',
        'Curves': '_generate_curves'
    }
    method_name = method_names.get(component_type)
    if method_name:
        method = globals()[method_name]
        proj = method(proj, ngsi_ld_data[component_type])
    return proj


def _generate_patterns(proj, ngsi_ld_data: dict):
    for pattern in ngsi_ld_data:
        name = _name_from_id(pattern['id'])
        values = pattern['multipliers']['value']
        length = len(values)
        pattern_step = pattern['timeStep']['value']
        en.addpattern(ph=proj, id=name)
        index = en.getpatternindex(ph=proj, id=name)
        try:
            start_time_str = pattern['startTime']['value']
        except KeyError:
            start_time_str = pattern[
                'https://uri.fiware.org/ns/data-models#startTime']['value']
        start_time_datetime = datetime.strptime(start_time_str, '%H:%M:%S')
        start_time_sec = timedelta(
            hours=start_time_datetime.hour,
            minutes=start_time_datetime.minute,
            seconds=start_time_datetime.second
        ).total_seconds()
        en.setpattern(
            ph=proj,
            index=index,
            values=make_array(values),
            len=length
        )
        en.settimeparam(proj, en.PATTERNSTEP, pattern_step)
        en.settimeparam(proj, en.PATTERNSTART, int(start_time_sec))
    return proj


def _generate_curves(proj, ngsi_ld_data: dict):
    for curve in ngsi_ld_data:
        name = _name_from_id(curve['id'])
        x_values = curve['xData']['value']
        y_values = curve['yData']['value']
        try:
            length = len(x_values)
        except TypeError:
            x_values = [x_values]
            y_values = [y_values]
            length = len(x_values)
        en.addcurve(ph=proj, id=name)
        index = en.getcurveindex(ph=proj, id=name)
        en.setcurve(
            ph=proj,
            index=index,
            xValues=make_array(x_values),
            yValues=make_array(y_values),
            nPoints=length
        )
    return proj


def _set_source(proj, source_pattern_name: Union[str, None], node_index: int,
                source_quality: Union[float, None],
                source_type: Union[float, None]):
    if source_pattern_name:
        index_source_pattern = en.getpatternindex(
            ph=proj,
            id=source_pattern_name
        )
        en.setnodevalue(
            ph=proj,
            index=node_index,
            property=en.SOURCEPAT,
            value=index_source_pattern
        )
    if source_quality is not None:
        en.setnodevalue(
            ph=proj,
            index=node_index,
            property=en.SOURCEQUAL,
            value=source_quality
        )
    if source_type is not None:
        en.setnodevalue(
            ph=proj,
            index=node_index,
            property=en.SOURCETYPE,
            value=source_type
        )
    return proj


def _generate_junctions(proj, ngsi_ld_data: dict):
    for junction in ngsi_ld_data:
        name = _name_from_id(junction['id'])
        en.addnode(ph=proj, id=name, nodeType=en.JUNCTION)
        index = en.getnodeindex(ph=proj, id=name)
        en.setnodevalue(
            ph=proj,
            index=index,
            property=en.INITQUAL,
            value=junction['initialQuality']['value']
        )
        position = junction['location']['value']['coordinates']
        en.setcoord(
            ph=proj,
            index=index,
            x=position[0],
            y=position[1]
        )
        demand_pattern_name = _object_name_if_exists(
            junction, 'demandPattern', 'demandCategory')
        if demand_pattern_name:
            pattern_id = demand_pattern_name
        else:
            pattern_id = ''
        en.setjuncdata(
            ph=proj,
            index=index,
            elev=junction['elevation']['value'],
            dmnd=junction['demandCategory']['baseDemand']['value'],
            dmndpat=pattern_id
        )
        en.setnodevalue(
            ph=proj,
            index=index,
            property=en.EMITTER,
            value=junction['emitterCoefficient']['value']
        )
        source_quality = _value_if_exists(
            junction, 'sourceQuality', 'sourceCategory')
        source_pattern_name = _object_name_if_exists(
            junction, 'sourcePattern', 'sourceCategory')
        source_type = _source_type_from_entity(junction)
        proj = _set_source(proj, source_pattern_name, index,
                           source_quality, source_type)
    return proj


def _generate_reservoirs(proj, ngsi_ld_data: dict):
    for reservoir in ngsi_ld_data:
        name = _name_from_id(reservoir['id'])
        en.addnode(ph=proj, id=name, nodeType=en.RESERVOIR)
        index = en.getnodeindex(ph=proj, id=name)
        en.setnodevalue(
            ph=proj,
            index=index,
            property=en.INITQUAL,
            value=reservoir['initialQuality']['value']
        )
        position = reservoir['location']['value']['coordinates']
        en.setcoord(
            ph=proj,
            index=index,
            x=position[0],
            y=position[1]
        )
        en.setnodevalue(
            ph=proj,
            index=index,
            property=en.ELEVATION,
            value=reservoir['reservoirHead']['value']
        )
        # Head pattern not extracted from .inp file or included in data model
        source_quality = _value_if_exists(
            reservoir, 'sourceQuality', 'sourceCategory')
        source_pattern_name = _object_name_if_exists(
            reservoir, 'sourcePattern', 'sourceCategory')
        source_type = _source_type_from_entity(reservoir)
        proj = _set_source(proj, source_pattern_name, index,
                           source_quality, source_type)
    return proj


def _generate_tanks(proj, ngsi_ld_data: dict):
    for tank in ngsi_ld_data:
        name = _name_from_id(tank['id'])
        en.addnode(ph=proj, id=name, nodeType=en.TANK)
        index = en.getnodeindex(ph=proj, id=name)
        en.setnodevalue(
            ph=proj,
            index=index,
            property=en.INITQUAL,
            value=tank['initialQuality']['value']
        )
        position = tank['location']['value']['coordinates']
        en.setcoord(
            ph=proj,
            index=index,
            x=position[0],
            y=position[1]
        )
        volume_curve_name = _object_name_if_exists(tank, 'volumeCurve')
        if volume_curve_name is None:
            volume_curve_name = ''
        en.settankdata(
            ph=proj,
            index=index,
            elev=tank['elevation']['value'],
            initlvl=tank['initLevel']['value'],
            minlvl=tank['minLevel']['value'],
            maxlvl=tank['maxLevel']['value'],
            diam=tank['nominalDiameter']['value'],
            minvol=tank['minVolume']['value'],
            volcurve=volume_curve_name
        )
        # EPANET source code does not deal with elevation and levels correctly
        # in settankdata, so set again with setnodevalue.
        en.setnodevalue(
            ph=proj,
            index=index,
            property=en.ELEVATION,
            value=tank['elevation']['value']
        )
        en.setnodevalue(
            ph=proj,
            index=index,
            property=en.MINLEVEL,
            value=tank['minLevel']['value']
        )
        en.setnodevalue(
            ph=proj,
            index=index,
            property=en.MAXLEVEL,
            value=tank['maxLevel']['value']
        )
        mix_fraction = tank['mixingFraction']['value']
        if mix_fraction is not None:
            en.setnodevalue(
                ph=proj,
                index=index,
                property=en.MIXFRACTION,
                value=mix_fraction
            )
        else:
            en.setnodevalue(
                ph=proj,
                index=index,
                property=en.MIXFRACTION,
                value=1
            )
        en.setnodevalue(
                ph=proj,
                index=index,
                property=en.TANK_KBULK,
                value=tank['bulkReactionCoefficient']['value']
            )
        en.setnodevalue(
                ph=proj,
                index=index,
                property=en.MIXMODEL,
                value=_mix_model_from_entity(tank)
            )
        source_quality = _value_if_exists(
            tank, 'sourceQuality', 'sourceCategory')
        source_pattern_name = _object_name_if_exists(
            tank, 'sourcePattern', 'sourceCategory')
        source_type = _source_type_from_entity(tank)
        proj = _set_source(proj, source_pattern_name, index,
                           source_quality, source_type)
    return proj


def _generate_pipes(proj, ngsi_ld_data: dict):
    for pipe in ngsi_ld_data:
        name = _name_from_id(pipe['id'])
        link_type = _pipe_type_from_entity(pipe)[0]
        en.addlink(
            ph=proj,
            id=name,
            linkType=link_type,
            fromNode=_name_from_id(pipe['startsAt']['object']),
            toNode=_name_from_id(pipe['endsAt']['object'])
        )
        index = en.getlinkindex(proj, name)
        en.setlinkvalue(
            ph=proj,
            index=index,
            property=en.KBULK,
            value=pipe['bulkCoeff']['value']
        )
        en.setlinkvalue(
            ph=proj,
            index=index,
            property=en.KWALL,
            value=pipe['wallCoeff']['value']
        )
        try:
            length = pipe['length']['value']
        except KeyError:
            length = pipe[
                'https://uri.fiware.org/ns/data-models#length']['value']
        en.setpipedata(
            ph=proj,
            index=index,
            length=length,
            diam=pipe['diameter']['value'],
            rough=pipe['roughness']['value'],
            mloss=pipe['minorLoss']['value']
        )
        # Set initial status if not a check valve pipe
        if link_type == 1:
            en.setlinkvalue(
                ph=proj,
                index=index,
                property=en.INITSTATUS,
                value=_link_status_from_entity(pipe)
            )
        if _value_if_exists(pipe, 'vertices'):
            vertices_data = _value_if_exists(pipe, 'vertices')
            if vertices_data['type'] == 'Point':
                vertices_x = [vertices_data['coordinates'][0]]
                vertices_y = [vertices_data['coordinates'][1]]
                count = 1
            else:
                vertices_x = [coordinates[0] for coordinates in
                              vertices_data['coordinates']]
                vertices_y = [coordinates[1] for coordinates in
                              vertices_data['coordinates']]
                count = len(vertices_data['coordinates'])
            print('Setting vertices_x={}, vertices_y={}, count={}'.format(
                vertices_x, vertices_y, count))
            en.setvertices(
                ph=proj,
                index=index,
                x=make_array(vertices_x),
                y=make_array(vertices_y),
                count=count
            )
    return proj


def _generate_pumps(proj, ngsi_ld_data: dict):
    for pump in ngsi_ld_data:
        name = _name_from_id(pump['id'])
        en.addlink(
            ph=proj,
            id=name,
            linkType=en.PUMP,
            fromNode=_name_from_id(pump['startsAt']['object']),
            toNode=_name_from_id(pump['endsAt']['object'])
        )
        index = en.getlinkindex(proj, name)
        en.setlinkvalue(
            ph=proj,
            index=index,
            property=en.INITSTATUS,
            value=_link_status_from_entity(pump)
        )
        try:
            speed = pump['speed']['value']
        except KeyError:
            speed = pump[
                'https://uri.fiware.org/ns/data-models#speed']['value']
        en.setlinkvalue(
            ph=proj,
            index=index,
            property=en.INITSETTING,
            value=speed
        )
        h_curve_name = _object_name_if_exists(pump, 'pumpCurve')
        if h_curve_name:
            index_h_curve = en.getcurveindex(
                ph=proj,
                id=h_curve_name)
            en.setheadcurveindex(
                ph=proj,
                linkIndex=index,
                curveIndex=index_h_curve
            )
        else:
            en.setlinkvalue(
                ph=proj,
                index=index,
                property=en.PUMP_POWER,
                value=_value_if_exists(pump, 'power')
            )
        e_curve_name = _object_name_if_exists(pump, 'efficCurve')
        if e_curve_name:
            index_e_curve = en.getcurveindex(
                ph=proj,
                id=e_curve_name)
            en.setlinkvalue(
                ph=proj,
                index=index,
                property=en.PUMP_ECURVE,
                value=index_e_curve
            )
        e_cost = pump['energyPrice']['value']
        if e_cost:
            en.setlinkvalue(
                ph=proj,
                index=index,
                property=en.PUMP_ECOST,
                value=e_cost
            )
        e_pattern_name = _object_name_if_exists(pump, 'energyPattern')
        if e_pattern_name:
            index_e_pattern = en.getpatternindex(
                ph=proj,
                id=e_pattern_name)
            en.setlinkvalue(
                ph=proj,
                index=index,
                property=en.PUMP_EPAT,
                value=index_e_pattern
            )
        if _value_if_exists(pump, 'vertices'):
            vertices_data = _value_if_exists(pump, 'vertices')
            if vertices_data['type'] == 'Point':
                vertices_x = [vertices_data['coordinates'][0]]
                vertices_y = [vertices_data['coordinates'][1]]
                count = 1
            else:
                vertices_x = [coordinates[0] for coordinates in
                              vertices_data['coordinates']]
                vertices_y = [coordinates[1] for coordinates in
                              vertices_data['coordinates']]
                count = len(vertices_data['coordinates'])
            print('Setting vertices_x={}, vertices_y={}, count={}'.format(
                vertices_x, vertices_y, count))
            en.setvertices(
                ph=proj,
                index=index,
                x=make_array(vertices_x),
                y=make_array(vertices_y),
                count=count
            )
    return proj


def _generate_valves(proj, ngsi_ld_data: dict):
    for valve in ngsi_ld_data:
        name = _name_from_id(valve['id'])
        link_type = _valve_type_from_entity(valve)[0]
        if link_type == 8:
            # InitSetting cannot be set for GPVs (link type 8). Instead, a head
            # loss curve ID needs to be set, but there is no toolkit function
            # for this at present.
            raise RuntimeError(
                """ERROR: Model contains a general purpose valve, but the """
                """EPANET toolkit has no functionality at present to set """
                """the head curve for these""")
        en.addlink(
            ph=proj,
            id=name,
            linkType=link_type,
            fromNode=_name_from_id(valve['startsAt']['object']),
            toNode=_name_from_id(valve['endsAt']['object'])
        )
        index = en.getlinkindex(proj, name)
        en.setlinkvalue(
            ph=proj,
            index=index,
            property=en.DIAMETER,
            value=valve['diameter']['value']
        )
        minor_loss_coeff = valve['minorLoss']['value']
        if minor_loss_coeff != 0:
            en.setlinkvalue(
                ph=proj,
                index=index,
                property=en.MINORLOSS,
                value=minor_loss_coeff
            )
        en.setlinkvalue(
            ph=proj,
            index=index,
            property=en.INITSETTING,
            value=valve['setting']['value']
        )
        if _value_if_exists(valve, 'vertices'):
            vertices_data = _value_if_exists(valve, 'vertices')
            if vertices_data['type'] == 'Point':
                vertices_x = [vertices_data['coordinates'][0]]
                vertices_y = [vertices_data['coordinates'][1]]
                count = 1
            else:
                vertices_x = [coordinates[0] for coordinates in
                              vertices_data['coordinates']]
                vertices_y = [coordinates[1] for coordinates in
                              vertices_data['coordinates']]
                count = len(vertices_data['coordinates'])
            print('Setting vertices_x={}, vertices_y={}, count={}'.format(
                vertices_x, vertices_y, count))
            en.setvertices(
                ph=proj,
                index=index,
                x=make_array(vertices_x),
                y=make_array(vertices_y),
                count=count
            )
    return proj


def make_array(values):
    dbl_arr = en.doubleArray(len(values))
    for i in range(len(values)):
        dbl_arr[i] = values[i]
    return dbl_arr
