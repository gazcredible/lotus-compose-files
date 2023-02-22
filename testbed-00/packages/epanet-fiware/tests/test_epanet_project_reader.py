import epanet.toolkit as en

import epanet_fiware.epanet_project_reader as epr


def test_get_component_count():
    # If a project is supplied from an .inp
    inp_file = './tests/test_inputs/test_non_zero_pattern_start.inp'
    rpt_file = './tests/outputs/test.rpt'
    out_file = ''
    proj = en.createproject()
    en.open(proj, inp_file, rpt_file, out_file)
    # Then when the components are counted
    count = epr.get_component_count(proj)
    # The numbers returned should match those in the .inp file
    assert count.Nodes == 9
    assert count.Links == 9
    assert count.Patterns == 2
    assert count.Curves == 2
    assert count.Controls == 0
    assert count.Rules == 0
