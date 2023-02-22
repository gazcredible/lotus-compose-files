import os
import time

from epanet_fiware.epanetmodel import EPAnetModel, SimStatus
import epanet_fiware.enumerations as enu


def main():
    # epanet_inp_file = 'inputs/WIS309_names_shortened_wgs84.inp'
    epanet_inp_file = 'inputs/d-town.inp'
    output_path = 'outputs'
    network_name = os.path.splitext(os.path.basename(epanet_inp_file))[0]
    model = EPAnetModel(network_name=network_name,
                        filename=epanet_inp_file,
                        output_path=output_path)
    model.set_time_param(
            param=enu.TimeParams.Duration,
            # value=7 * 24 * 60 * 60)
            value=2 * 60 * 60)

    # Run step-by-step simulation
    sim_start = int(time.time())
    model.simulate_init()
    while model.simulation_status in [
            SimStatus.initialised, SimStatus.started]:
        model.simulate_step()
    sim_duration = int(time.time()) - sim_start
    print('Step-by-step with clear_previous_data=False sim_duration =',
          sim_duration)

    # Run whole simulation
    sim_start = int(time.time())
    model.simulate_full()
    sim_duration = int(time.time()) - sim_start
    print('Full sim_duration =', sim_duration)


if __name__ == "__main__":
    main()
