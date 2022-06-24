import numpy as np
import yaml
import math
 
np.random.seed(1234) # Set seed for reprodusability
number_of_repeats = 1200
rnd_seeds = np.random.randint(0, high = 100000, size = number_of_repeats)
days_to_simulate = 31
rpc_host = "10.11.1.4"

""" 
Buy = 600; Sell = 200
Buy = 400; Sell = 200
Buy = 200; Sell = 200
Buy = 200; Sell = 400
Buy = 200; Sell = 600
 
Buy = 1500; Sell = 500
Buy = 1000; Sell = 500
Buy = 500; Sell = 500
Buy = 500; Sell = 1000
Buy = 500; Sell = 1500
 
Buy = 3600; Sell = 1200
Buy = 2400; Sell = 1200
Buy = 1200; Sell = 1200
Buy = 1200; Sell = 2400
Buy = 1200; Sell = 3600
 
Buy = 9000; Sell = 3000
Buy = 6000; Sell = 3000
Buy = 3000; Sell = 3000
Buy = 3000; Sell = 6000
Buy = 3000; Sell = 9000
 """

buy_sell_sizes = [(600,200),(400,200),(200,200),(200,400),(200,600),
                  (1500, 500), (1000, 500), (500, 500), (500, 1000), (500, 1500),
                  (3600, 1200), (2400, 1200), (1200, 1200), (1200, 2400), (1200, 3600),
                  (9000, 3000), (6000, 3000), (3000, 3000), (3000, 6000), (3000, 9000)]
 
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