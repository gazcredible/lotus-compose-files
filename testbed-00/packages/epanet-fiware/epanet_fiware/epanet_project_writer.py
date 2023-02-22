import epanet.toolkit as en
from epanet_fiware.enumerations import QualityInfo


def set_qual_info(
        proj, info: QualityInfo):
    en.setqualtype(
        ph=proj,
        qualType=info.QualType,
        chemName=info.ChemName,
        chemUnits=info.ChemUnits,
        traceNode=info.TraceNode)
    return proj


def set_init_level(proj, node_id: str, prop: int, value: float):
    tank_index = en.getnodeindex(ph=proj, id=node_id)
    elevation = en.getnodevalue(
        ph=proj, index=tank_index, property=en.ELEVATION)
    min_level = en.getnodevalue(
        ph=proj, index=tank_index, property=en.MINLEVEL)
    max_level = en.getnodevalue(
        ph=proj, index=tank_index, property=en.MAXLEVEL)
    diameter = en.getnodevalue(
        ph=proj, index=tank_index, property=en.TANKDIAM)
    min_vol = en.getnodevalue(
        ph=proj, index=tank_index, property=en.MINVOLUME)
    vol_curve_index = en.getnodevalue(
        ph=proj, index=tank_index, property=en.VOLCURVE)
    if vol_curve_index in [0, None]:
        vol_curve_id = ''
    else:
        vol_curve_id = en.getcurveid(
            ph=proj, index=int(vol_curve_index))
    en.settankdata(
        ph=proj,
        index=tank_index,
        elev=elevation,
        initlvl=value,
        minlvl=min_level,
        maxlvl=max_level,
        diam=diameter,
        minvol=min_vol,
        volcurve=vol_curve_id
    )
    return proj


def set_link_value(
        proj, link_id: str, prop: int, value: float):
    link_index = en.getlinkindex(ph=proj, id=link_id)
    en.setlinkvalue(ph=proj, index=link_index, property=prop, value=value)
    return proj


def set_node_value(
        proj, node_id: str, prop: int, value: float):
    node_index = en.getnodeindex(ph=proj, id=node_id)
    en.setnodevalue(ph=proj, index=node_index, property=prop, value=value)
    return proj
