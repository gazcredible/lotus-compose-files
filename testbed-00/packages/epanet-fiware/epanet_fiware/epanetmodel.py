# flake8: noqa: E302
import epanet.toolkit as en
from typing import Optional, Union, List
from enum import Enum

import epanet_fiware.epanet_project_reader as epr
import epanet_fiware.epanet_project_writer as epw
from epanet_fiware.epanet_simulation import OutputsDynamic, simulate
import epanet_fiware.epanet_simulation as es
import epanet_fiware.fiware_connection as fc
import epanet_fiware.ngsi_ld_writer as nlw
import epanet_fiware.ngsi_ld_reader as nlr
import epanet_fiware.enumerations as enu
from epanet_fiware.epanet_outfile_handler import (
    EpanetOutFile, NodeResultLabels, LinkResultLabels)

class SimStatus(Enum):
    none = 'none'
    initialised = 'initialised'
    started = 'started'
    finished = 'finished'
    closed = 'closed'


class EPAnetModel:
    def __init__(self, network_name: str,
                 filename: Optional[str] = None,
                 output_path: Optional[str] = '.',
                 inp_coordinate_system: Optional[
                     nlw.CoordinateSystem] = nlw.CoordinateSystem.undefined,
                 gateway_server: Optional[str] = None,  # For existing model
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 auth_url: Optional[str] = None):
        self.name = network_name
        self.inp_file = filename
        self.inp_coordinate_system = inp_coordinate_system
        self.gateway_server = gateway_server
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.rpt_file = '{}/{}.rpt'.format(output_path, self.name)
        self.out_file = '{}/{}.out'.format(output_path, self.name)
        self.project_source = enu.ProjectSources.NoModel
        self.proj_for_simulation = None  # EPANET project
        self.out_file_available = False
        self.result_from_stepped_sim = None   # Simulation results
        self.out_file_data = None
        self.simulation_status = SimStatus.none  # Status of simulation
        self._populate_project()  # From .inp file if available, else FIWARE

    def _populate_project(self):
        if self.inp_file:
            self.proj_for_simulation = en.createproject()
            en.open(
                ph=self.proj_for_simulation, inpFile=self.inp_file,
                rptFile=self.rpt_file, outFile=self.out_file)
            self.project_source = enu.ProjectSources.Inp
        elif self.gateway_server:
            self.proj_for_simulation = nlr.project_from_fiware(
                network_name=self.name,
                rpt_file=self.rpt_file,
                gateway_server=self.gateway_server,
                client_id=self.client_id,
                client_secret=self.client_secret,
                auth_url=self.auth_url
            )
            self.project_source = enu.ProjectSources.Fiware
        else:
            raise RuntimeError(
                """ERROR: No model available to load. """
                """Please provide an .inp file or gateway server""")

    def _update_project_status(self, status: SimStatus):
        if self.project_source == enu.ProjectSources.Fiware:
            self.inp_proj_status = status
        elif self.project_source == enu.ProjectSources.Inp:
            self.fiware_model_proj_status = status
        else:
            raise RuntimeError(
                'ERROR: No model loaded. Load model using FIWARE or .inp file')

    def get_node_ids(self, node_type: enu.NodeTypes) -> List[str]:
        if node_type.name not in enu.NodeTypes.__members__:
            raise RuntimeError(
                'ERROR: {} is not a node type'.format(node_type.name)
                )
        node_ids = []
        num_nodes = en.getcount(self.proj_for_simulation, en.NODECOUNT)
        for node_index in range(num_nodes):
            actual_type = en.getnodetype(
                self.proj_for_simulation, node_index + 1)
            if actual_type == node_type.value:
                node_id = en.getnodeid(
                    self.proj_for_simulation, node_index + 1)
                node_ids.append(node_id)
        return node_ids

    def get_link_ids(self, link_type: enu.LinkTypes) -> List[str]:
        if link_type.name not in enu.LinkTypes.__members__:
            raise RuntimeError(
                'ERROR: {} is not a link type'.format(link_type.name)
                )
        link_ids = []
        num_links = en.getcount(self.proj_for_simulation, en.LINKCOUNT)
        for link_index in range(num_links):
            actual_type = en.getlinktype(
                self.proj_for_simulation, link_index + 1)
            if actual_type == link_type.value:
                link_id = en.getlinkid(
                    self.proj_for_simulation, link_index + 1)
                link_ids.append(link_id)
        return link_ids

    def set_link_property(
            self, link_id: str,
            prop: Union[
                enu.PipeProperties, enu.PumpProperties, enu.ValveProperties],
            value: float):
        self._check_valid_link_prop(link_id, prop)
        self._check_method_set(prop)
        identifier = prop.value.Identifier
        method = getattr(epw, prop.value.MethodSet)
        self.proj_for_simulation = method(
            self.proj_for_simulation, link_id, identifier, value)

    def set_node_property(
            self, node_id: str,
            prop: Union[enu.JunctionProperties, enu.ReservoirProperties,
                        enu.TankProperties], value: float):
        self._check_valid_node_prop(node_id, prop)
        self._check_method_set(prop)
        identifier = prop.value.Identifier
        method = getattr(epw, prop.value.MethodSet)
        self.proj_for_simulation = method(
            self.proj_for_simulation, node_id, identifier, value)

    def get_link_property(
            self, link_id: str, prop: Union[
                enu.PipeProperties, enu.PumpProperties, enu.ValveProperties]):
        self._check_valid_link_prop(link_id, prop)
        identifier = prop.value.Identifier
        method = getattr(epr, prop.value.MethodGet)
        return method(self.proj_for_simulation, link_id, identifier)

    def get_node_property(
            self, node_id: str,
            prop: Union[enu.JunctionProperties, enu.ReservoirProperties,
                        enu.TankProperties]):
        self._check_valid_node_prop(node_id, prop)
        identifier = prop.value.Identifier
        method = getattr(epr, prop.value.MethodGet)
        return method(self.proj_for_simulation, node_id, identifier)

    def get_node_position(self, node_id: str):
        try:
            position = self.get_node_property(
                node_id, enu.JunctionProperties.Position)
        except Exception:
            try:
                position = self.get_node_property(
                    node_id, enu.TankProperties.Position)
            except Exception:
                position = self.get_node_property(
                    node_id, enu.ReservoirProperties.Position)
        return position

    def set_time_param(self, param: enu.TimeParams, value: int):
        self._check_valid_time_param(param)
        self._check_method_set(param)
        identifier = param.value.Identifier
        method = getattr(en, param.value.MethodSet)
        method(self.proj_for_simulation, identifier, value)

    def get_time_param(self, param: enu.TimeParams):
        self._check_valid_time_param(param)
        identifier = param.value.Identifier
        method = getattr(en, param.value.MethodGet)
        return method(self.proj_for_simulation, identifier)

    def get_option(self, option: enu.Options):
        self._check_valid_option(option)
        identifier = option.value.Identifier
        method = getattr(epr, option.value.MethodGet, None)
        if not callable(method):
            method = getattr(en, option.value.MethodGet)
        return method(self.proj_for_simulation, identifier)

    def set_option(self, option: enu.Options, value: int):
        self._check_valid_option(option)
        self._check_method_set(option)
        identifier = option.value.Identifier
        method = getattr(epw, option.value.MethodSet, None)
        if callable(method):
            self.proj_for_simulation = method(
                self.proj_for_simulation, value)
        else:
            method = getattr(en, option.value.MethodSet)
            method(self.proj_for_simulation, identifier, value)

    def set_epanet_mode(self, mode: enu.EpanetModes, pmin: float = 0,
                        preq: float = 0.1, pexp: float = 0.5):
        en.setdemandmodel(
            ph=self.proj_for_simulation, type=mode.value, pmin=pmin, preq=preq,
            pexp=pexp)

    def _get_node_type(self, node_id: str) -> enu.NodeTypes:
        node_index = en.getnodeindex(self.proj_for_simulation, node_id)
        node_type = en.getnodetype(self.proj_for_simulation, node_index)
        return enu.NodeTypes(node_type)

    def _get_link_type(self, link_id: str) -> enu.LinkTypes:
        link_index = en.getlinkindex(self.proj_for_simulation, link_id)
        link_type = en.getlinktype(self.proj_for_simulation, link_index)
        return enu.LinkTypes(link_type)

    def _check_valid_option(self, option: enu.Options):
        if option not in enu.Options:
            raise RuntimeError(
                'ERROR: {} is not a valid option'.format(
                    option))

    def _check_valid_time_param(self, param: enu.TimeParams):
        if param not in enu.TimeParams:
            raise RuntimeError(
                'ERROR: {} is not a valid time parameter'.format(
                    param))

    def _check_valid_link_prop(
            self, link_id: str,
            prop: Union[enu.PipeProperties, enu.PumpProperties,
                        enu.ValveProperties]) -> str:
        common_properties = [
            'Name', 'LinkType', 'StartNodeID', 'EndNodeID', 'VerticesX',
            'VerticesY', 'InitStatus', 'Diameter']
        link_type = self._get_link_type(link_id)
        if prop.name in common_properties:
            return
        if any([
            (link_type.value <= 1) and (prop not in enu.PipeProperties),
            (link_type.value == 2) and (prop not in enu.PumpProperties),
            (link_type.value >= 3) and (prop not in enu.ValveProperties)
        ]):
            raise RuntimeError(
                'ERROR: {} is not a valid {} property'.format(
                    prop, link_type.name))

    def _check_valid_node_prop(
            self, node_id: str,
            prop: Union[enu.JunctionProperties, enu.ReservoirProperties,
                        enu.TankProperties]):
        common_properties = [
            'Name', 'NodeType', 'Position', 'Elevation', 'InitQuality',
            'SourceQuality', 'SourceType']
        node_type = self._get_node_type(node_id)
        if prop.name in common_properties:
            return
        if any([
            (node_type.value == 0) and (prop not in enu.JunctionProperties),
            (node_type.value == 1) and (prop not in enu.ReservoirProperties),
            (node_type.value == 2) and (prop not in enu.TankProperties)
        ]):
            raise RuntimeError(
                'ERROR: {} is not a valid {} property'.format(
                    prop, node_type.name))

    def _check_method_set(
            self,
            prop: Union[enu.PipeProperties, enu.PumpProperties,
                        enu.ValveProperties, enu.JunctionProperties,
                        enu.ReservoirProperties, enu.TankProperties,
                        enu.TimeParams, enu.Options]):
        if prop.value.MethodSet is None:
            raise RuntimeError(
                'ERROR: {} cannot be set (read only)'.format(prop))

    def simulate_init(self):
        [self.proj_for_simulation, self.component_count,
         self.result_from_stepped_sim
         ] = es.initialise_simulation(self.proj_for_simulation)
        self.simulation_status = SimStatus.initialised

    def simulate_step(self, clear_previous_data=False):
        # Run a single simulation step
        if self.simulation_status == SimStatus.none:
            raise RuntimeError('Error: Simulation not initialised. '
                               'Use simulate_init()')
        if self.simulation_status in [SimStatus.finished, SimStatus.closed]:
            raise RuntimeError('Error: Simulation already finished '
                               'and/or closed')
        # delete existing simulation data to stop memory consumption
        if clear_previous_data is True:
            self.result_from_stepped_sim = OutputsDynamic(
                HydraulicNodes={},
                HydraulicLinks={},
                QualityNodes={},
                QualityLinks={},
                Ranges=self.result_from_stepped_sim.Ranges
            )
        [self.proj_for_simulation, self.proj_t, self.result_from_stepped_sim
         ] = es.simulate_step(
            self.proj_for_simulation,
            self.component_count,
            self.result_from_stepped_sim
        )
        if self.proj_t <= 0:
            self.simulation_status = SimStatus.finished
            self.simulate_close()
        else:
            self.simulation_status = SimStatus.started

    def simulate_close(self):
        # Close hydraulic and quality simulation
        if self.simulation_status in [SimStatus.none, SimStatus.closed]:
            raise RuntimeError('Error: No simulation to close')
        self.proj_for_simulation = es.finish_simulation(
            self.proj_for_simulation)
        self.simulation_status = SimStatus.closed

    def simulate_full(self):
        # Run full simulation (non step-by-step) and generate output binary
        # (quickest simulation approach)
        if self.proj_for_simulation is None:
            raise RuntimeError('Error: No project loaded for simulation')
        simulation_complete = simulate(self.proj_for_simulation)
        if simulation_complete:
            self.out_file_available = True
            self.out_file_data = EpanetOutFile(self.out_file)
        else:
            self.out_file_available = False

    def reporting_periods(self):
        try:
            return self.out_file_data.reporting_periods()
        except Exception:
            return None

    def _check_period_valid(self, period: int):
        if not self.out_file_data:
            raise RuntimeError('Error: Output file data available')
        total_periods = self.reporting_periods()
        if period not in range(total_periods):
            raise RuntimeError(
                'Error: {} is not a valid reporting period.'.format(period) +
                ' {} reporting periods available'.format(total_periods))

    def get_node_result(self,
                        period: int,
                        prop: NodeResultLabels,
                        node_id: Union[str, None] = None,
                        node_index: Union[int, None] = None):
        self._check_period_valid(period)
        if prop not in NodeResultLabels:
            raise RuntimeError('Error: {} is not a valid node result'.format(
                prop.name))
        if not node_index:
            if not node_id:
                raise RuntimeError(
                    'A node ID or a node index must be supplied')
            node_index = en.getnodeindex(self.proj_for_simulation, node_id)
        return getattr(self.out_file_data, prop.value)(period, node_index)

    def get_link_result(self,
                        period: int,
                        prop: LinkResultLabels,
                        link_id: Union[str, None] = None,
                        link_index: Union[int, None] = None):
        self._check_period_valid(period)
        if prop not in LinkResultLabels:
            raise RuntimeError('Error: {} is not a valid link result'.format(
                prop.name))
        if not link_index:
            if not link_id:
                raise RuntimeError(
                    'A link ID or a link index must be supplied')
            link_index = en.getlinkindex(self.proj_for_simulation, link_id)
        return getattr(self.out_file_data, prop.value)(period, link_index)

    def _post_components(self, access_token: Union[str, None],
                         component_type: str, gateway_server: str):
        method_names = {
            'Junctions': 'json_ld_junction',
            'Reservoirs': 'json_ld_reservoir',
            'Tanks': 'json_ld_tank',
            'Pipes': 'json_ld_pipe',
            'Pumps': 'json_ld_pump',
            'Valves': 'json_ld_valve',
            'Patterns': 'json_ld_pattern',
            'Curves': 'json_ld_curve'
        }
        method_name = method_names.get(component_type)
        if method_name:
            print('Posting {}'.format(component_type))
            method = getattr(nlw, method_name)
            data_all_components = method(
                self.proj_for_simulation,
                self.inp_coordinate_system
            )
            if len(data_all_components) > 0:
                fc.create_entities(access_token, data_all_components,
                                   gateway_server, self.name)

    def post_network_model(self,
                           gateway_server: str,
                           client_id: Optional[str] = None,
                           client_secret: Optional[str] = None,
                           auth_url: Optional[str] = None):
        if self.project_source != enu.ProjectSources.Inp:
            raise RuntimeError(
                'ERROR: No .inp file available to post')
        access_token = fc.get_access_token(client_id, client_secret, auth_url)
        fc.delete_network(access_token, gateway_server, self.name)
        for component in ['Junctions', 'Reservoirs', 'Tanks', 'Pipes', 'Pumps',
                          'Valves', 'Patterns', 'Curves']:
            self._post_components(access_token, component, gateway_server)
