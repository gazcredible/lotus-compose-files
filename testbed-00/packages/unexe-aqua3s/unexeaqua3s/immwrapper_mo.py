import unexeaqua3s.IMM_PI_MO
import numpy as np
import pandas as pd
import datetime
import inspect
import os

import unexefiware.base_logger


class IMM_Wrapper():
    def __init__(self):
        self.init()

    def init(self):
        self.results = {'solutions': [], 'diagnostics': [], 'new_solutions': [], 'found_solution': False}

    def do_it(self, fiware_service: str, leakPipeID: str, repair_duration_hours: int, n_solutions: int, logger: unexefiware.base_logger.BaseLogger):
        try:
            self.init()

            # collect epanet model from contextbroker - could rewrite this hardcoded?
            inp_file = os.environ['FILE_PATH'] + os.environ['FILE_VISUALISER_FOLDER'] + '/data/' + fiware_service + '/waternetwork/epanet.inp'
            IMM = unexeaqua3s.IMM_PI_MO.IMM_model(inp_file=inp_file, network_name=fiware_service)

            # Get Leak Node
            leakNodeID = IMM.get_leakNodeID(leakPipeID)

            # identify OperationalPipeIDS - i.e. closed pipe ids
            closed_pipe_ids = ['11']  # this should be scripted to determine which pipes are closed (within IMM_PI.py file)
            prv_pipe_ids = ['57']

            IMM.set_simulation_Parameters(leakNodeID=leakNodeID,
                                          leakPipeID=leakPipeID,
                                          OperationalPipeIDs=closed_pipe_ids,
                                          OperationalPRVIDs=prv_pipe_ids,
                                          repair_sec=repair_duration_hours * 60 * 60)

            # calc pop per node
            IMM.get_pop_per_node(total_population=205000)
            # calc base demand and base velocity scores 48 hours after awarenesstime
            IMM.base_scenario_sim()
            # calc PIs for default pipe repair-leak scenario (i.e. repair pipe at time of awareness)
            IMM.default_repair_scenario()  # need to double check this

            # ALGORITHM PROBLEM SET-UP
            from pymoo.factory import get_algorithm, get_crossover, get_mutation, get_sampling
            from pymoo.optimize import minimize
            from pymoo.core.problem import ElementwiseProblem

            NUM_closed_pipes = len(closed_pipe_ids)
            NUM_closed_pipe_constraints = 2 * NUM_closed_pipes
            NUM_PipeRepair_constraints = 1
            NUM_PRVs = len(prv_pipe_ids)

            class MyProblem(ElementwiseProblem):
                def __init__(self):
                    super().__init__(n_var=6,
                                     n_obj=2,
                                     n_constr=3,
                                     xl=np.array([0, 0, 0, 0, 0, 0]),  # X0: repair start time, X1: open closed pipe, X2: reclose pipe, X3: adjust prv setting X4: prv setting adjust time start, X5:  prv setting adjust time end
                                     xu=np.array([(48 - repair_duration_hours), 47, 48, 4, 47, 48]),
                                     type_var=int
                                     )

                def _evaluate(self, X, out, *args, **kwargs):
                    # Objective functions
                    f1 = IMM.assess_IMM(X)  # Overall IMM PI value
                    f2 = IMM.num_interventions(X)  # Num of interventions
                    # Constraints
                    pipe_repair = X[0] + repair_duration_hours - 48  # <= 0 #pipe must be repaired within 48 hrs
                    closed_pipe1 = X[1] - X[2]  # <= 0 #closing time must occur > opening time
                    prv1 = X[4] - X[5]  # <= 0 #closing time must occur > opening time

                    # overall Constraints (G) and objectives (F)
                    out["G"] = np.column_stack([pipe_repair, closed_pipe1, prv1])
                    out["F"] = np.column_stack([f1, f2])  # Objective Value

            # REPAIR OPERATOR
            # works by eliminating offspring after they've been reproduced but before they've been evaluated by the obj. function
            # i.e. can increase speed and helps avoid getting stuck in local minimum
            from pymoo.core.repair import Repair
            class repair_method(Repair):
                def _do(self, problem, pop, **kwargs):
                    for k in range(len(pop)):
                        x = pop[k].X
                        if x[1] == 0:
                            x[2] = 0  # i.e. if not operative closed pipe, no need to reclose closed pipe
                        if x[3] == 2:  # i.e. if not operating PRVC (2 == original setting), no need to have prv operational times (4 and 5)
                            x[4] = 0
                            x[5] = 0
                    return pop

            # SET INITIAL POPULATION
            # This can help explore local minimums and improve analysis
            X = np.array([[0, 0, 0, 2, 0, 0],  # begin pipe repair right away - nothing else
                          [0, 1, 48, 2, 0, 0],  # & open closed pipe right away
                          [0, 0, 0, 4, 1, 48],  # increase PRV setting to 200%
                          [0, 1, 48, 4, 1, 48],
                          [0, 1, 48, 1, 1, 48],
                          [10, 1, 48, 4, 1, 48],
                          [0, 1, 48, 4, 10, 48]])

            # GENETIC ALGORITHM SETTINGS
            from pymoo.algorithms.moo.nsga2 import NSGA2
            algorithm = NSGA2(
                sampling=X,
                crossover=get_crossover('int_sbx'),
                mutation=get_mutation('int_pm'),
                repair=repair_method(),
                eliminate_duplicates=True)

            # CUSTOMIZED TERMINATION
            # from pymoo.termination.default import DefaultMultiObjectiveTermination
            from pymoo.util.termination.default import MultiObjectiveDefaultTermination
            termination = MultiObjectiveDefaultTermination(
                f_tol=0.0025,
                n_last=5,
                n_max_gen=20
            )

            # #Test analysis
            # X = [0, 0, 0, 2, 0, 0]
            # IMM.assess_IMM(X)
            #
            # print(IMM.num_interventions(X))
            # print(IMM.PI_Results(X))

            # RUN GA
            ga_results = minimize(MyProblem(),
                                  algorithm,
                                  termination=termination,  # ('tol','n_gen', 10),
                                  seed=1,
                                  save_history=True,
                                  # verbose=True #False
                                  verbose=False
                                  )

            # print("Best solution found: %s" % ga_results.X)

            # GET N SOLUTIONS
            def top_n_solutions(res, n):
                IMM_solutions = []
                ga_results = pd.DataFrame(res.X)
                ga_results['interventions'] = res.F[:, 1]
                max_int = int(ga_results['interventions'].max())
                while len(IMM_solutions) < n:
                    counter = 0
                    for i in range((max_int), 0, -1):
                        imm = {}
                        x = ga_results[ga_results.interventions == i]
                        x = x.drop('interventions', axis=1)
                        x = x.iloc[counter]
                        x = x.to_numpy()
                        imm['X'] = x
                        imm['PIs'] = IMM.PI_Results(x)
                        imm['Interventions'] = imm['PIs']['Interventions']
                        del imm['PIs']['Interventions']
                        if len(IMM_solutions) < n:
                            IMM_solutions.append(imm)
                    counter = counter + 1
                return IMM_solutions

            self.top_solutions = top_n_solutions(ga_results, n_solutions)

            self.results['solutions'] = []
            self.results['new_solutions'] = []

            def print_top_solutions(top_solutions, n_solutions, closed_pipe_id, prv_pipe_id):
                for i in range(n_solutions):
                    solution = []
                    solution.append("Solution Number " + str(i + 1))
                    solution.append("\tNumber of Interventions: " + str(top_solutions[i]['Interventions']))
                    solution.append("\tPERFORMANCE INDICATORS")
                    solution.append("\t\tP1 (Number of Customer Minutes with Zero Pressure): " + str(top_solutions[i]['PIs']['PI1_IMM']))
                    solution.append("\t\tP2 (Number of Customer Minutes with Low Pressure (<6m): " + str(top_solutions[i]['PIs']['PI2_IMM']))
                    solution.append("\t\tP3 (Unmet Demand (m3)): " + str(top_solutions[i]['PIs']['PI3_IMM']))
                    solution.append("\t\tP4 (Discoloration Risk Increase Score): " + str(top_solutions[i]['PIs']['PI4_IMM']))
                    solution.append("\t\tP5 (Total Leak Volume (m3): " + str(top_solutions[i]['PIs']['LeakVolume_IMM']))
                    solution.append("\t\tPTotal (Overall Performance Indicator): " + str(top_solutions[i]['PIs']['Total_PI']))
                    solution.append("\tIntervention Steps")
                    solution.append("\t\t Begin pipe repair on leaking Pipe at hour " + str(top_solutions[i]['X'][0]))
                    if top_solutions[i]['X'][1] > 0:
                        solution.append("\t\t Open Closed Pipe_" + str(closed_pipe_id) + " at hour " + str(top_solutions[i]['X'][1]))
                        solution.append("\t\t Reclose Pipe_" + str(closed_pipe_id) + " at " + str(top_solutions[i]['X'][2]))
                    if top_solutions[i]['X'][3] == 0:
                        solution.append("\t\t Close PRV_ " + str(prv_pipe_id) + " at hour " + str(top_solutions[i]['X'][4]))
                    if top_solutions[i]['X'][3] == 1:
                        solution.append("\t\t Reduce PRV_" + str(prv_pipe_id) + " pressure setting by 50%  at hour " + str(top_solutions[i]['X'][4]))
                    if top_solutions[i]['X'][3] == 3:
                        solution.append("\t\t Increase PRV_" + str(prv_pipe_id) + " pressure setting by 50%  at hour " + str(top_solutions[i]['X'][4]))
                    if top_solutions[i]['X'][3] == 4:
                        solution.append("\t\t Increase PRV_" + str(prv_pipe_id) + " pressure setting by 100%  at hour " + str(top_solutions[i]['X'][4]))
                    if top_solutions[i]['X'][3] != 2:
                        solution.append("\t\t Return PRV_" + str(prv_pipe_id) + " to original setting at hour " + str(top_solutions[i]['X'][5]))

                    new_solution = {}
                    new_solution['P1'] = int(top_solutions[i]['PIs']['PI1_IMM']) #zero pressure
                    new_solution['P2'] = int(top_solutions[i]['PIs']['PI2_IMM']) #low pressure
                    new_solution['P3'] = int(top_solutions[i]['PIs']['PI3_IMM']) #unmet demand
                    new_solution['P4'] = int(top_solutions[i]['PIs']['PI4_IMM']) #discoloration
                    new_solution['P5'] = int(top_solutions[i]['PIs']['LeakVolume_IMM']) #leak volume
                    new_solution['PTOTAL'] = int(top_solutions[i]['PIs']['Total_PI'])

                    new_solution['STEPS'] = []

                    new_solution['STEPS'].append('Begin pipe repair on leaking Pipe at hour ' + str(top_solutions[i]['X'][0]))

                    solution.append('Begin pipe repair on leaking Pipe at hour ' + str(top_solutions[i]['X'][0]))
                    if top_solutions[i]['X'][1] > 0:
                        new_solution['STEPS'].append("Open Closed Pipe " + str(closed_pipe_id[0]) + " at hour " + str(top_solutions[i]['X'][1]))
                        new_solution['STEPS'].append("Reclose Pipe " + str(closed_pipe_id[0]) + " at hour " + str(top_solutions[i]['X'][2]))
                    if top_solutions[i]['X'][3] == 0:
                        new_solution['STEPS'].append("Close PRV  " + str(prv_pipe_id[0]) + " at hour " + str(top_solutions[i]['X'][4]))
                    if top_solutions[i]['X'][3] == 1:
                        new_solution['STEPS'].append("Reduce PRV " + str(prv_pipe_id[0]) + " pressure setting by 50%  at hour " + str(top_solutions[i]['X'][4]))
                    if top_solutions[i]['X'][3] == 3:
                        new_solution['STEPS'].append("Increase PRV " + str(prv_pipe_id[0]) + " pressure setting by 50%  at hour " + str(top_solutions[i]['X'][4]))
                    if top_solutions[i]['X'][3] == 4:
                        new_solution['STEPS'].append("Increase PRV " + str(prv_pipe_id[0]) + " pressure setting by 100%  at hour " + str(top_solutions[i]['X'][4]))
                    if top_solutions[i]['X'][3] != 2:
                        new_solution['STEPS'].append("Return PRV " + str(prv_pipe_id[0]) + " to original setting at hour " + str(top_solutions[i]['X'][5]))

                    solution.append('<br>')

                    fixed_solution = []

                    for line in solution:
                        fixed_solution.append(line.replace('\t', '...'))

                    self.results['solutions'].append(fixed_solution)
                    self.results['new_solutions'].append(new_solution)

            print_top_solutions(self.top_solutions, n_solutions, closed_pipe_ids, prv_pipe_ids)

            self.results['found_solution'] = True

        except Exception as e:
            logger.exception(inspect.currentframe(), e)

            if 'diagnostics' in self.results:
                self.results['diagnostics'].append('Epic fail at line 10')
                self.results['diagnostics'].append(logger.exception_to_string(e))

            self.results['found_solution'] = False

