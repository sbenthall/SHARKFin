# SHARKFin

_Simulating Heterogeneous Agents Research Toolkit) with Finance_

## Development Installation

To check out the code, clone the repository.

```
git clone git@github.com:sbenthall/SHARKFin.git
cd SHARKFin
```

You may wish to create and enter a virtual environment.

Then, install the required packages and then the SHARKFin package in development mode:

```
pip install -r requirements.txt
pip install -e .
```

Run the automated tests:

```
python -m pytest sharkfin
```

## Configuration

TBD


## Native Python Market Installation

TBD

## AMMPS Installation

TBD

## NetLogo Installation

The original SHARKFin installation path uses NetLogo for its market simulation engine.

The simulation depends on a specific NetLogo version.
Be sure to have netlogo-5.3.1-64 installed.
You will specify the install directory in a configuration
file.

### Configuration

There are now two config files:

 (1) macroliquidity.ini
 (2) macroliquidity_local.ini

You need to have both files present on your machine.

Any parameters you specify in `macroliquidity_local.ini`
will override the values in `macroliquidity.ini`.

Full paths to the directories for python, logs,
NetLogo models, and NetLogo home must be specified in
a macroliquidity_local.ini file.

Do NOT commit this local config file to the github repo.

The defaults are

```
[DEFAULT]
pythondir=./py
logdir=./out/logs
[pnl]
NLmodeldir=./nl/
NLhomedir=./netlogo-5.3.1-64/
```

### Execution

To run the simulation:

```
$ python3 ./py/pnl.py
```

### Output

The `pnl.py` file, when run, should output three files
into `./out/logs/`

```
 LM_90_5.log           This is the process log
 LMallorders_90_5.csv  The ticker of orders over time
 LMinventory_90_5.csv  Record of traders' inventories over time
 ```

### NetLogo Simulation

This simulation builds on Mark Paddrick's OFR model.
It has some additional components.

A breed in the NetLogo file `order_updates` is
created during the simulation and instances of this
breed are collected in a list: allOrders.
There is then a special reporter that PyNetLogo
can call to query this list: `prop_allOrders`.
