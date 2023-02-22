from typing import NamedTuple
import time
import epanet.toolkit as en

from epanet_fiware.valuerange import ValueRange
import epanet_fiware.epanet_project_reader as epr

OutputsDynamic = NamedTuple('OutputsDynamic', [
    ('HydraulicNodes', dict),
    ('QualityNodes', dict),
    ('HydraulicLinks', dict),
    ('QualityLinks', dict),
    ('Ranges', dict)
])


def simulate_rpt(epanet_proj) -> None:
    en.resetreport(ph=epanet_proj)
    en.solveH(ph=epanet_proj)
    en.solveQ(ph=epanet_proj)
    en.setreport(ph=epanet_proj, format='SUMMARY YES')
    en.setreport(ph=epanet_proj, format='NODES ALL')
    en.setreport(ph=epanet_proj, format='LINKS ALL')
    en.setreport(ph=epanet_proj, format='status yes')
    en.setreport(ph=epanet_proj, format='quality yes')
    en.report(ph=epanet_proj)
    return None


def initialise_simulation(epanet_proj):
    count = epr.get_component_count(epanet_proj)
    en.openH(ph=epanet_proj)
    en.initH(ph=epanet_proj, initFlag=0)
    en.openQ(ph=epanet_proj)
    en.initQ(ph=epanet_proj, saveFlag=0)
    hydraulic_node_dict = {}
    hydraulic_link_dict = {}
    quality_node_dict = {}
    quality_link_dict = {}
    simulation_ranges = {}
    simulation_ranges['node_quality'] = ValueRange()
    simulation_ranges['junction_pressure'] = ValueRange()
    simulation_ranges['junction_demand_deficit'] = ValueRange()
    simulation_ranges['tank_level'] = ValueRange()
    simulation_ranges['tank_volume'] = ValueRange()
    simulation_ranges['link_flow'] = ValueRange()
    simulation_ranges['link_velocity'] = ValueRange()
    simulation_ranges['link_quality'] = ValueRange()
    simulation_ranges['valve_status'] = ValueRange()
    simulation_ranges['pump_state'] = ValueRange()
    return [epanet_proj, count,
            OutputsDynamic(
                HydraulicNodes=hydraulic_node_dict,
                HydraulicLinks=hydraulic_link_dict,
                QualityNodes=quality_node_dict,
                QualityLinks=quality_link_dict,
                Ranges=simulation_ranges
                )
            ]


def finish_simulation(epanet_proj):
    en.closeH(ph=epanet_proj)
    en.closeQ(ph=epanet_proj)
    return epanet_proj


def finish_quality_simulation(epanet_proj):
    en.closeQ(ph=epanet_proj)
    return epanet_proj


def simulate_step(epanet_proj, count: epr.Count, proj_result: OutputsDynamic):
    en.runH(ph=epanet_proj)
    en.runQ(ph=epanet_proj)
    [hydraulic_node_dict, simulation_ranges] = update_node_hyd_results(
        proj_result.HydraulicNodes,
        epanet_proj,
        count.Nodes,
        proj_result.Ranges
    )
    [hydraulic_link_dict, simulation_ranges] = update_link_hyd_results(
        proj_result.HydraulicLinks,
        epanet_proj,
        count.Links,
        simulation_ranges
    )
    [quality_node_dict, simulation_ranges] = update_node_quality_results(
        proj_result.QualityNodes,
        epanet_proj,
        count.Nodes,
        simulation_ranges
    )
    [quality_link_dict, simulation_ranges] = update_link_quality_results(
        proj_result.QualityLinks,
        epanet_proj,
        count.Links,
        simulation_ranges
    )
    t = en.nextH(ph=epanet_proj)
    t = en.nextQ(ph=epanet_proj)
    return [epanet_proj,
            t,
            OutputsDynamic(
                HydraulicNodes=hydraulic_node_dict,
                HydraulicLinks=hydraulic_link_dict,
                QualityNodes=quality_node_dict,
                QualityLinks=quality_link_dict,
                Ranges=simulation_ranges
                )
            ]


def simulate_quality_step(epanet_proj, count: epr.Count,
                          quality_node_dict: dict, quality_link_dict: dict,
                          simulation_ranges: dict):
    en.runQ(ph=epanet_proj)
    quality_node_dict, simulation_ranges = update_node_quality_results(
        quality_node_dict, epanet_proj, count.Nodes, simulation_ranges
    )
    quality_link_dict, simulation_ranges = update_link_quality_results(
        quality_link_dict, epanet_proj, count.Links, simulation_ranges
    )
    t = en.nextQ(ph=epanet_proj)
    return [epanet_proj, t, quality_node_dict, quality_link_dict,
            simulation_ranges]


def update_link_hyd_results(hydraulic_link_dict: dict, epanet_proj,
                            num_links: int, simulation_ranges: dict) -> dict:
    time_step = en.gettimeparam(epanet_proj, en.HTIME)
    hydraulic_link_dict[time_step] = {}
    for i in range(num_links):
        link_id = en.getlinkid(ph=epanet_proj, index=i + 1)
        status = en.getlinkvalue(
            ph=epanet_proj, index=i + 1, property=en.STATUS)
        velocity = en.getlinkvalue(
            ph=epanet_proj, index=i + 1, property=en.VELOCITY)
        flow = en.getlinkvalue(
            ph=epanet_proj, index=i + 1, property=en.FLOW)
        pump_state = en.getlinkvalue(
            ph=epanet_proj, index=i + 1, property=en.PUMP_STATE)

        hydraulic_link_dict[time_step][link_id] = {}
        hydraulic_link_dict[time_step][link_id]['status'] = status
        hydraulic_link_dict[time_step][link_id]['velocity'] = velocity
        hydraulic_link_dict[time_step][link_id]['flow'] = flow
        hydraulic_link_dict[time_step][link_id]['pumpState'] = pump_state

        simulation_ranges['link_flow'].add(flow)
        simulation_ranges['link_velocity'].add(velocity)
        simulation_ranges['valve_status'].add(status)
        simulation_ranges['pump_state'].add(pump_state)
    return hydraulic_link_dict, simulation_ranges


def update_link_quality_results(quality_link_dict: dict, epanet_proj,
                                num_links: int, simulation_ranges: dict
                                ) -> dict:
    time_step = en.gettimeparam(epanet_proj, en.QTIME)
    quality_link_dict[time_step] = {}
    for i in range(num_links):
        link_id = en.getlinkid(ph=epanet_proj, index=i + 1)
        quality = en.getlinkvalue(
            ph=epanet_proj, index=i + 1, property=en.LINKQUAL)
        quality_link_dict[time_step][link_id] = {}
        quality_link_dict[time_step][link_id]['quality'] = quality
        simulation_ranges['link_quality'].add(quality)
    return quality_link_dict, simulation_ranges


def update_node_hyd_results(hydraulic_node_dict: dict, epanet_proj,
                            num_nodes: int, simulation_ranges: dict) -> dict:
    time_step = en.gettimeparam(epanet_proj, en.HTIME)
    hydraulic_node_dict[time_step] = {}
    for i in range(num_nodes):
        node_id = en.getnodeid(ph=epanet_proj, index=i + 1)
        pressure = en.getnodevalue(
            ph=epanet_proj, index=i + 1, property=en.PRESSURE)
        demand = en.getnodevalue(
            ph=epanet_proj, index=i + 1, property=en.DEMAND)
        demand_deficit = en.getnodevalue(
            ph=epanet_proj, index=i + 1, property=en.DEMANDDEFICIT)
        head = en.getnodevalue(
            ph=epanet_proj, index=i + 1, property=en.HEAD)
        tank_level = en.getnodevalue(
            ph=epanet_proj, index=i + 1, property=en.TANKLEVEL)
        tank_volume = en.getnodevalue(
            ph=epanet_proj, index=i + 1, property=en.TANKVOLUME)

        hydraulic_node_dict[time_step][node_id] = {}
        hydraulic_node_dict[time_step][node_id]['pressure'] = pressure
        hydraulic_node_dict[time_step][node_id]['demand'] = demand
        hydraulic_node_dict[
            time_step][node_id]['demandDeficit'] = demand_deficit
        hydraulic_node_dict[time_step][node_id]['head'] = head
        hydraulic_node_dict[time_step][node_id]['tankLevel'] = tank_level
        hydraulic_node_dict[time_step][node_id]['tankVolume'] = tank_volume

        simulation_ranges['junction_pressure'].add(pressure)
        simulation_ranges['junction_demand_deficit'].add(demand_deficit)
        simulation_ranges['tank_level'].add(tank_level)
        simulation_ranges['tank_volume'].add(tank_volume)
    return hydraulic_node_dict, simulation_ranges


def update_node_quality_results(quality_node_dict: dict, epanet_proj,
                                num_nodes: int, simulation_ranges: dict
                                ) -> dict:
    time_step = en.gettimeparam(epanet_proj, en.QTIME)
    quality_node_dict[time_step] = {}
    for i in range(num_nodes):
        node_id = en.getnodeid(ph=epanet_proj, index=i + 1)
        quality = en.getnodevalue(
            ph=epanet_proj, index=i + 1, property=en.QUALITY)
        quality_node_dict[time_step][node_id] = {}
        quality_node_dict[time_step][node_id]['quality'] = quality
        simulation_ranges['node_quality'].add(quality)
    return quality_node_dict, simulation_ranges


def simulate(epanet_proj) -> bool:
    start_time = time.time()
    error_code = en.solveH(epanet_proj)
    if error_code not in [0, None]:
        print('Error {} in EN_solveH'.format(error_code))
        return False
    en.solveQ(epanet_proj)
    if error_code not in [0, None]:
        print('Error {} in EN_solveQ'.format(error_code))
        return False
    print('Simulation time: {} s'.format(time.time() - start_time))
    return True
