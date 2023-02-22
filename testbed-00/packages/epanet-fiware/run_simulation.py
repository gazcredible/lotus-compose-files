import os
import epanet.toolkit as en

import epanet_fiware.epanet_project_reader as epr


# inp_file = 'inputs/309D07_DMA.inp'
# inp_file = 'outputs/309D07_DMA_from_gui.inp'
inp_file = 'inputs/309D07_DMA_wgs84.inp'
output_path = 'outputs'
network_name = os.path.splitext(os.path.basename(inp_file))[0]

rpt_file = '{}/{}.rpt'.format(output_path, network_name)

proj = en.createproject()
en.open(ph=proj, inpFile=inp_file,
        rptFile=rpt_file, outFile='')

# Initialise hydraulic and quality simulation
count = epr.get_component_count(proj)
en.openH(ph=proj)
en.initH(ph=proj, initFlag=0)

# Run hydraulic simulation
index_node_for_analysis = 0
id_node_for_analysis = en.getnodeid(
    ph=proj, index=index_node_for_analysis + 1)
print('Results for node {}'.format(id_node_for_analysis))
print('{:10} {:10} {:15}'.format('TIME (s)', 'TIME (hrs)', 'PRESSURE'))
report_timestep = en.gettimeparam(proj, en.REPORTSTEP)

while True:
    en.runH(ph=proj)
    t = en.nextH(ph=proj)
    time_s = en.gettimeparam(proj, en.HTIME)
    pressure = en.getnodevalue(
        ph=proj,
        index=index_node_for_analysis + 1,
        property=en.PRESSURE)
    if time_s % report_timestep == 0:
        print('{:<10} {:<10} {:<15}'.format(
            time_s, time_s / (60 * 60), pressure))
    if t <= 0:
        break

# Close simulation
en.closeH(ph=proj)
en.closeQ(ph=proj)


en.saveinpfile(proj, 'outputs/inp.inp')
