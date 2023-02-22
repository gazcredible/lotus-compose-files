import pytest
from math import pi
import epanet.toolkit as en

import epanet_fiware.enumerations as enu
from epanet_fiware.epanetmodel import EPAnetModel
from epanet_fiware.enumerations import ProjectSources, NodeTypes, LinkTypes
import epanet_fiware.ngsi_ld_writer as nlw
import config


def test_init_without_inp():
    # If only the model name is specified
    network_name = 'name'
    # Then when a model is generated, an exception should be raised
    with pytest.raises(Exception) as e:
        assert EPAnetModel(network_name=network_name)
        assert 'ERROR: No model available to load' in str(e.value)


def test_init_with_invalid_inp():
    # If an invalid .inp file name is specified
    network_name = 'name'
    filename = 'invalid'
    # Then when a model is generated an exception should be raised
    with pytest.raises(Exception) as e:
        assert EPAnetModel(
            network_name=network_name, filename=filename)
    assert str(e.value) == "Error 302: cannot open input file"


def test_init_with_inp_with_gpv():
    # If an .inp file containing a GPV is provided
    network_name = 'name'
    filename = './test_inputs/test_with_gpv.inp'
    inp_coordinate_system = nlw.CoordinateSystem.osgb
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename,
                        inp_coordinate_system=inp_coordinate_system)
    # An error should be raised when posting to FIWARE
    with pytest.raises(Exception) as e:
        assert model.post_network_model(config.gateway_server)
    assert 'contains a general purpose valve (GPV)' in str(e.value)


def test_init_with_inp_with_zero_pattern_start():
    # If a valid .inp file is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # An an EPANET project should have been generated for use in simulations
    assert model.proj_for_simulation
    # And the project source should have been set to 'Inp'
    assert model.project_source == ProjectSources.Inp
    # And it should be possible to run a simulation from proj_for_simulation
    # with no error
    model.simulate_full()


def test_get_node_ids_with_link_type():
    # If an .inp file is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # It should not be possible to retrieve junction ids using a link type
    with pytest.raises(RuntimeError):
        assert model.get_node_ids(LinkTypes.Pipe)


def test_get_link_ids_with_node_type():
    # If an .inp file is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # It should not be possible to retrieve link ids using a node type
    with pytest.raises(RuntimeError):
        assert model.get_link_ids(NodeTypes.Junction)


def test_get_node_ids_junctions():
    # If an .inp file with junctions ['J0', 'J1', 'J2', 'J3', 'J4', 'J5', 'J7']
    # is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The junction ids can be retrieved
    junction_ids = model.get_node_ids(NodeTypes.Junction)
    assert junction_ids == ['J0', 'J1', 'J2', 'J3', 'J4', 'J5', 'J7']


def test_get_node_ids_reservoirs():
    # If an .inp file with reservoirs ['R1']
    # is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The reservoir ids can be retrieved
    reservoir_ids = model.get_node_ids(NodeTypes.Reservoir)
    assert reservoir_ids == ['R1']


def test_get_node_ids_tanks():
    # If an .inp file with tanks ['T1']
    # is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The tank ids can be retrieved
    tank_ids = model.get_node_ids(NodeTypes.Tank)
    assert tank_ids == ['T1']


def test_get_link_ids_pipes():
    # If an .inp file with pipes ['P1', 'P3']
    # is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The pipe ids can be retrieved
    pipe_ids = model.get_link_ids(LinkTypes.Pipe)
    assert pipe_ids == ['P1', 'P3']


def test_get_link_ids_cvs():
    # If an .inp file with CV pipes ['P2']
    # is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The pipe ids can be retrieved
    pipe_ids = model.get_link_ids(LinkTypes.CheckValvePipe)
    assert pipe_ids == ['P2']


def test_get_link_ids_pumps():
    # If an .inp file with pumps ['pump1']
    # is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The pump ids can be retrieved
    pump_ids = model.get_link_ids(LinkTypes.Pump)
    assert pump_ids == ['pump1']


def test_get_link_ids_prvs():
    # If an .inp file with FCVs ['prv']
    # is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The valve ids can be retrieved
    valve_ids = model.get_link_ids(LinkTypes.PRValve)
    assert valve_ids == ['prv']


def test_get_link_ids_psvs():
    # If an .inp file with PSVs ['psv']
    # is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The valve ids can be retrieved
    valve_ids = model.get_link_ids(LinkTypes.PSValve)
    assert valve_ids == ['psv']


def test_get_link_ids_pbvs():
    # If an .inp file with PBVs ['pbv']
    # is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The valve ids can be retrieved
    valve_ids = model.get_link_ids(LinkTypes.PBValve)
    assert valve_ids == ['pbv']


def test_get_link_ids_fcvs():
    # If an .inp file with FCVs ['fcv']
    # is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The valve ids can be retrieved
    valve_ids = model.get_link_ids(LinkTypes.FCValve)
    assert valve_ids == ['fcv']


def test_get_link_ids_tcvs():
    # If an .inp file with FCVs ['tcv']
    # is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The valve ids can be retrieved
    valve_ids = model.get_link_ids(LinkTypes.TCValve)
    assert valve_ids == ['tcv']


def test_get_link_ids_gpvs():
    # If an .inp file with no GPVs is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The valve ids can be retrieved
    valve_ids = model.get_link_ids(LinkTypes.GPValve)
    assert valve_ids == []


def test_get_node_property_junction():
    # If an .inp file with junction 'J0' is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The junction properties retrieved should match those specified in the
    # .inp file
    assert model.get_node_property(
        'J0', enu.JunctionProperties.Name) == 'J0'
    assert model.get_node_property(
        'J0', enu.JunctionProperties.NodeType) == NodeTypes.Junction.value
    assert model.get_node_property(
        'J0', enu.JunctionProperties.Position) == [50, 70]
    assert round(model.get_node_property(
        'J0', enu.JunctionProperties.Elevation), 2) == 710
    assert model.get_node_property(
        'J0', enu.JunctionProperties.BaseDemand) == 5
    assert model.get_node_property(
        'J0', enu.JunctionProperties.DemandPatternName) == 'pattern1'
    assert model.get_node_property(
        'J0', enu.JunctionProperties.InitQuality) == 1
    assert model.get_node_property(
        'J0', enu.JunctionProperties.Emitter) == 5
    assert model.get_node_property(
        'J0', enu.JunctionProperties.SourceQuality) == 10
    assert model.get_node_property(
        'J0', enu.JunctionProperties.SourcePatternName) is None
    assert model.get_node_property(
        'J0', enu.JunctionProperties.SourceType) == enu.SourceTypes.MASS.value


def test_get_node_property_tank():
    # If an .inp file with tank 'T1' is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The tank properties retrieved should match those specified in the
    # .inp file
    expected_init_volume = round(pi * (50.5 / 2)**2 * 120, 2)
    expected_total_volume = round(pi * (50.5 / 2)**2 * 150, 2)
    expected_min_volume = round(pi * (50.5 / 2)**2 * 100, 2)
    assert model.get_node_property(
        'T1', enu.TankProperties.Name) == 'T1'
    assert model.get_node_property(
        'T1', enu.TankProperties.NodeType) == NodeTypes.Tank.value
    assert model.get_node_property(
        'T1', enu.TankProperties.Position) == [30, 70]
    assert model.get_node_property(
        'T1', enu.TankProperties.SourcePatternName) is None
    assert model.get_node_property(
        'T1', enu.TankProperties.Elevation) == 850
    assert model.get_node_property(
        'T1', enu.TankProperties.InitQuality) == 10
    assert model.get_node_property(
        'T1', enu.TankProperties.SourceQuality) is None
    assert model.get_node_property(
        'T1', enu.TankProperties.SourceType) is None
    assert round(model.get_node_property(
        'T1', enu.TankProperties.InitLevel), 2) == 120
    assert round(model.get_node_property(
        'T1', enu.TankProperties.InitVolume), 2) == expected_init_volume
    assert model.get_node_property(
        'T1', enu.TankProperties.MixModel) == 0
    assert round(model.get_node_property(
        'T1', enu.TankProperties.MixZoneVolume), 2) == expected_total_volume
    assert model.get_node_property(
        'T1', enu.TankProperties.Diameter) == 50.5
    assert round(model.get_node_property(
        'T1', enu.TankProperties.MinVolume), 2) == expected_min_volume
    assert model.get_node_property(
        'T1', enu.TankProperties.MinLevel) == 100
    assert model.get_node_property(
        'T1', enu.TankProperties.MaxLevel) == 150
    assert model.get_node_property(
        'T1', enu.TankProperties.MixFraction) == 1
    assert model.get_node_property(
        'T1', enu.TankProperties.KBulk) == -0.5
    assert model.get_node_property(
        'T1', enu.TankProperties.VolumeCurveName) is None
    assert round(model.get_node_property(
        'T1', enu.TankProperties.MaxVolume), 2) == expected_total_volume
    assert model.get_node_property(
        'T1', enu.TankProperties.CanOverflow) == 0


def test_get_node_property_reservoir():
    # If an .inp file with reservoir 'R1' is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The reservoir properties retrieved should match those specified in the
    # .inp file
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.Name) == 'R1'
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.NodeType) == NodeTypes.Reservoir.value
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.Position) == [20, 70]
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.SourcePatternName) == 'pattern1'
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.Elevation) == 800
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.InitQuality) == 9
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.SourceQuality) == 5
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.SourceType
        ) == enu.SourceTypes.CONCEN.value


def test_get_link_property_pipe():
    # If an .inp file with pipe 'P1' is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The pipe properties retrieved should match those specified in the
    # .inp file
    assert model.get_link_property(
        'P1', enu.PipeProperties.Name) == 'P1'
    assert model.get_link_property(
        'P1', enu.PipeProperties.LinkType) == LinkTypes.Pipe.value
    assert model.get_link_property(
        'P1', enu.PipeProperties.StartNodeID) == 'R1'
    assert model.get_link_property(
        'P1', enu.PipeProperties.EndNodeID) == 'J0'
    assert model.get_link_property(
        'P1', enu.PipeProperties.VerticesX) == [1, 2]
    assert model.get_link_property(
        'P1', enu.PipeProperties.VerticesY) == [2, 3]
    assert model.get_link_property(
        'P1', enu.PipeProperties.KBulk) == -0.5
    assert model.get_link_property(
        'P1', enu.PipeProperties.KWall) == -1
    assert model.get_link_property(
        'P1', enu.PipeProperties.Length) == 10530
    assert model.get_link_property(
        'P1', enu.PipeProperties.Diameter) == 18
    assert model.get_link_property(
        'P1', enu.PipeProperties.Roughness) == 100
    assert round(model.get_link_property(
        'P1', enu.PipeProperties.MinorLossCoeff), 4) == 0.01
    assert model.get_link_property(
        'P1', enu.PipeProperties.InitStatus) == 1


def test_get_link_property_pump():
    # If an .inp file with pump 'pump1' is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The pump properties retrieved should match those specified in the
    # .inp file
    assert model.get_link_property(
        'pump1', enu.PumpProperties.Name) == 'pump1'
    assert model.get_link_property(
        'pump1', enu.PumpProperties.LinkType) == LinkTypes.Pump.value
    assert model.get_link_property(
        'pump1', enu.PumpProperties.StartNodeID) == 'T1'
    assert model.get_link_property(
        'pump1', enu.PumpProperties.EndNodeID) == 'J0'
    assert model.get_link_property(
        'pump1', enu.PumpProperties.InitStatus) == 1
    assert model.get_link_property(
        'pump1', enu.PumpProperties.InitSetting) == 1
    assert model.get_link_property(
        'pump1', enu.PumpProperties.HCurveName) == 'curve_pump'
    assert model.get_link_property(
        'pump1', enu.PumpProperties.PowerRating) == 0
    assert model.get_link_property(
        'pump1', enu.PumpProperties.ECurveName) is None
    assert model.get_link_property(
        'pump1', enu.PumpProperties.ECost) == 0
    assert model.get_link_property(
        'pump1', enu.PumpProperties.EPatternName) is None
    assert model.get_link_property(
        'pump1', enu.PumpProperties.VerticesX) == [1.1]
    assert model.get_link_property(
        'pump1', enu.PumpProperties.VerticesY) == [2.2]
    assert model.get_link_property(
        'pump1', enu.PumpProperties.PumpSpeedPatternName) is None


def test_get_link_property_valve():
    # If an .inp file with valve 'prv' is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The pump properties retrieved should match those specified in the
    # .inp file
    assert model.get_link_property(
        'prv', enu.ValveProperties.Name) == 'prv'
    assert model.get_link_property(
        'prv', enu.ValveProperties.LinkType) == LinkTypes.PRValve.value
    assert model.get_link_property(
        'prv', enu.ValveProperties.StartNodeID) == 'J0'
    assert model.get_link_property(
        'prv', enu.ValveProperties.EndNodeID) == 'J1'
    assert model.get_link_property(
        'prv', enu.ValveProperties.Diameter) == 11
    assert model.get_link_property(
        'prv', enu.ValveProperties.MinorLossCoeff) == 0
    assert model.get_link_property(
        'prv', enu.ValveProperties.InitStatus) == 1
    assert model.get_link_property(
        'prv', enu.ValveProperties.InitSetting) == 10
    assert model.get_link_property(
        'prv', enu.ValveProperties.VerticesX) is None
    assert model.get_link_property(
        'prv', enu.ValveProperties.VerticesY) is None


def test_get_options():
    # If an .inp file is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # The options retrieved should match those specified in the
    # .inp file
    assert model.get_option(enu.Options.Trials) == 40
    assert model.get_option(enu.Options.Accuracy) == 0.001
    assert model.get_option(enu.Options.Tolerance) == 0.01
    assert model.get_option(enu.Options.EmitExpon) == 0.5
    assert model.get_option(enu.Options.DemandMult) == 1
    assert model.get_option(enu.Options.HeadError) == 0
    assert model.get_option(enu.Options.FlowChange) == 0
    assert model.get_option(enu.Options.HeadLossForm) == en.HW
    assert model.get_option(enu.Options.DemandCharge) == 0
    assert model.get_option(enu.Options.SpGravity) == 1
    assert model.get_option(enu.Options.Viscos) == 1
    assert model.get_option(enu.Options.Unbalanced) == 10
    assert model.get_option(enu.Options.CheckFreq) == 2
    assert model.get_option(enu.Options.MaxCheck) == 10
    assert model.get_option(enu.Options.DampLimit) == 0
    assert model.get_option(enu.Options.Diffus) == 1
    assert model.get_option(enu.Options.BulkOrder) == 1
    assert model.get_option(enu.Options.WallOrder) == 1
    assert model.get_option(enu.Options.TankOrder) == 1
    assert model.get_option(enu.Options.ConcenLimit) == 0
    assert model.get_option(enu.Options.QualInfo) == enu.QualityInfo(
        en.CHEM, 'Chlorine', 'mg/L', 0)


def test_set_options():
    # If an .inp file is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # It should be possible to set the options
    model.set_option(enu.Options.Trials, 50)
    assert model.get_option(enu.Options.Trials) == 50
    model.set_option(enu.Options.Accuracy, 0.002)
    assert model.get_option(enu.Options.Accuracy) == 0.002
    model.set_option(enu.Options.Tolerance, 0.02)
    assert model.get_option(enu.Options.Tolerance) == 0.02
    model.set_option(enu.Options.EmitExpon, 0.6)
    assert model.get_option(enu.Options.EmitExpon) == 0.6
    model.set_option(enu.Options.DemandMult, 2)
    assert model.get_option(enu.Options.DemandMult) == 2
    model.set_option(enu.Options.HeadError, 1)
    assert round(model.get_option(enu.Options.HeadError), 4) == 1
    model.set_option(enu.Options.FlowChange, 1)
    assert model.get_option(enu.Options.FlowChange) == 1
    model.set_option(enu.Options.HeadLossForm, en.DW)
    assert model.get_option(enu.Options.HeadLossForm) == en.DW
    model.set_option(enu.Options.DemandCharge, 10)
    assert model.get_option(enu.Options.DemandCharge) == 10
    model.set_option(enu.Options.SpGravity, 10)
    assert model.get_option(enu.Options.SpGravity) == 10
    model.set_option(enu.Options.Viscos, 2)
    assert model.get_option(enu.Options.Viscos) == 2
    model.set_option(enu.Options.Unbalanced, 20)
    assert model.get_option(enu.Options.Unbalanced) == 20
    model.set_option(enu.Options.CheckFreq, 3)
    assert model.get_option(enu.Options.CheckFreq) == 3
    model.set_option(enu.Options.MaxCheck, 20)
    assert model.get_option(enu.Options.MaxCheck) == 20
    model.set_option(enu.Options.DampLimit, 1)
    assert model.get_option(enu.Options.DampLimit) == 1
    model.set_option(enu.Options.Diffus, 2)
    assert model.get_option(enu.Options.Diffus) == 2
    model.set_option(enu.Options.BulkOrder, 2)
    assert model.get_option(enu.Options.BulkOrder) == 2
    model.set_option(enu.Options.WallOrder, 0)
    assert model.get_option(enu.Options.WallOrder) == 0
    model.set_option(enu.Options.TankOrder, 2)
    assert model.get_option(enu.Options.TankOrder) == 2
    model.set_option(enu.Options.ConcenLimit, 1)
    assert model.get_option(enu.Options.ConcenLimit) == 1
    model.set_option(enu.Options.QualInfo, enu.QualityInfo(
        en.AGE, 'substance', 'tonnes/L', 'R1'))
    assert model.get_option(enu.Options.QualInfo) == enu.QualityInfo(
        en.AGE, 'AGE', 'hrs', 0)


def test_set_link_property_pipe():
    # If an .inp file with pipe 'P1' is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # It should not be possible to change the following properties
    with pytest.raises(Exception) as e:
        assert model.set_link_property(
            'P1', enu.PipeProperties.Name, 'new_name')
        assert '(read only)' in e
        assert model.set_link_property(
            'P1', enu.PipeProperties.LinkType, enu.LinkTypes.Pump)
        assert '(read only)' in e
        assert model.set_link_property(
            'P1', enu.PipeProperties.StartNodeID, 'new_id')
        assert '(read only)' in e
        assert model.set_link_property(
            'P1', enu.PipeProperties.EndNodeID, 'new_id')
        assert '(read only)' in e
        assert model.set_link_property(
            'P1', enu.PipeProperties.VerticesX, [])
        assert '(read only)' in e
        assert model.set_link_property(
            'P1', enu.PipeProperties.VerticesY, [])
        assert '(read only)' in e
        assert model.set_link_property('P1', enu.PipeProperties.Flow, 0)
        assert '(read only)' in e
        assert model.set_link_property('P1', enu.PipeProperties.Velocity, 0)
        assert '(read only)' in e
        assert model.set_link_property('P1', enu.PipeProperties.HeadLoss, 0)
        assert '(read only)' in e
        assert model.set_link_property('P1', enu.PipeProperties.Quality, 0)
        assert '(read only)' in e
    # And the following properties should be correctly altered
    model.set_link_property('P1', enu.PipeProperties.KBulk, -0.7)
    assert model.get_link_property(
        'P1', enu.PipeProperties.KBulk) == -0.7
    model.set_link_property('P1', enu.PipeProperties.KWall, -0.7)
    assert model.get_link_property(
        'P1', enu.PipeProperties.KWall) == -0.7
    model.set_link_property('P1', enu.PipeProperties.Length, 1)
    assert round(model.get_link_property(
        'P1', enu.PipeProperties.Length), 4) == 1
    model.set_link_property('P1', enu.PipeProperties.Diameter, 2)
    assert round(model.get_link_property(
        'P1', enu.PipeProperties.Diameter), 4) == 2
    model.set_link_property('P1', enu.PipeProperties.Roughness, 3)
    assert model.get_link_property(
        'P1', enu.PipeProperties.Roughness) == 3
    model.set_link_property('P1', enu.PipeProperties.MinorLossCoeff, 0.02)
    assert round(model.get_link_property(
        'P1', enu.PipeProperties.MinorLossCoeff), 4) == 0.02
    model.set_link_property('P1', enu.PipeProperties.InitStatus, 0)
    assert model.get_link_property(
        'P1', enu.PipeProperties.InitStatus) == 0


def test_set_link_property_pump():
    # If an .inp file with pump 'pump1' is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # It should not be possible to change the following properties
    with pytest.raises(Exception) as e:
        assert model.set_link_property(
            'pump1', enu.PumpProperties.Name, 'new_name')
        assert '(read only)' in e
        assert model.set_link_property(
            'pump1', enu.PumpProperties.LinkType, enu.LinkTypes.Pump)
        assert '(read only)' in e
        assert model.set_link_property(
            'pump1', enu.PumpProperties.StartNodeID, 'new_id')
        assert '(read only)' in e
        assert model.set_link_property(
            'pump1', enu.PumpProperties.EndNodeID, 'new_id')
        assert '(read only)' in e
        assert model.set_link_property(
            'pump1', enu.PumpProperties.HCurveName, 'new_id')
        assert '(read only)' in e
        assert model.set_link_property(
            'pump1', enu.PumpProperties.ECurveName, 'new_id')
        assert '(read only)' in e
        assert model.set_link_property(
            'pump1', enu.PumpProperties.EPatternName, 'new_id')
        assert '(read only)' in e
        assert model.set_link_property(
            'pump1', enu.PumpProperties.VerticesX, [])
        assert '(read only)' in e
        assert model.set_link_property(
            'pump1', enu.PumpProperties.VerticesY, [])
        assert '(read only)' in e
        assert model.set_link_property(
            'pump1', enu.PumpProperties.PumpSpeedPatternName, 'new_id')
        assert '(read only)' in e
        assert model.set_link_property('pump1', enu.PumpProperties.Flow, 0)
        assert '(read only)' in e
        assert model.set_link_property('pump1', enu.PumpProperties.Velocity, 0)
        assert '(read only)' in e
        assert model.set_link_property('pump1', enu.PumpProperties.HeadLoss, 0)
        assert '(read only)' in e
        assert model.set_link_property(
            'pump1', enu.PumpProperties.Quality, 0)
        assert '(read only)' in e
        assert model.set_link_property(
            'pump1', enu.PumpProperties.EnergyUse, 0)
        assert '(read only)' in e
        assert model.set_link_property(
            'pump1', enu.PumpProperties.PumpState, 0)
        assert '(read only)' in e
        assert model.set_link_property(
            'pump1', enu.PumpProperties.PumpEffic, 0)
        assert '(read only)' in e
    # And the following properties should be correctly altered
    model.set_link_property('pump1', enu.PumpProperties.InitStatus, 0)
    assert model.get_link_property(
        'pump1', enu.PumpProperties.InitStatus) == 0
    model.set_link_property('pump1', enu.PumpProperties.InitSetting, 0)
    assert model.get_link_property(
        'pump1', enu.PumpProperties.InitSetting) == 0
    model.set_link_property('pump1', enu.PumpProperties.PowerRating, 1)
    assert model.get_link_property(
        'pump1', enu.PumpProperties.PowerRating) == 1
    model.set_link_property('pump1', enu.PumpProperties.ECost, 1)
    assert model.get_link_property(
        'pump1', enu.PumpProperties.ECost) == 1
    model.set_link_property('pump1', enu.PumpProperties.Status, 1)
    assert model.get_link_property(
        'pump1', enu.PumpProperties.Status) == 1
    model.set_link_property('pump1', enu.PumpProperties.Setting, 1)
    assert model.get_link_property(
        'pump1', enu.PumpProperties.Setting) == 1


def test_set_link_property_valve():
    # If an .inp file with valve 'prv' is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # It should not be possible to change the following properties
    with pytest.raises(Exception) as e:
        assert model.set_link_property(
            'prv', enu.ValveProperties.Name, 'new_name')
        assert '(read only)' in e
        assert model.set_link_property(
            'prv', enu.ValveProperties.LinkType, enu.LinkTypes.Pump)
        assert '(read only)' in e
        assert model.set_link_property(
            'prv', enu.ValveProperties.StartNodeID, 'new_id')
        assert '(read only)' in e
        assert model.set_link_property(
            'prv', enu.ValveProperties.EndNodeID, 'new_id')
        assert '(read only)' in e
        assert model.set_link_property(
            'prv', enu.ValveProperties.VerticesX, [])
        assert '(read only)' in e
        assert model.set_link_property(
            'prv', enu.ValveProperties.VerticesY, [])
        assert '(read only)' in e
        assert model.set_link_property('prv', enu.ValveProperties.Flow, 0)
        assert '(read only)' in e
        assert model.set_link_property('prv', enu.ValveProperties.Velocity, 0)
        assert '(read only)' in e
        assert model.set_link_property('prv', enu.ValveProperties.HeadLoss, 0)
        assert '(read only)' in e
        assert model.set_link_property('prv', enu.ValveProperties.Quality, 0)
        assert '(read only)' in e
    # And the following properties should be correctly altered
    model.set_link_property('prv', enu.ValveProperties.Diameter, 2)
    assert round(model.get_link_property(
        'prv', enu.ValveProperties.Diameter), 4) == 2
    model.set_link_property('prv', enu.ValveProperties.MinorLossCoeff, 0.1)
    assert round(model.get_link_property(
        'prv', enu.ValveProperties.MinorLossCoeff), 4) == 0.1
    model.set_link_property('prv', enu.ValveProperties.InitStatus, 0)
    assert model.get_link_property(
        'prv', enu.ValveProperties.InitStatus) == 0
    model.set_link_property('prv', enu.ValveProperties.InitSetting, 5)
    assert model.get_link_property(
        'prv', enu.ValveProperties.InitSetting) == 5
    model.set_link_property('prv', enu.ValveProperties.Status, 1)
    assert model.get_link_property(
        'prv', enu.ValveProperties.Status) == 1
    model.set_link_property('prv', enu.ValveProperties.Setting, 8)
    assert round(model.get_link_property(
        'prv', enu.ValveProperties.Setting), 4) == 8


def test_set_node_property_junction():
    # If an .inp file with junction 'J0' is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # It should not be possible to change the following properties
    with pytest.raises(Exception) as e:
        assert model.set_node_property(
            'J0', enu.JunctionProperties.Name, 'new_name')
        assert '(read only)' in e
        assert model.set_node_property(
            'J0', enu.JunctionProperties.NodeType, enu.NodeTypes.Junction)
        assert '(read only)' in e
        assert model.set_node_property(
            'J0', enu.JunctionProperties.Position, [1, 2])
        assert '(read only)' in e
        assert model.set_node_property(
            'J0', enu.JunctionProperties.DemandPatternName, 'new_id')
        assert '(read only)' in e
        assert model.set_node_property(
            'J0', enu.JunctionProperties.SourcePatternName, 'new_id')
        assert '(read only)' in e
        assert model.set_node_property('J0', enu.JunctionProperties.Supply, 0)
        assert '(read only)' in e
        assert model.set_node_property(
            'J0', enu.JunctionProperties.SupplyDeficit, 0)
        assert '(read only)' in e
        assert model.set_node_property('J0', enu.JunctionProperties.Head, 0)
        assert '(read only)' in e
        assert model.set_node_property(
            'J0', enu.JunctionProperties.Pressure, 0)
        assert '(read only)' in e
        assert model.set_node_property('J0', enu.JunctionProperties.Quality, 0)
        assert '(read only)' in e
        assert model.set_node_property(
            'J0', enu.JunctionProperties.SourceMassInflow, 0)
        assert '(read only)' in e
    # And the following properties should be correctly altered
    model.set_node_property('J0', enu.JunctionProperties.Elevation, 100)
    assert round(model.get_node_property(
        'J0', enu.JunctionProperties.Elevation), 4) == 100
    model.set_node_property('J0', enu.JunctionProperties.BaseDemand, 10)
    assert round(model.get_node_property(
        'J0', enu.JunctionProperties.BaseDemand), 4) == 10
    model.set_node_property('J0', enu.JunctionProperties.InitQuality, 0)
    assert model.get_node_property(
        'J0', enu.JunctionProperties.InitQuality) == 0
    model.set_node_property('J0', enu.JunctionProperties.Emitter, 1)
    assert model.get_node_property(
        'J0', enu.JunctionProperties.Emitter) == 1
    model.set_node_property('J0', enu.JunctionProperties.SourceQuality, 5)
    assert model.get_node_property(
        'J0', enu.JunctionProperties.SourceQuality) == 5
    model.set_node_property(
        'J0', enu.JunctionProperties.SourceType, enu.SourceTypes.CONCEN.value)
    assert model.get_node_property(
        'J0', enu.JunctionProperties.SourceType
        ) == enu.SourceTypes.CONCEN.value


def test_set_node_property_tank():
    # If an .inp file with tank 'T1' is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # It should not be possible to change the following properties
    with pytest.raises(Exception) as e:
        assert model.set_node_property(
            'T1', enu.TankProperties.Name, 'new_name')
        assert '(read only)' in e
        assert model.set_node_property(
            'T1', enu.TankProperties.NodeType, enu.NodeTypes.Junction)
        assert '(read only)' in e
        assert model.set_node_property(
            'T1', enu.TankProperties.Position, [1, 2])
        assert '(read only)' in e
        assert model.set_node_property(
            'T1', enu.TankProperties.SourcePatternName, 'new_id')
        assert '(read only)' in e
        assert model.set_node_property(
            'T1', enu.TankProperties.InitVolume, 0)
        assert '(read only)' in e
        assert model.set_node_property(
            'T1', enu.TankProperties.MixZoneVolume, 0)
        assert '(read only)' in e
        assert model.set_node_property(
            'T1', enu.TankProperties.VolumeCurveName, 'new_id')
        assert '(read only)' in e
        assert model.set_node_property(
            'T1', enu.TankProperties.MaxVolume, 0)
        assert '(read only)' in e
        assert model.set_node_property(
            'T1', enu.TankProperties.CanOverflow, 1)
        assert '(read only)' in e
        assert model.set_node_property(
            'T1', enu.TankProperties.TankLevel, 0)
        assert '(read only)' in e
        assert model.set_node_property('T1', enu.TankProperties.Supply, 0)
        assert '(read only)' in e
        assert model.set_node_property(
            'T1', enu.TankProperties.SupplyDeficit, 0)
        assert '(read only)' in e
        assert model.set_node_property('T1', enu.TankProperties.Head, 0)
        assert '(read only)' in e
        assert model.set_node_property(
            'T1', enu.TankProperties.Pressure, 0)
        assert '(read only)' in e
        assert model.set_node_property('T1', enu.TankProperties.Quality, 0)
        assert '(read only)' in e
        assert model.set_node_property(
            'T1', enu.TankProperties.SourceMassInflow, 0)
        assert '(read only)' in e
        assert model.set_node_property(
            'T1', enu.TankProperties.Volume, 0)
        assert '(read only)' in e
    # And the following properties should be correctly altered
    model.set_node_property('T1', enu.TankProperties.Elevation, 100)
    assert round(model.get_node_property(
        'T1', enu.TankProperties.Elevation), 4) == 100
    model.set_node_property('T1', enu.TankProperties.InitQuality, 0)
    assert model.get_node_property(
        'T1', enu.TankProperties.InitQuality) == 0
    model.set_node_property('T1', enu.TankProperties.SourceQuality, 5)
    assert model.get_node_property(
        'T1', enu.TankProperties.SourceQuality) == 5
    model.set_node_property(
        'T1', enu.TankProperties.SourceType, enu.SourceTypes.CONCEN.value)
    assert model.get_node_property(
        'T1', enu.TankProperties.SourceType
        ) == enu.SourceTypes.CONCEN.value
    model.set_node_property('T1', enu.TankProperties.InitLevel, 100)
    assert round(model.get_node_property(
        'T1', enu.TankProperties.InitLevel), 4) == 100
    model.set_node_property('T1', enu.TankProperties.MixModel, 1)
    assert model.get_node_property(
        'T1', enu.TankProperties.MixModel) == 1
    model.set_node_property('T1', enu.TankProperties.Diameter, 5)
    assert round(model.get_node_property(
        'T1', enu.TankProperties.Diameter), 4) == 5
    model.set_node_property('T1', enu.TankProperties.MinVolume, 0.1)
    assert model.get_node_property(
        'T1', enu.TankProperties.MinVolume) == 0.1
    model.set_node_property('T1', enu.TankProperties.MinLevel, 0.1)
    assert round(model.get_node_property(
        'T1', enu.TankProperties.MinLevel), 4) == 0.1
    model.set_node_property('T1', enu.TankProperties.MaxLevel, 125)
    assert round(model.get_node_property(
        'T1', enu.TankProperties.MaxLevel), 4) == 125
    model.set_node_property('T1', enu.TankProperties.MixFraction, 0.5)
    assert model.get_node_property(
        'T1', enu.TankProperties.MixFraction) == 0.5
    model.set_node_property('T1', enu.TankProperties.KBulk, 0.5)
    assert model.get_node_property(
        'T1', enu.TankProperties.KBulk) == 0.5


def test_set_node_property_reservoir():
    # If an .inp file with reservoir 'R1' is provided
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename)
    # It should not be possible to change the following properties
    with pytest.raises(Exception) as e:
        assert model.set_node_property(
            'R1', enu.ReservoirProperties.Name, 'new_name')
        assert '(read only)' in e
        assert model.set_node_property(
            'R1', enu.ReservoirProperties.NodeType, enu.NodeTypes.Junction)
        assert '(read only)' in e
        assert model.set_node_property(
            'R1', enu.ReservoirProperties.Position, [1, 2])
        assert '(read only)' in e
        assert model.set_node_property(
            'R1', enu.ReservoirProperties.SourcePatternName, 'new_id')
        assert '(read only)' in e
        assert model.set_node_property('R1', enu.ReservoirProperties.Supply, 0)
        assert '(read only)' in e
        assert model.set_node_property(
            'R1', enu.ReservoirProperties.SupplyDeficit, 0)
        assert '(read only)' in e
        assert model.set_node_property('R1', enu.ReservoirProperties.Head, 0)
        assert '(read only)' in e
        assert model.set_node_property(
            'R1', enu.ReservoirProperties.Pressure, 0)
        assert '(read only)' in e
        assert model.set_node_property(
            'R1', enu.ReservoirProperties.Quality, 0)
        assert '(read only)' in e
        assert model.set_node_property(
            'R1', enu.ReservoirProperties.SourceMassInflow, 0)
        assert '(read only)' in e
    # And the following properties should be correctly altered
    model.set_node_property('R1', enu.ReservoirProperties.Elevation, 100)
    assert round(model.get_node_property(
        'R1', enu.ReservoirProperties.Elevation), 4) == 100
    model.set_node_property('R1', enu.ReservoirProperties.InitQuality, 0)
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.InitQuality) == 0
    model.set_node_property('R1', enu.ReservoirProperties.SourceQuality, 5)
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.SourceQuality) == 5
    model.set_node_property(
        'R1', enu.ReservoirProperties.SourceType, enu.SourceTypes.CONCEN.value)
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.SourceType
        ) == enu.SourceTypes.CONCEN.value


def test_post_network():
    # If an .inp file is provided with an appropriatelyy specified coordinate
    # referencing system
    network_name = 'name'
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    inp_coordinate_system = nlw.CoordinateSystem.osgb
    # Then after a model has been generated
    model = EPAnetModel(network_name=network_name, filename=filename,
                        inp_coordinate_system=inp_coordinate_system)
    # This can be posted using FIWARE
    model.post_network_model(config.gateway_server)


def test_retrieve_network():
    # If a network name is supplied that matches the one given when a
    # network was posted (with test_post_network())
    network_name = 'name'
    # Then a model can be retrieved using FIWARE
    model = EPAnetModel(
            network_name=network_name,
            gateway_server=config.gateway_server)
    # And the component ids should match those in the original .inp file
    junction_ids = model.get_node_ids(NodeTypes.Junction)
    assert junction_ids == ['J0', 'J1', 'J2', 'J3', 'J4', 'J5', 'J7']
    reservoir_ids = model.get_node_ids(NodeTypes.Reservoir)
    assert reservoir_ids == ['R1']
    tank_ids = model.get_node_ids(NodeTypes.Tank)
    assert tank_ids == ['T1']
    pipe_ids = model.get_link_ids(LinkTypes.Pipe)
    assert pipe_ids == ['P1', 'P3']
    pipe_ids = model.get_link_ids(LinkTypes.CheckValvePipe)
    assert pipe_ids == ['P2']
    pump_ids = model.get_link_ids(LinkTypes.Pump)
    assert pump_ids == ['pump1']
    valve_ids = model.get_link_ids(LinkTypes.PRValve)
    assert valve_ids == ['prv']
    valve_ids = model.get_link_ids(LinkTypes.PSValve)
    assert valve_ids == ['psv']
    valve_ids = model.get_link_ids(LinkTypes.PBValve)
    assert valve_ids == ['pbv']
    valve_ids = model.get_link_ids(LinkTypes.FCValve)
    assert valve_ids == ['fcv']
    valve_ids = model.get_link_ids(LinkTypes.TCValve)
    assert valve_ids == ['tcv']
    valve_ids = model.get_link_ids(LinkTypes.GPValve)
    assert valve_ids == []
    # And junction properties (except coordinates, which have been converted
    # to WGS84) should match those in the .inp file, since the .inp file uses
    # metric units
    assert model.get_node_property(
        'J0', enu.JunctionProperties.Name) == 'J0'
    assert model.get_node_property(
        'J0', enu.JunctionProperties.NodeType) == NodeTypes.Junction.value
    assert model.get_node_property(
        'J0', enu.JunctionProperties.Position) != [50, 70]
    assert round(model.get_node_property(
        'J0', enu.JunctionProperties.Elevation), 2) == 710
    assert model.get_node_property(
        'J0', enu.JunctionProperties.BaseDemand) == 5
    assert model.get_node_property(
        'J0', enu.JunctionProperties.DemandPatternName) == 'pattern1'
    assert model.get_node_property(
        'J0', enu.JunctionProperties.InitQuality) == 1
    assert model.get_node_property(
        'J0', enu.JunctionProperties.Emitter) == 5
    assert model.get_node_property(
        'J0', enu.JunctionProperties.SourceQuality) == 10
    assert model.get_node_property(
        'J0', enu.JunctionProperties.SourcePatternName) is None
    assert model.get_node_property(
        'J0', enu.JunctionProperties.SourceType) == enu.SourceTypes.MASS.value
    # And tank properties (except coordinates, which have been converted to
    # WGS84) should match those in the .inp file, since the .inp file uses
    # metric units
    expected_init_volume = round(pi * (50.5 / 2)**2 * 120, 2)
    expected_total_volume = round(pi * (50.5 / 2)**2 * 150, 2)
    expected_min_volume = round(pi * (50.5 / 2)**2 * 100, 2)
    assert model.get_node_property(
        'T1', enu.TankProperties.Name) == 'T1'
    assert model.get_node_property(
        'T1', enu.TankProperties.NodeType) == NodeTypes.Tank.value
    assert model.get_node_property(
        'T1', enu.TankProperties.Position) != [30, 70]
    assert model.get_node_property(
        'T1', enu.TankProperties.SourcePatternName) is None
    assert model.get_node_property(
        'T1', enu.TankProperties.Elevation) == 850
    assert model.get_node_property(
        'T1', enu.TankProperties.InitQuality) == 10
    assert model.get_node_property(
        'T1', enu.TankProperties.SourceQuality) is None
    assert model.get_node_property(
        'T1', enu.TankProperties.SourceType) is None
    assert round(model.get_node_property(
        'T1', enu.TankProperties.InitVolume), 2) == expected_init_volume
    assert model.get_node_property(
        'T1', enu.TankProperties.MixModel) == 0
    assert round(model.get_node_property(
        'T1', enu.TankProperties.MixZoneVolume), 2) == expected_total_volume
    assert model.get_node_property(
        'T1', enu.TankProperties.Diameter) == 50.5
    assert round(model.get_node_property(
        'T1', enu.TankProperties.MinVolume), 2) == expected_min_volume
    assert model.get_node_property(
        'T1', enu.TankProperties.MinLevel) == 100
    assert model.get_node_property(
        'T1', enu.TankProperties.MaxLevel) == 150
    assert model.get_node_property(
        'T1', enu.TankProperties.MixFraction) == 1
    assert model.get_node_property(
        'T1', enu.TankProperties.KBulk) == -0.5
    assert model.get_node_property(
        'T1', enu.TankProperties.VolumeCurveName) is None
    assert round(model.get_node_property(
        'T1', enu.TankProperties.MaxVolume), 2) == expected_total_volume
    assert model.get_node_property(
        'T1', enu.TankProperties.CanOverflow) == 0
    # And reservoir properties (except coordinates, which have been converted
    # to WGS84) should match those in the .inp file, since the .inp file uses
    # metric units
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.Name) == 'R1'
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.NodeType) == NodeTypes.Reservoir.value
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.Position) != [20, 70]
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.SourcePatternName) == 'pattern1'
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.Elevation) == 800
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.InitQuality) == 9
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.SourceQuality) == 5
    assert model.get_node_property(
        'R1', enu.ReservoirProperties.SourceType
        ) == enu.SourceTypes.CONCEN.value
    # And pipe properties (except coordinates, which have been converted to
    # WGS84) should match those in the .inp file, since the .inp file uses
    # metric units
    assert model.get_link_property(
        'P1', enu.PipeProperties.Name) == 'P1'
    assert model.get_link_property(
        'P1', enu.PipeProperties.LinkType) == LinkTypes.Pipe.value
    assert model.get_link_property(
        'P2', enu.PipeProperties.LinkType) == LinkTypes.CheckValvePipe.value
    assert model.get_link_property(
        'P1', enu.PipeProperties.StartNodeID) == 'R1'
    assert model.get_link_property(
        'P1', enu.PipeProperties.EndNodeID) == 'J0'
    assert model.get_link_property(
        'P1', enu.PipeProperties.VerticesX) != [1, 2]
    assert model.get_link_property(
        'P1', enu.PipeProperties.VerticesY) != [2, 3]
    assert model.get_link_property(
        'P1', enu.PipeProperties.KBulk) == -0.5
    assert model.get_link_property(
        'P1', enu.PipeProperties.KWall) == -1
    assert model.get_link_property(
        'P1', enu.PipeProperties.Length) == 10530
    assert model.get_link_property(
        'P1', enu.PipeProperties.Diameter) == 18
    assert model.get_link_property(
        'P1', enu.PipeProperties.Roughness) == 100
    assert round(model.get_link_property(
        'P1', enu.PipeProperties.MinorLossCoeff), 4) == 0.01
    assert model.get_link_property(
        'P1', enu.PipeProperties.InitStatus) == 1
    # And pump properties (except coordinates, which have been converted to
    # WGS84) should match those in the .inp file, since the .inp file uses
    # metric units
    assert model.get_link_property(
        'pump1', enu.PumpProperties.Name) == 'pump1'
    assert model.get_link_property(
        'pump1', enu.PumpProperties.LinkType) == LinkTypes.Pump.value
    assert model.get_link_property(
        'pump1', enu.PumpProperties.StartNodeID) == 'T1'
    assert model.get_link_property(
        'pump1', enu.PumpProperties.EndNodeID) == 'J0'
    assert model.get_link_property(
        'pump1', enu.PumpProperties.InitStatus) == 1
    assert model.get_link_property(
        'pump1', enu.PumpProperties.InitSetting) == 1
    assert model.get_link_property(
        'pump1', enu.PumpProperties.HCurveName) == 'curve_pump'
    assert model.get_link_property(
        'pump1', enu.PumpProperties.PowerRating) == 0
    assert model.get_link_property(
        'pump1', enu.PumpProperties.ECurveName) is None
    assert model.get_link_property(
        'pump1', enu.PumpProperties.ECost) == 0
    assert model.get_link_property(
        'pump1', enu.PumpProperties.EPatternName) is None
    assert model.get_link_property(
        'pump1', enu.PumpProperties.VerticesX) != [1.1]
    assert model.get_link_property(
        'pump1', enu.PumpProperties.VerticesY) != [2.2]
    assert model.get_link_property(
        'pump1', enu.PumpProperties.PumpSpeedPatternName) is None
    # And valve properties (except coordinates, which have been converted to
    # WGS84) should match those in the .inp file, since the .inp file uses
    # metric units
    assert model.get_link_property(
        'prv', enu.ValveProperties.Name) == 'prv'
    assert model.get_link_property(
        'prv', enu.ValveProperties.LinkType) == LinkTypes.PRValve.value
    assert model.get_link_property(
        'psv', enu.ValveProperties.LinkType) == LinkTypes.PSValve.value
    assert model.get_link_property(
        'pbv', enu.ValveProperties.LinkType) == LinkTypes.PBValve.value
    assert model.get_link_property(
        'fcv', enu.ValveProperties.LinkType) == LinkTypes.FCValve.value
    assert model.get_link_property(
        'tcv', enu.ValveProperties.LinkType) == LinkTypes.TCValve.value
    assert model.get_link_property(
        'prv', enu.ValveProperties.StartNodeID) == 'J0'
    assert model.get_link_property(
        'prv', enu.ValveProperties.EndNodeID) == 'J1'
    assert model.get_link_property(
        'prv', enu.ValveProperties.Diameter) == 11
    assert model.get_link_property(
        'prv', enu.ValveProperties.MinorLossCoeff) == 0
    assert model.get_link_property(
        'prv', enu.ValveProperties.InitStatus) == 1
    assert model.get_link_property(
        'prv', enu.ValveProperties.InitSetting) == 10
    assert model.get_link_property(
        'prv', enu.ValveProperties.VerticesX) is None
    assert model.get_link_property(
        'prv', enu.ValveProperties.VerticesY) is None
    # And pattern start time and time step should match those in the .inp file
    assert model.get_time_param(enu.TimeParams.PatternStart) == 2 * 60 * 60
    assert model.get_time_param(enu.TimeParams.PatternStep) == 2 * 60 * 60


def test_simulate_full_with_fiware():
    # If a network name is supplied that matches the one given when a
    # network was posted (with test_post_network())
    network_name = 'name'
    # And a model is retrieved using FIWARE
    model_fiware = EPAnetModel(
            network_name=network_name,
            gateway_server=config.gateway_server)
    # And the time parameters are set to match those in the inp file
    filename = './test_inputs/test_non_zero_pattern_start.inp'
    model_inp = EPAnetModel(network_name=network_name, filename=filename)
    duration = model_inp.get_time_param(enu.TimeParams.Duration)
    model_fiware.set_time_param(enu.TimeParams.Duration, duration)
    hyd_step = model_inp.get_time_param(enu.TimeParams.HydStep)
    model_fiware.set_time_param(enu.TimeParams.HydStep, hyd_step)
    qual_step = model_inp.get_time_param(enu.TimeParams.QualStep)
    model_fiware.set_time_param(enu.TimeParams.QualStep, qual_step)
    report_step = model_inp.get_time_param(enu.TimeParams.ReportStep)
    model_fiware.set_time_param(enu.TimeParams.ReportStep, report_step)
    report_start = model_inp.get_time_param(enu.TimeParams.ReportStart)
    model_fiware.set_time_param(enu.TimeParams.ReportStart, report_start)
    rule_start = model_inp.get_time_param(enu.TimeParams.RuleStep)
    model_fiware.set_time_param(enu.TimeParams.RuleStep, rule_start)
    statistic = model_inp.get_time_param(enu.TimeParams.Statistic)
    model_fiware.set_time_param(enu.TimeParams.Statistic, statistic)
    # And the quality options are set to match those in the inp file
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
    # Then a full simulaion can be run
    model_fiware.simulate_full()
    # And the simulation results should match results generated using the .inp
    # file directly
    model_inp.simulate_full()
    result_fiware = model_fiware.result
    result_inp = model_inp.result
    # a) the node quality ranges should match
    range_fiware = result_fiware.Ranges['node_quality']
    range_inp = result_inp.Ranges['node_quality']
    assert round(range_fiware['minval'], 4) == round(range_inp['minval'], 4)
    assert round(range_fiware['maxval'], 4) == round(range_inp['maxval'], 4)
    # b) the junction_pressure ranges should match
    range_fiware = result_fiware.Ranges['junction_pressure']
    range_inp = result_inp.Ranges['junction_pressure']
    assert round(range_fiware['minval'], 4) == round(range_inp['minval'], 4)
    assert round(range_fiware['maxval'], 4) == round(range_inp['maxval'], 4)
    # b) the junction_pressure ranges should match
    range_fiware = result_fiware.Ranges['junction_pressure']
    range_inp = result_inp.Ranges['junction_pressure']
    assert round(range_fiware['minval'], 4) == round(range_inp['minval'], 4)
    assert round(range_fiware['maxval'], 4) == round(range_inp['maxval'], 4)
    # b) the junction_pressure ranges should match
    range_fiware = result_fiware.Ranges['junction_pressure']
    range_inp = result_inp.Ranges['junction_pressure']
    assert round(range_fiware['minval'], 4) == round(range_inp['minval'], 4)
    assert round(range_fiware['maxval'], 4) == round(range_inp['maxval'], 4)
    # c) the tank_level ranges should match
    range_fiware = result_fiware.Ranges['tank_level']
    range_inp = result_inp.Ranges['tank_level']
    assert round(range_fiware['minval'], 4) == round(range_inp['minval'], 4)
    assert round(range_fiware['maxval'], 4) == round(range_inp['maxval'], 4)
    # d) the tank_volume ranges should match
    range_fiware = result_fiware.Ranges['tank_volume']
    range_inp = result_inp.Ranges['tank_volume']
    assert round(range_fiware['minval'], 4) == round(range_inp['minval'], 4)
    assert round(range_fiware['maxval'], 4) == round(range_inp['maxval'], 4)
    # e) the link_flow ranges should match
    range_fiware = result_fiware.Ranges['link_flow']
    range_inp = result_inp.Ranges['link_flow']
    assert round(range_fiware['minval'], 4) == round(range_inp['minval'], 4)
    assert round(range_fiware['maxval'], 4) == round(range_inp['maxval'], 4)
    # f) the link_velocity ranges should match
    range_fiware = result_fiware.Ranges['link_velocity']
    range_inp = result_inp.Ranges['link_velocity']
    assert round(range_fiware['minval'], 4) == round(range_inp['minval'], 4)
    assert round(range_fiware['maxval'], 4) == round(range_inp['maxval'], 4)
    # g) the link_quality ranges should match
    range_fiware = result_fiware.Ranges['link_quality']
    range_inp = result_inp.Ranges['link_quality']
    assert round(range_fiware['minval'], 4) == round(range_inp['minval'], 4)
    assert round(range_fiware['maxval'], 4) == round(range_inp['maxval'], 4)
    # h) the valve_status ranges should match
    range_fiware = result_fiware.Ranges['valve_status']
    range_inp = result_inp.Ranges['valve_status']
    assert round(range_fiware['minval'], 4) == round(range_inp['minval'], 4)
    assert round(range_fiware['maxval'], 4) == round(range_inp['maxval'], 4)
    # i) the pump_state ranges should match
    range_fiware = result_fiware.Ranges['pump_state']
    range_inp = result_inp.Ranges['pump_state']
    assert round(range_fiware['minval'], 4) == round(range_inp['minval'], 4)
    assert round(range_fiware['maxval'], 4) == round(range_inp['maxval'], 4)
