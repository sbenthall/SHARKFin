import numpy as np
import yaml
import math
 
np.random.seed(1234) # Set seed for reprodusability
number_of_repeats = 1200
rnd_seeds = np.random.randint(0, high = 100000, size = number_of_repeats)
days_to_simulate = 31
rpc_host = "10.11.1.4"
 
buy_sell_sizes = [(600,200),(400,200),(200,200),(200,400),(200,600),
                  (1500, 500), (1000, 500), (500, 500), (500, 1000), (500, 1500),
                  (3000, 1000), (2000, 1000), (1000, 1000), (1000, 2000), (1000, 3000),
                  (7500, 2500), (5000, 2500), (2500, 2500), (2500, 5000), (2500, 7500)]
 
n = 0
n_files = 0
sims_in_yaml = 10
configs = list()
for buy_sell in buy_sell_sizes:
    for seed in rnd_seeds:
 
        segment = math.floor(n/1200) + 2
        rpc_host = "10.11." + str(segment) + ".4"
 
        configs.append({"SIMID" : n,
        "SIMRNDSEED" : int(seed),
        "DAYSTOSIMULATE" : days_to_simulate ,
        "RPCHOST": rpc_host,
        "RPCQUEUE" : "chumqueue" + str(n),
        "BUYSIZE" : buy_sell[0],
        "SELLSIZE" : buy_sell[1]})
        n += 1
        if len(configs) == sims_in_yaml:
            f = open('chum_config{}.yaml'.format(n_files), encoding = 'utf-8', mode = "w")
            yaml_content = {"SIMULATIONS" : configs}
            yaml.dump(yaml_content, f)
            configs = list() #make new list
            n_files += 1
        if n == number_of_repeats*len(buy_sell_sizes):
            f = open('chum_config{}.yaml'.format(n_files), encoding = 'utf-8', mode = "w")
 
            yaml_content = {"SIMULATIONS" : configs}
            yaml.dump(yaml_content, f)
            f.close()