import matplotlib.pyplot as plt

from epanet_fiware.epanetmodel import EPAnetModel
import epanet_fiware.enumerations as enu
from epanet_fiware.ngsi_ld_writer import CoordinateSystem
import config


def main(link_id: str, node_id: str, plot_all: bool = False):
    network_name = 'name'
    filename = './tests/test_inputs/test_non_zero_pattern_start.inp'

    # Simulation results from project generated from inp file
    model_inp = EPAnetModel(
        network_name=network_name,
        filename=filename,
        inp_coordinate_system=CoordinateSystem.osgb)
    print('Starting simulation from inp')
    model_inp.simulate_full()
    print('Simulation from inp complete')
    outputs_inp = model_inp.result

    # Simulation results from .inp file saved from project generated from .inp
    # file
    # ... to add

    # Simulation results generated using FIWARE
    print('Starting simulation from FIWARE')
    model_inp.post_network_model(config.gateway_server)
    model_fiware = EPAnetModel(
            network_name=network_name,
            gateway_server=config.gateway_server)

    qual_info = model_inp.get_option(enu.Options.QualInfo)
    model_fiware.set_option(
        enu.Options.QualInfo,
        enu.QualityInfo(
            qual_info.QualType,
            qual_info.ChemName,
            qual_info.ChemUnits,
            'R1'
        )
    )
    duration = model_inp.get_time_param(enu.TimeParams.Duration)
    model_fiware.set_time_param(enu.TimeParams.Duration, duration)
    hyd_step = model_inp.get_time_param(enu.TimeParams.HydStep)
    model_fiware.set_time_param(enu.TimeParams.HydStep, hyd_step)
    qual_step = model_inp.get_time_param(enu.TimeParams.QualStep)
    model_fiware.set_time_param(enu.TimeParams.QualStep, qual_step)
    pattern_step = model_inp.get_time_param(enu.TimeParams.PatternStep)
    model_fiware.set_time_param(enu.TimeParams.PatternStep, pattern_step)

    model_fiware.simulate_full()
    outputs_fiware = model_fiware.result

    times = [time for time in outputs_inp.HydraulicLinks]
    print('Simulation from FIWARE complete')

    # Identify link(s) and node(s) to plot
    if plot_all:
        links = [link for link in outputs_inp.HydraulicLinks[times[0]]]
        nodes = [node for node in outputs_inp.HydraulicNodes[times[0]]]
    else:
        links = [link_id]
        nodes = [node_id]

    # Plot results for selected link(s)
    for link in links:
        count = 0
        num_attributes = len(
            outputs_inp.HydraulicLinks[times[0]][link]) + len(
                outputs_inp.QualityLinks[times[0]][link])
        fig_links, axs_links = plt.subplots(num_attributes)
        fig_links.suptitle('Link {} results'.format(link))
        for attribute in outputs_inp.HydraulicLinks[times[0]][link]:
            result_inp = []
            result_fiware = []
            for time in times:
                result_inp.append(
                    outputs_inp.HydraulicLinks[time][link][attribute])
                result_fiware.append(
                    outputs_fiware.HydraulicLinks[time][link][attribute])
            axs_links[count].plot(times, result_inp, label='result_inp')
            axs_links[count].plot(times, result_fiware, label='result_fiware')
            axs_links[count].set(xlabel='time (s)', ylabel=attribute)
            axs_links[count].legend()
            count += 1
        for attribute in outputs_inp.QualityLinks[times[0]][link]:
            result_inp = []
            result_fiware = []
            for time in times:
                result_inp.append(
                    outputs_inp.QualityLinks[time][link][attribute])
                result_fiware.append(
                    outputs_fiware.QualityLinks[time][link][attribute])
            axs_links[count].plot(times, result_inp, label='result_inp')
            axs_links[count].plot(times, result_fiware, label='result_fiware')
            axs_links[count].set(xlabel='time (s)', ylabel=attribute)
            axs_links[count].legend()
            count += 1
        plt.show()

    # Plot results for selected node9s)
    for node in nodes:
        count = 0
        num_attributes = len(
            outputs_inp.HydraulicNodes[times[0]][node]) + len(
                outputs_inp.QualityNodes[times[0]][node])
        fig_nodes, axs_nodes = plt.subplots(num_attributes)
        fig_nodes.suptitle('Node {} results'.format(node))
        for attribute in outputs_inp.HydraulicNodes[times[0]][node]:
            result_inp = []
            result_fiware = []
            for time in times:
                result_inp.append(
                    outputs_inp.HydraulicNodes[time][node][attribute])
                result_fiware.append(
                    outputs_fiware.HydraulicNodes[time][node][attribute])
            axs_nodes[count].plot(times, result_inp, label='result_inp')
            axs_nodes[count].plot(times, result_fiware, label='result_fiware')
            axs_nodes[count].set(xlabel='time (s)', ylabel=attribute)
            axs_nodes[count].legend()
            count += 1
        for attribute in outputs_inp.QualityNodes[times[0]][node]:
            result_inp = []
            result_fiware = []
            for time in times:
                result_inp.append(
                    outputs_inp.QualityNodes[time][node][attribute])
                result_fiware.append(
                    outputs_fiware.QualityNodes[time][node][attribute])
            axs_nodes[count].plot(times, result_inp, label='result_inp')
            axs_nodes[count].plot(times, result_fiware, label='result_fiware')
            axs_nodes[count].set(xlabel='time (s)', ylabel=attribute)
            axs_nodes[count].legend()
            count += 1
        plt.show()


if __name__ == "__main__":
    link_id = 'P1'
    node_id = 'T1'
    plot_all = False
    main(link_id, node_id, plot_all)
