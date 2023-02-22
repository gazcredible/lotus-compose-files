import unexeaqua3s.IMM_PI
import numpy as np
import datetime
import inspect
import os

class IMM_Wrapper():
    def __init__(self):
        pass

    def do_it(self, fiware_service, leakPipeID, repair_duration, logger):
        try:
            self.results = []

            # collect epanet model from contextbroker - could rewrite this hardcoded?
            inp_file = os.environ['FILE_PATH'] + 'visualiser/data/' + fiware_service + '/waternetwork/epanet.inp'
            # inp_file = inp_file_location(fiware_wrapper, fiware_service)
            IMM = unexeaqua3s.IMM_PI.IMM_model(inp_file=inp_file, network_name=fiware_service)

            # Get Leak Node
            leakNodeID = IMM.get_leakNodeID(leakPipeID)

            # Get RepairDuration Int
            repair_duration_int = int(''.join(char for char in repair_duration if char.isdigit()))
            # identify OperationalPipeIDS - i.e. closed pipe ids
            closed_pipe_ids = ['37']  # this should be scripted to determine which pipes are closed (within IMM_PI.py file)

            # %% Declare leaknodeID, LeakPipeID, awarenesstime, etc.
            # leakNodeID = '96'  # these can be adjusted
            # leakPipeID = '38'

            IMM.set_simulation_Parameters(leakNodeID=leakNodeID,
                                          leakPipeID=leakPipeID,
                                          OperationalPipeIDs=closed_pipe_ids,
                                          repair_sec=repair_duration_int * 60 * 60)

            # calc pop per node
            IMM.get_pop_per_node(total_population=205000)
            # calc base demand and base velocity scores 48 hours after awarenesstime
            IMM.base_scenario_sim()
            # calc PIs for default pipe repair-leak scenario (i.e. repair pipe at time of awareness)
            IMM.default_repair_scenario()  # need to double check this

            # run Evolutionary Optimizer
            # %%Calc Objective function
            # input: only the X vector
            # run and calc PIS by compairing to PIS from default repair scenario
            # x array:
            # x0: repair start time (0-48)
            # x1: closed pipe 1: opening time (0-48)
            # x2: closed pipe 1: closing time (0-48)

            # x=np.array([0,1,47])
            # IMM.assess_IMM(x)

            # %% GA Set-up
            from pymoo.factory import get_algorithm, get_crossover, get_mutation, get_sampling
            from pymoo.optimize import minimize
            from pymoo.core.problem import ElementwiseProblem

            NUM_closed_pipes = 1
            NUM_closed_pipe_constraints = 2 * NUM_closed_pipes
            NUM_PipeRepair_constraints = 1

            class MyProblem(ElementwiseProblem):
                def __init__(self):
                    super().__init__(n_var=1 + NUM_closed_pipes * 2,
                                     n_obj=1,
                                     n_constr=NUM_PipeRepair_constraints + NUM_closed_pipe_constraints,
                                     xl=0,
                                     xu=48,
                                     type_var=int
                                     )

                def _evaluate(self, X, out, *args, **kwargs):
                    # Objective and Constraint functions
                    out["F"] = -IMM.assess_IMM(X)  # Objective Value
                    # pipe_repair_1 = -X[0]+0.5 #<= 0 #pipe repair time must be greater than 0
                    pipe_repair_2 = X[0] + repair_duration_int - 48  # <= 0 #pipe must be repaired within 48 hrs
                    closedPipe1_1 = -X[1] * 100 + X[2]  # <=0 #if pipe 1 start time = 0, then pipe 1 endtime = 0
                    closedPipe1_2 = X[1] - X[2]  # <= 0 #closing time must occur > opening time
                    out["G"] = np.column_stack([pipe_repair_2, closedPipe1_1, closedPipe1_2])

            # %% Solution
            start_time = datetime.datetime.now()
            start_hour = start_time.replace(microsecond=0, second=0, minute=0)

            method = get_algorithm("ga",
                                   pop_size=6,
                                   sampling=get_sampling("int_random"),
                                   crossover=get_crossover("int_sbx", prob=1.0, eta=3.0),
                                   mutation=get_mutation("int_pm", eta=3.0),
                                   eliminate_duplicates=True,
                                   )

            res = minimize(MyProblem(),
                           method,
                           termination=('n_gen', 11),
                           seed=1,
                           save_history=True,
                           verbose=False
                           )

            # print("Best solution found: %s" % res.X)
            self.results = []
            self.results.append("IMM Steps:")
            if int(res.X[1]) > 0:
                if int(res.X[0]) <= int(res.X[1]):
                    self.results.append("1. Begin repair by closing leaky pipe (Pipe ID:" + leakPipeID + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[0]))))
                    if (int(res.X[0]) + repair_duration_int) < int(res.X[1]):
                        self.results.append("2. Finish pipe repair and reopen repaired pipe (Pipe ID:" + leakPipeID + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[0]) + repair_duration_int)))
                        self.results.append("3. Open pipe (Pipe ID:" + closed_pipe_ids[0] + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[1]))))
                        self.results.append("4. Close pipe (Pipe ID:" + closed_pipe_ids[0] + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[2]))))
                    else:
                        self.results.append("2. Open pipe (Pipe ID:" + closed_pipe_ids[0] + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[1]))))
                        self.results.append("3. Finish pipe repair and reopen repaired pipe (Pipe ID:" + leakPipeID + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[0]) + repair_duration_int)))
                        self.results.append("4. Close pipe (Pipe ID:" + closed_pipe_ids[0] + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[2]))))
                else:
                    self.results.append("1. Open pipe (Pipe ID:" + closed_pipe_ids[0] + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[1]))))
                    self.results.append("2. Begin repair by closing leaky pipe (Pipe ID:" + leakPipeID + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[0]))))
                    self.results.append("3. Finish pipe repair and reopen repaired pipe (Pipe ID:" + leakPipeID + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[0]) + repair_duration_int)))
                    self.results.append("4. Close pipe (Pipe ID:" + closed_pipe_ids[0] + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[2]))))
            if int(res.X[1]) == 0:
                self.results.append("1. Begin repair by closing leaky pipe (Pipe ID:" + leakPipeID + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[0]))))
                self.results.append("2. Finish pipe repair and reopen repaired pipe (Pipe ID:" + leakPipeID + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[0]) + repair_duration_int)))

            # print("Function value: %s" % res.F)
            # print("Constraint violation: %s" % res.CV)

            # simulationTime = datetime.datetime.now() - start_time
            # print("Total training time: " + str(simulationTime))
        except Exception as e:
            self.results.append('Epic fail at line 10')
            self.results.append( logger.exception_to_string(e) )
            logger.exception(inspect.currentframe(), e)
