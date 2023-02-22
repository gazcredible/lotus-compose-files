import os
import time

import unexeaqua3s.fiwareresources
import unexefiware.base_logger
import threading
import inspect

import epanet.toolkit as en
import epanet_fiware.ngsi_ld_writer

import unexeaqua3s.immwrapper_mo

import blueprints.debug

IMMInstance_Idle = 'idle'
IMMInstance_Busy = 'busy'
IMMInstance_Done = 'complete'

class IMMInstance():
    def __init__(self, pilot_name, logger):
        self.current_state = IMMInstance_Idle
        self.pilot_name = pilot_name

        self.link_labels = []
        self.running = True

        self.logger = logger

        self.actions = []
        self.thread = None

        self.new_results = {}

    def _process_thread(self):
        if self.logger:
            try:
                self.logger.log(inspect.currentframe(),'Starting IMM Process for: ' + self.pilot_name)

                if False: #GARETH - Fudge IMM results here
                    for i in range(0,5):
                        self.actions.append('Do step:' +str(i))

                    self.new_results['solutions'] = [['Solution Number 1', '...Number of Interventions: 2', '...PERFORMANCE INDICATORS', '......P1 (Number of Customer Minutes with Zero Pressure): 0', '......P2 (Number of Customer Minutes with Low Pressure (<6m): 0', '......P3 (Unmet Demand (m3)): 0', '......P4 (Discoloration Risk Increase Score): 8', '......P5 (Total Leak Volume (m3): 391.2289270840012', '......PTotal (Overall Performance Indicator): 399.2289270840012', '...Intervention Steps', '...... Begin pipe repair on leaking Pipe at hour 0', "...... Open Closed Pipe_['11'] at hour 1", "...... Reclose Pipe_['11'] at 48", 'Begin pipe repair on leaking Pipe at hour 0', '<br>'],
                                         ['Solution Number 2', '...Number of Interventions: 1', '...PERFORMANCE INDICATORS', '......P1 (Number of Customer Minutes with Zero Pressure): 0', '......P2 (Number of Customer Minutes with Low Pressure (<6m): 0', '......P3 (Unmet Demand (m3)): 54.03859127999749', '......P4 (Discoloration Risk Increase Score): 4', '......P5 (Total Leak Volume (m3): 391.2289270840012', '......PTotal (Overall Performance Indicator): 449.2675183639987', '...Intervention Steps', '...... Begin pipe repair on leaking Pipe at hour 0', 'Begin pipe repair on leaking Pipe at hour 0', '<br>'],
                                         ['Solution Number 3', '...Number of Interventions: 2', '...PERFORMANCE INDICATORS', '......P1 (Number of Customer Minutes with Zero Pressure): 0', '......P2 (Number of Customer Minutes with Low Pressure (<6m): 0', '......P3 (Unmet Demand (m3)): 0', '......P4 (Discoloration Risk Increase Score): 8', '......P5 (Total Leak Volume (m3): 391.2289270840012', '......PTotal (Overall Performance Indicator): 399.2289270840012', '...Intervention Steps', '...... Begin pipe repair on leaking Pipe at hour 0', "...... Open Closed Pipe_['11'] at hour 1", "...... Reclose Pipe_['11'] at 48", 'Begin pipe repair on leaking Pipe at hour 0', '<br>'],
                                         ['Solution Number 4', '...Number of Interventions: 1', '...PERFORMANCE INDICATORS', '......P1 (Number of Customer Minutes with Zero Pressure): 0', '......P2 (Number of Customer Minutes with Low Pressure (<6m): 0', '......P3 (Unmet Demand (m3)): 54.03859127999749', '......P4 (Discoloration Risk Increase Score): 4', '......P5 (Total Leak Volume (m3): 391.2289270840012', '......PTotal (Overall Performance Indicator): 449.2675183639987', '...Intervention Steps', '...... Begin pipe repair on leaking Pipe at hour 0', 'Begin pipe repair on leaking Pipe at hour 0', '<br>'],
                                         ['Solution Number 5', '...Number of Interventions: 2', '...PERFORMANCE INDICATORS', '......P1 (Number of Customer Minutes with Zero Pressure): 0', '......P2 (Number of Customer Minutes with Low Pressure (<6m): 0', '......P3 (Unmet Demand (m3)): 0', '......P4 (Discoloration Risk Increase Score): 8', '......P5 (Total Leak Volume (m3): 391.2289270840012', '......PTotal (Overall Performance Indicator): 399.2289270840012', '...Intervention Steps', '...... Begin pipe repair on leaking Pipe at hour 0', "...... Open Closed Pipe_['11'] at hour 1", "...... Reclose Pipe_['11'] at 48", 'Begin pipe repair on leaking Pipe at hour 0', '<br>']],
                    self.new_results['diagnostics'] = ['Epic fail at line 10','bad things occured']
                    self.new_results['new_solutions'] = [{'P1': 0, 'P2': 0, 'P3': 0, 'P4': 8, 'P5': 391, 'PTOTAL': 399, 'STEPS': ['Begin pipe repair on leaking Pipe at hour 0', 'Open Closed Pipe 11 at hour 1', 'Reclose Pipe 11 at hour 48']},
                                             {'P1': 0, 'P2': 0, 'P3': 54, 'P4': 4, 'P5': 391, 'PTOTAL': 449, 'STEPS': ['Begin pipe repair on leaking Pipe at hour 0']},
                                             {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 8, 'P5': 391, 'PTOTAL': 399, 'STEPS': ['Begin pipe repair on leaking Pipe at hour 0', 'Open Closed Pipe 11 at hour 1', 'Reclose Pipe 11 at hour 48']},
                                             {'P1': 0, 'P2': 0, 'P3': 54, 'P4': 4, 'P5': 391, 'PTOTAL': 449, 'STEPS': ['Begin pipe repair on leaking Pipe at hour 0']},
                                             {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 8, 'P5': 391, 'PTOTAL': 399, 'STEPS': ['Begin pipe repair on leaking Pipe at hour 0', 'Open Closed Pipe 11 at hour 1', 'Reclose Pipe 11 at hour 48']}
                                             ]
                    self.new_results['found_solution'] = False

                else:
                    imm = unexeaqua3s.immwrapper_mo.IMM_Wrapper()
                    imm.do_it(fiware_service=self.pilot_name, leakPipeID=self.selected_pipe, repair_duration_hours=self.repair_duration, n_solutions=self.max_number_of_solutions, logger=self.logger)

                    if imm.results['diagnostics'] != []:
                        for step in imm.results['diagnostics']:
                            self.actions.append(step)
                    else:
                        if imm.results['solutions']:
                            for solution in imm.results['solutions']:
                                for step in solution:
                                    self.actions.append(step)
                        else:
                            self.actions.append('Failed to work')

                    self.new_results['solutions'] = imm.results['new_solutions']
                    self.new_results['diagnostics'] = imm.results['diagnostics']
                    self.new_results['found_solution'] = imm.results['found_solution']



            except Exception as e:
                self.current_state = IMMInstance_Done
                self.actions.append('Failed to work:' +str(e))
                self.logger.exception(inspect.currentframe(),e)

                self.new_results['solutions'] = []
                self.new_results['diagnostics'] = [self.logger.exception_to_string(e)]
                self.new_results['found_solution'] = False

        self.thread = None
        self.logger.log(inspect.currentframe(), 'Finished IMM Process for: ' + self.pilot_name)
        self.current_state = IMMInstance_Done

    def init(self):
        self.current_state = IMMInstance_Idle
        self.epanet_model = None
        self.selected_pipe = None
        self.max_number_of_solutions = None

        if self.logger:
            self.logger.log(inspect.currentframe(),'Setup IMM for: ' + self.pilot_name)

    def build_from_epanet(self,epanet_model):

        self.epanet_model = epanet_model
        self.dump_stuff()

    def dump_stuff(self):

        proj = self.epanet_model.epanetmodel.proj_for_simulation
        self.link_labels = []

        num_links = en.getcount(ph=proj, object=en.LINKCOUNT)
        for link in range(num_links):
            index = link + 1
            link_type = en.getlinktype(ph=proj, index=index)
            if link_type in [en.PIPE, en.CVPIPE]:
                common_data = epanet_fiware.ngsi_ld_writer._get_link_common_data(proj, index)
                self.link_labels.append(common_data.Name)

        self.link_labels.sort()

    def start(self, selected_pipe, repair_duration, max_number_of_solutions):
        if self.current_state == IMMInstance_Idle:
            self.selected_pipe = selected_pipe
            self.current_state = IMMInstance_Busy
            self.repair_duration = repair_duration
            self.max_number_of_solutions = max_number_of_solutions
            self.actions = []



            self.thread = threading.Thread(target=self._process_thread, args='')
            self.thread.start()

            return True

        return False

    def reset(self):
        if self.current_state != IMMInstance_Idle:
            self.current_state = IMMInstance_Idle
            self.actions = []

            if self.thread != None:
                self.thread = None


    def state(self):
        return self.current_state


class IMMProcessor():
    def __init__(self):
        self.pilots = {}
        self.logger = None

    def init(self, logger = None):
        # each pilot needs a processor to handle stuff
        # have the epanet model for IMMing
        # and current state
        self.logger = logger

        pilots = os.environ['PILOTS'].split(',')
        for pilot in pilots:
            self.pilots[pilot] = IMMInstance(pilot, self.logger)
            self.pilots[pilot].init()

    def get_links(self, access_token):
        if access_token in self.pilots:
            return self.pilots[access_token].link_labels

        return []

    def get_instructions(self, access_token):
        return self.pilots[access_token].actions

    def start(self, access_token, selected_pipe:str, repair_duration:str,max_number_of_solutions:str):
        #GARETH - convert repair duration into seconds?
        #       - convert max_number_of_solutions in to int?

        repair_duration_int = int(''.join(char for char in repair_duration if char.isdigit()))
        max_solution_int = int(max_number_of_solutions)

        #max_solution_int = 3
        #selected_pipe = '14'
        #repair_duration_int = 4
        #max_solution_int = 3

        return self.pilots[access_token].start(selected_pipe, repair_duration_int, max_solution_int)

    def reset(self, access_token):
        return self.pilots[access_token].reset()

    def pilot_state(self, access_token):
        return self.pilots[access_token].state()

    def load_epanet(self, access_token, epanet_model):
        self.pilots[access_token].build_from_epanet(epanet_model)

    def has_epanet(self, access_token):
        return self.pilots[access_token].epanet_model is not None

    def get_client_data(self, access_token):
        data = {}
        try:
            data['status'] = self.pilot_state(access_token)
            data['pipe_List'] = self.get_links(access_token)
            data['instructions'] = self.get_instructions(access_token)
            data['repair_duration'] = ['1hr','2hrs','3hrs','4hrs','5hrs','6hrs','7hrs','8hrs','9hrs', '10hrs', '11hrs', '12hrs']
            data['number_of_solutions'] = ['1','2','3','4','5']

            data['new_results'] = self.pilots[access_token].new_results
        except Exception as e:
            blueprints.debug.servicelog.exception(inspect.currentframe(),e)

        return data
