import os
import click
# import epanet.toolkit as en

from epanet_fiware.epanetmodel import EPAnetModel, SimStatus
from epanet_fiware.ngsi_ld_writer import CoordinateSystem
import epanet_fiware.enumerations as enu
import epanet_fiware.epanet_outfile_handler as eoh
import config


@click.command()
@click.argument('epanet-inp-file', type=click.Path(exists=True))
@click.argument('output-path')
@click.option('--fiware/--no-fiware', default=False)
def main(epanet_inp_file: str, output_path: str, fiware: bool):
    """
    1. Generate python dictionaries from .inp file,
    EPANET_INP_FILENAME
    2. Run simulation from .inp file directly
    3. Run step-by-step simulation (from .inp file directly)
    4. Demo retrieval of model data
    dictionaries.
    5.Create JSON-LD and store entities with FIWARE
    6. Generate new EPAnetModel using FIWARE
    7. Set the required simulation duration
    8. Run simulation using model from FIWARE
    9. Demo retrieval of model data
    """

    inp_coordinate_system = CoordinateSystem.osgb

    # 1. Generate python dictionaries and EPANET projects from .inp file
    network_name = os.path.splitext(os.path.basename(epanet_inp_file))[0]
    model_inp = EPAnetModel(network_name=network_name,
                            filename=epanet_inp_file,
                            output_path=output_path,
                            inp_coordinate_system=inp_coordinate_system)

    # 2. Run simulation in one go to generate output binary
    model_inp.simulate_full()
    print('\nmodel_inp.out_file_data = \n{}\n', model_inp.out_file_data)
    
    # Retrieve a node's results at a specified time
    period = 3
    node_id = '32'
    node_index = None
    prop = eoh.NodeResultLabels.Head
    value = model_inp.get_node_result(
        period, prop, node_id, node_index)
    print('\nvalue = {}'.format(value))

    # Retrieve a link's results at a specified time
    period = 3
    link_id = '113'
    link_index = None
    prop = eoh.LinkResultLabels.ReactionRate
    value = model_inp.get_link_result(
        period, prop, link_id, link_index)
    print('\nvalue = {}'.format(value))

    # print('\nresult = \n{}\n', model_inp.result)

    # 3. Run step-by-step simulation
    # model_inp.simulate_init()
    # while model_inp.simulation_status in [
    #         SimStatus.initialised, SimStatus.started]:
    #     model_inp.simulate_step(clear_previous_data=True)
    # print('\nresult = \n{}\n', model_inp.result)

    # 4. Use get functions
    # get_functions_demo(model_inp)

    if fiware:
        # 6.Create JSON-LD and store entities with FIWARE

        model_inp.post_network_model(config.gateway_server, config.client_id,
                                     config.client_secret, config.auth_url)

        # 6. Generate new EPAnetModel using FIWARE
        model_fiware = EPAnetModel(
            network_name=network_name,
            output_path=output_path,
            inp_coordinate_system=inp_coordinate_system,
            gateway_server=config.gateway_server)

        # 7. Set the required simulation duration
        model_fiware.set_time_param(
            param=enu.TimeParams.Duration,
            value=24 * 60 * 60)

        # 8. Run simulation using model from FIWARE
        model_fiware.simulate_full()
        # print('\nresult = \n{}\n', model_inp.result)

        # 9. Use get functions
        get_functions_demo(model_fiware)

    # # Analyse EPANET project rules and controls
    # proj = model_inp.proj_for_simulation
    # num_rules = en.getcount(proj, en.RULECOUNT)
    # for i in range(num_rules):
    #     rule_index = i + 1
    #     print('rule_index =', rule_index)
    # num_controls = en.getcount(proj, en.CONTROLCOUNT)
    # for i in range(num_controls):
    #     control_index = i + 1
    #     print('control_index =', control_index)
    #     print('retrieved control =', en.getcontrol(proj, control_index))


def get_functions_demo(model: EPAnetModel):
    # 1. Get IDs
    junction_ids = model.get_node_ids(enu.NodeTypes.Junction)
    print('junction_ids = {}'.format(junction_ids))
    reservoir_ids = model.get_node_ids(enu.NodeTypes.Reservoir)
    print('reservoir_ids = {}'.format(reservoir_ids))
    tank_ids = model.get_node_ids(enu.NodeTypes.Tank)
    print('tank_ids = {}'.format(tank_ids))
    pipe_ids = model.get_link_ids(enu.LinkTypes.Pipe)
    print('pipe_ids = {}'.format(pipe_ids))
    cv_pipe_ids = model.get_link_ids(enu.LinkTypes.CheckValvePipe)
    print('cv_pipe_ids = {}'.format(cv_pipe_ids))
    pump_ids = model.get_link_ids(enu.LinkTypes.Pump)
    print('pump_ids = {}'.format(pump_ids))
    prv_ids = model.get_link_ids(enu.LinkTypes.PRValve)
    print('prv_ids = {}'.format(prv_ids))
    psv_ids = model.get_link_ids(enu.LinkTypes.PSValve)
    print('psv_ids = {}'.format(psv_ids))
    pbv_ids = model.get_link_ids(enu.LinkTypes.PBValve)
    print('pbv_ids = {}'.format(pbv_ids))
    fcv_ids = model.get_link_ids(enu.LinkTypes.FCValve)
    print('fcv_ids = {}'.format(fcv_ids))
    tcv_ids = model.get_link_ids(enu.LinkTypes.TCValve)
    print('tcv_ids = {}'.format(tcv_ids))
    gpv_ids = model.get_link_ids(enu.LinkTypes.GPValve)
    print('gpv_ids = {}'.format(gpv_ids))

    # 2. Get properties
    # a) All pipe diameters
    pipe_diameters = [
        model.get_link_property(pipe_id, enu.PipeProperties.Diameter) for
        pipe_id in pipe_ids]
    print('pipe_diameters =', pipe_diameters)
    # b) All junction diameters
    junction_base_demands = [
        model.get_node_property(
            junction_id, enu.JunctionProperties.BaseDemand) for
        junction_id in junction_ids]
    print('junction_base_demands =', junction_base_demands)
    # c) All pipe vertex x coordinates
    pipe_vertices_x = [
        model.get_link_property(pipe_id, enu.PipeProperties.VerticesX) for
        pipe_id in pipe_ids]
    print('pipe_vertices_x =', pipe_vertices_x)
    # d) All pipe vertex y coordinates
    pipe_vertices_y = [
        model.get_link_property(pipe_id, enu.PipeProperties.VerticesY) for
        pipe_id in pipe_ids]
    print('pipe_vertices_y =', pipe_vertices_y)
    # e) All junction positions
    junction_position = [
        model.get_node_property(
            junction_id, enu.JunctionProperties.Position) for
        junction_id in junction_ids]
    print('junction_position =', junction_position)
    # f) All junction types
    junction_types = [
        model.get_node_property(
            junction_id, enu.JunctionProperties.NodeType) for
        junction_id in junction_ids]
    print('junction_types =', junction_types)
    # g) All tank types
    tank_types = [
        model.get_node_property(
            tank_id, enu.TankProperties.NodeType) for
        tank_id in tank_ids]
    print('tank_types =', tank_types)
    # h) All pipe types
    pipe_types = [
        model.get_link_property(
            pipe_id, enu.PipeProperties.LinkType) for
        pipe_id in pipe_ids]
    print('pipe_types =', pipe_types)


if __name__ == "__main__":
    main()
