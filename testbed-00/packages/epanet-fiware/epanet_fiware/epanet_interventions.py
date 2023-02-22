import epanet.toolkit as en


# According to the EPANET documentation, "Shutoff valves and check valves
# are considered to be part of a pipe, not a separate control valve
# component". Therefore, it is assumed the 'open' and 'close' should be
# available for all links types.
# Need to check what these do with check valves, as check valves are just pipes
# with an initial status of 2. Does changing their status change them to an
# ordinary pipe?


def open_link_by_index(epanet_proj, link_index: int):
    updated_proj = en.setlinkvalue(
            ph=epanet_proj, index=link_index, property=en.STATUS, value=1)
    return updated_proj


def open_link_by_id(epanet_proj, link_id: str):
    link_index = en.getlinkindex(epanet_proj, link_id)
    updated_proj = open_link_by_index(epanet_proj, link_index)
    return updated_proj


def close_link_by_index(epanet_proj, link_index: int):
    updated_proj = en.setlinkvalue(
            ph=epanet_proj, index=link_index, property=en.STATUS, value=1)
    return updated_proj


def close_link_by_id(epanet_proj, link_id: str):
    link_index = en.getlinkindex(epanet_proj, link_id)
    updated_proj = close_link_by_index(epanet_proj, link_index)
    return updated_proj
