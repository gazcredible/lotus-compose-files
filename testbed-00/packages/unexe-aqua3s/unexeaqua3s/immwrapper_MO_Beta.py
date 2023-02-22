import epanet_fiware.epanetmodel
import epanet_fiware.enumerations as enu
import epanet_fiware.epanet_outfile_handler as outfile_handler
import epanet.toolkit as en
import pandas as pd
import numpy as np
import datetime
from typing import Optional
import multiprocess as mp
import unexeaqua3s.IMM_PI_MO

#%%Set-up IMM class
np.random.seed()
repair_duration_int = 4
#%% TRIESTE
inp_file = '/home/brett/Desktop/epanet.inp'
network_name = 'Trieste_11Closed'
closed_pipe_ids = ['11']
prv_pipe_ids =['57']
test = unexeaqua3s.IMM_PI_MO.IMM_model(inp_file=inp_file, network_name=network_name)
#Declare leaknodeID, LeakPipeID, awarenesstime, etc.
test.set_simulation_Parameters(leakNodeID = '79',
                               leakPipeID='14',
                               OperationalPipeIDs = closed_pipe_ids,
                               OperationalPRVIDs = prv_pipe_ids,
                               repair_sec=repair_duration_int * 60 * 60)

#%% GT
inp_file = '/home/brett/Desktop/epanet_GT_rev4b.inp'
network_name = 'GT_Rev4b'
closed_pipe_ids = ['TestPipe']
prv_pipe_ids =['3092019_7444.3092019_10244.1', '3092019_10357.3092019_2270.1', '3092019_2221.3092019_10375.1', '3092019_10493.3092019_2496.1']
test = unexeaqua3s.IMM_PI_MO.IMM_model(inp_file=inp_file, network_name=network_name)
#Declare leaknodeID, LeakPipeID, awarenesstime, etc.
test.set_simulation_Parameters(leakNodeID = '3092019_10352',
                               leakPipeID='3092019_2256.3092019_2258.1',
                               OperationalPipeIDs = closed_pipe_ids,
                               OperationalPRVIDs = prv_pipe_ids,
                               repair_sec=repair_duration_int * 60 * 60)
#%%Initial Analysis
# calc pop per node
test.get_pop_per_node(total_population=12600)#205000)
# calc base demand and base velocity scores 48 hours after awarenesstime
test.base_scenario_sim()
# calc PIs for default pipe repair-leak scenario (i.e. repair pipe at time of awareness)
test.default_repair_scenario()  # need to double check this


#%%
X = [0,0,0,0,0,0]
X = [0,0,0,20,47,48]
X = [6,15,48,0,15,24,0,15,24,0,15,24,0,15,24]
X = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
X = [0,3,25,2,12,47,4,19,32,4,10,31,3,19,44]


print(test.num_interventions(X))
print(test.PI_Results(X))
# %% MULTI OBJ - GA Set-up
from pymoo.factory import get_algorithm, get_crossover, get_mutation, get_sampling
from pymoo.optimize import minimize
from pymoo.core.problem import ElementwiseProblem

NUM_closed_pipes = len(closed_pipe_ids)
NUM_closed_pipe_constraints = 2 * NUM_closed_pipes
NUM_PipeRepair_constraints = 1
NUM_PRVs = len(prv_pipe_ids)


class MyProblem(ElementwiseProblem):
    def __init__(self):
        super().__init__(n_var=15,
                         n_obj=2,
                         n_constr=6,
                         xl=np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]),
                         xu=np.array([(48-repair_duration_int),47,48,4,47,48,4,47,48,4,47,48,4,47,48]),
                         type_var=int
                         )

    def _evaluate(self, X, out, *args, **kwargs):
        # Objective functions
        f1 = test.assess_IMM(X)#+0.00000001*test.num_interventions(X)
        f2 = test.num_interventions(X)
        # Constraints
        pipe_repair = X[0] + repair_duration_int - 48  # <= 0 #pipe must be repaired within 48 hrs
        closed_pipe1 = X[1] - X[2]  # <= 0 #closing time must occur > opening time
        #closed_pipe2 = -X[1] * 100 + X[2]#-X[1]*100 - X[2] #if X[1] ==0, X[2] == 0
        prv1 = X[4] - X[5]  # <= 0 #closing time must occur > opening time
        prv2 = X[7] - X[8]  # <= 0 #closing time must occur > opening time
        prv3 = X[10] - X[11]  # <= 0 #closing time must occur > opening time
        prv4 = X[13] - X[14]  # <= 0 #closing time must occur > opening time

        #overall Constraings (G) and objectives (F)
        out["G"] = np.column_stack([pipe_repair, closed_pipe1, prv1, prv2, prv3, prv4])
        out["F"] = np.column_stack([f1, f2])  # Objective Value

#%% Algorithm - without Repair
start_time = datetime.datetime.now()

method = get_algorithm("nsga2",
                       pop_size=20,
                       # n_offsprings=10,
                       sampling=get_sampling("int_random"),
                       crossover=get_crossover("int_sbx"), #, prob=1.0, eta=0.9),
                       mutation=get_mutation("int_pm"),#, eta=10.0),
                       eliminate_duplicates=True,
                       )

#%% Solve Solution - without repair
res = minimize(MyProblem(),
               method,
               termination=('n_gen', 6),
               seed=1,
               save_history=True,
               verbose=True
               )

print("Best solution found: %s" % res.X)

#%% Repair operator:
#repair operator works by eliminating offspring after they've been reproduced but before they've been evaluated by the obj. function
from pymoo.core.repair import Repair
class repair_method(Repair):
    def _do(self, problem, pop, **kwargs):
        for k in range(len(pop)):
            x = pop[k].X
            if x[1] == 0:
                x[2] = 0
            if x[3] == 2:
                x[4] = 0
                x[5] = 0
            if x[6] == 2:
                x[7] = 0
                x[8] = 0
            if x[9] == 2:
                x[10] = 0
                x[11] = 0
            if x[12] == 2:
                x[13] = 0
                x[14] = 0
        return pop

#%% Run Analysis - With Repair
#initial sampling - i.e. Biased initiation
X = np.array([[0,0,0,2,0,0,2,0,0,2,0,0,2,0,0],
             [0,1,48,2,0,0,2,0,0,2,0,0,2,0,0],
             [0,0,0,4,1,48,2,0,0,2,0,0,2,0,0],
             [0,0,0,2,0,0,4,1,48,2,0,0,2,0,0],
             [0,0,0,2,0,0,2,0,0,4,1,48,2,0,0],
             [0,0,0,2,0,0,2,0,0,2,0,0,4,1,48],
             [0,1,48,4,1,48,2,0,0,2,0,0,2,0,0],
             [0,1,48,4,1,48,4,1,48,2,0,0,2,0,0],
             [0,1,48,4,1,48,4,1,48,4,1,48,2,0,0],
             [0,1,48,4,1,48,4,1,48,4,1,48,4,1,48]])


from pymoo.algorithms.moo.nsga2 import NSGA2
algorithm = NSGA2(#pop_size=50,
                  sampling = X,#get_sampling('int_random'),
                  crossover = get_crossover('int_sbx'),
                  mutation = get_mutation('int_pm'),
                  repair = repair_method(),
                  eliminate_duplicates = True)

# algorithm = get_algorithm("nsga2",
#                           pop_size = 50,
#                           sampling = get_sampling('int_random'),
#                           crossover = get_crossover('int_sbx'),
#                           mutation = get_mutation('int_pm'),
#                           repair = repair_method(),
#                           eliminate_duplicates = True)

#Customized Terminiation
from pymoo.util.termination.default import MultiObjectiveDefaultTermination

termination = MultiObjectiveDefaultTermination(
    f_tol = 0.0025,
    n_last = 5,
    n_max_gen = 20
)

res = minimize(MyProblem(),
               algorithm,
               termination = termination,#('tol','n_gen', 10),
               seed=1,
               save_history=True,
               verbose=True
               )

print("Best solution found: %s" % res.X)

#%% Get n solutions
def top_n_solutions(res,n):
    IMM_solutions = []
    results = pd.DataFrame(res.X)
    results['interventions'] = res.F[:, 1]
    max_int = int(results['interventions'].max())
    while len(IMM_solutions) < n:
        counter = 0
        for i in range((max_int), 0, -1):
            imm = {}
            x = results[results.interventions == i]
            x = x.drop('interventions', axis=1)
            x = x.iloc[counter]
            x = x.to_numpy()
            imm['X'] = x
            imm['PIs'] = test.PI_Results(x)
            if len(IMM_solutions) < n:
                IMM_solutions.append(imm)
        counter = counter + 1
    return IMM_solutions

#%% get n solutions example:
imm_solutions = top_n_solutions(res,5)

#%%
#get max value from G column 2
# start from max value and work your way down grabbing index of first one
maxInt = np.amax(res.F, axis =0)[1]
a = (np.where(res.F== 4))

#%%
#convert solution list to panda dataframe
#add # of intervention column to pd
#for each



def get_n_solutions(n, res):
    IMM_solutions = []
    default_repair = {}
    default_repair['X'] = np.array([0, 0, 0])
    default_repair['PIs'] = test.PI_results['default_repair']
    IMM_solutions.append(default_repair)



    if n > len(res.pop): #if n greater than pop size return only pop size
        n = len(res.pop)
    for i in range(n):
        imm= {}
        imm['X'] = res.history[-1].pop[i].X
        imm['PIs'] = test.PI_Results(res.history[-1].pop[i].X)
        IMM_solutions.append(imm)
    return IMM_solutions

 #%%Scatter plot of pareto front
from pymoo.visualization.scatter import Scatter
plot = Scatter()
plot.add(res.F)
plot.show()

#%% Convergence Graph
import numpy as np
import matplotlib.pyplot as plt

n_evals = np.array([e.evaluator.n_eval for e in res.history])
opt = np.array([e.opt[0].F for e in res.history])

plt.title("Convergence")
plt.plot(n_evals, opt, "--")
plt.yscale("log")
plt.show()

# print("Function value: %s" % res.F)
# print("Constraint violation: %s" % res.CV)
#
# simulationTime = datetime.datetime.now() - start_time
# print("Total training time: " + str(simulationTime))
#
# #%% Visualization
# from pymoo.visualization.scatter import Scatter
# from pymoo.factory import get_problem, get_reference_directions
# ref_dirs = get_reference_directions("uniform", 3, n_partitions=12)
# plot = Scatter()
# plot.add(res.F)
# plot.show()
# %% Single Objective - GA
import unexeaqua3s.IMM_PI #single objective method
test = unexeaqua3s.IMM_PI.IMM_model(inp_file=inp_file, network_name=network_name)
#Declare leaknodeID, LeakPipeID, awarenesstime, etc.
test.set_simulation_Parameters(leakNodeID = '79',
                               leakPipeID='14',
                               OperationalPipeIDs = closed_pipe_ids,
                               OperationalPRVIDs = prv_pipe_ids,
                               repair_sec=repair_duration_int * 60 * 60)

test.get_pop_per_node(total_population=205000)
test.base_scenario_sim()
test.default_repair_scenario()  # need to double check this
print(test.PI_Results([0,1,10,11,10,20]))
#%%
from pymoo.factory import get_algorithm, get_crossover, get_mutation, get_sampling
from pymoo.optimize import minimize
from pymoo.core.problem import ElementwiseProblem

NUM_closed_pipes = len(closed_pipe_ids)
NUM_closed_pipe_constraints = 2 * NUM_closed_pipes
NUM_PipeRepair_constraints = 1
NUM_PRVs = len(prv_pipe_ids)

class MyProblem(ElementwiseProblem):
    def __init__(self):
        super().__init__(n_var=1 + NUM_closed_pipes * 2 + NUM_PRVs*3,
                         n_obj=1,
                         n_constr=NUM_PipeRepair_constraints + NUM_closed_pipe_constraints + NUM_PRVs*3,
                         xl=0,
                         xu=48,
                         type_var=int
                         )

    def _evaluate(self, X, out, *args, **kwargs):
        # Objective functions
        out["F"] = -test.assess_IMM(X)
        # Constraints
        # pipe_repair_1 = -X[0]+0.5 #<= 0 #pipe repair time must be greater than 0
        pipe_repair_2 = X[0] + repair_duration_int - 48  # <= 0 #pipe must be repaired within 48 hrs
        closedPipe1_1 = -X[1] * 100 + X[2]  # <=0 #if pipe 1 start time = 0, then pipe 1 endtime = 0
        closedPipe1_2 = X[1]+1 - X[2]  # <= 0 #closing time must occur > opening time
        prv_adjustment = X[3] - 20 #prv adjustment must be between 0-20 (20 means original setting * 200%, 1 means original setting *10%)
        prv_1 = -X[4] * 100 + X[5]  # <=0 #if pipe 1 start time = 0, then pipe 1 endtime = 0
        prv_2 = X[4]+1 - X[5]  # <= 0 #closing time must occur > opening time
        #overall Constraings (G) and objectives (F)
        out["G"] = np.column_stack([pipe_repair_2, closedPipe1_1, closedPipe1_2, prv_adjustment, prv_1, prv_2])

#%%
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

#%%
def get_n_solutions(n, res):
    IMM_solutions = []
    default_repair = {}
    default_repair['X'] = np.array([0, 0, 0])
    default_repair['PIs'] = test.PI_results['default_repair']
    IMM_solutions.append(default_repair)

    if n > len(res.pop): #if n greater than pop size return only pop size
        n = len(res.pop)
    for i in range(n):
        imm= {}
        imm['X'] = res.history[-1].pop[i].X
        imm['PIs'] = test.PI_Results(res.history[-1].pop[i].X)
        IMM_solutions.append(imm)
    return IMM_solutions

#%%
a = get_n_solutions(4,res)






# # print("Best solution found: %s" % res.X)
# self.results = []
# self.results.append("IMM Steps:")
# if int(res.X[1]) > 0:
#     if int(res.X[0]) <= int(res.X[1]):
#         self.results.append("1. Begin repair by closing leaky pipe (Pipe ID:" + leakPipeID + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[0]))))
#         if (int(res.X[0]) + repair_duration_int) < int(res.X[1]):
#             self.results.append("2. Finish pipe repair and reopen repaired pipe (Pipe ID:" + leakPipeID + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[0]) + repair_duration_int)))
#             self.results.append("3. Open pipe (Pipe ID:" + closed_pipe_ids[0] + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[1]))))
#             self.results.append("4. Close pipe (Pipe ID:" + closed_pipe_ids[0] + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[2]))))
#         else:
#             self.results.append("2. Open pipe (Pipe ID:" + closed_pipe_ids[0] + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[1]))))
#             self.results.append("3. Finish pipe repair and reopen repaired pipe (Pipe ID:" + leakPipeID + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[0]) + repair_duration_int)))
#             self.results.append("4. Close pipe (Pipe ID:" + closed_pipe_ids[0] + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[2]))))
#     else:
#         self.results.append("1. Open pipe (Pipe ID:" + closed_pipe_ids[0] + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[1]))))
#         self.results.append("2. Begin repair by closing leaky pipe (Pipe ID:" + leakPipeID + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[0]))))
#         self.results.append("3. Finish pipe repair and reopen repaired pipe (Pipe ID:" + leakPipeID + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[0]) + repair_duration_int)))
#         self.results.append("4. Close pipe (Pipe ID:" + closed_pipe_ids[0] + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[2]))))
# if int(res.X[1]) == 0:
#     self.results.append("1. Begin repair by closing leaky pipe (Pipe ID:" + leakPipeID + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[0]))))
#     self.results.append("2. Finish pipe repair and reopen repaired pipe (Pipe ID:" + leakPipeID + ") at " + str(start_hour + datetime.timedelta(hours=int(res.X[0]) + repair_duration_int)))

# print("Function value: %s" % res.F)
# print("Constraint violation: %s" % res.CV)

# simulationTime = datetime.datetime.now() - start_time
# print("Total training time: " + str(simulationTime))

#%%
start_time = datetime.datetime.now()

method = get_algorithm("nsga3",
                       pop_size=40,
                       n_offsprings=10,
                       sampling=get_sampling("int_random"),
                       crossover=get_crossover("int_sbx", prob=1.0, eta=3.0),
                       mutation=get_mutation("int_pm", eta=3.0),
                       eliminate_duplicates=True,
                       )

res = minimize(MyProblem(),
               method,
               termination=('n_gen', 40),
               seed=1,
               save_history=True
               )

print("Best solution found: %s" % res.X)
print("Function value: %s" % res.F)
print("Constraint violation: %s" % res.CV)

simulationTime = datetime.datetime.now() - start_time
print("Total training time: " + str(simulationTime))


#%%Parallelized - doesn't work
# from pymoo.factory import get_algorithm, get_crossover, get_mutation, get_sampling
# from pymoo.optimize import minimize
# from pymoo.core.problem import ElementwiseProblem
# from pymoo.core.problem import starmap_parallelized_eval
# from multiprocessing.pool import ThreadPool
# import multiprocessing
#
#
#
# NUM_closed_pipes = 1
# NUM_closed_pipe_constraints = 2*NUM_closed_pipes
# NUM_PipeRepair_constraints = 2
# repairDuration = 4 #pipe repair duration assumed to be 4hrs
#
#
#
# # the number of processes to be used
# n_proccess = 4
# pool = multiprocessing.Pool(n_proccess)
#
#
# class MyProblem(ElementwiseProblem):
#     def __init__(self):
#         super().__init__(n_var = 1+NUM_closed_pipes*2,
#                          n_obj = 1,
#                          n_constr = NUM_PipeRepair_constraints + NUM_closed_pipe_constraints,
#                          xl = 0,
#                          xu = 48,
#                          type_var = int,
#                          runner=pool.starmap,
#                          func_eval = starmap_parallelized_eval
#                          )
#
#     def _evaluate(self, X, out, *args, **kwargs):
#         # Objective and Constraint functions
#         out["F"] = -test.assess_IMM(X)# Objective Value
#         pipe_repair_1 = -X[0]+0.5 #<= 0 #pipe repair time must be greater than 0
#         pipe_repair_2 = X[0]+repairDuration-48 #<= 0 #pipe must be repaired within 48 hrs
#         closedPipe1_1 = -X[1]*100 + X[2] #<=0 #if pipe 1 start time = 0, then pipe 1 endtime = 0
#         closedPipe1_2 = X[1] - X[2] #<= 0 #closing time must occur > opening time
#         out["G"] = np.column_stack([pipe_repair_1, pipe_repair_2, closedPipe1_1, closedPipe1_2])
#
#
# #%%
#
# #solve solution
# method = get_algorithm("ga",
#                        pop_size=5,
#                        sampling=get_sampling("int_random"),
#                        crossover=get_crossover("int_sbx", prob=1.0, eta=3.0),
#                        mutation=get_mutation("int_pm", eta=3.0),
#                        eliminate_duplicates=True,
#                        )
#
# res = minimize(MyProblem(),
#                method,
#                termination=('n_gen', 5),
#                seed=1,
#                save_history=True
#                )
#
# pool.close()
# print("Best solution found: %s" % res.X)
# print("Function value: %s" % res.F)
# print("Constraint violation: %s" % res.CV)
#%% Visualization of Convergence

import matplotlib.pyplot as plt
# number of evaluations in each generation
n_evals = np.array([e.evaluator.n_eval for e in res.history])
# optimum value in each generation
opt = np.array([e.opt[0].F for e in res.history])

plt.title("Convergence")
plt.plot(n_evals, opt, "--")
plt.show()
