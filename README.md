# SHARKFin

_Simulating Heterogeneous Agents Research Toolkit) with Finance_

## Development Installation

SHARKFin depends on Python 3.9 or above.

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

SHARKFin comes with a simple native Python market class, the MockMarket.

The MockMarket has a dividend value that follows a lognormal random walk, and a constant price-to-dividend ratio.

## AMMPS Installation

AMMPS is currently closed-source so an ammps binary needs to be acquired.

### Running with AMMPS

To run a local simulation:

1. Start a rabbitMQ server. This is most easily accomplished using the publically available image on dockerhub.

```
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

2. Start AMMPS. These instructions assume you have the binary available. In `ammps_sharkfin_container`, the binaries are in `ammps_sharkfin_container/container_contents/ammps_bin` Run from `ammps_sharkfin_container` with:

```
dotnet container_contents/ammps_bin/amm.engine.dll RunConfFromFile testconfigs/testconf.xlsx working 0 --rabbitMQ-host localhost --rabbitMQ-queue rpc_queue -t true
```

Refer to AMMPS documentation for parameters and instructions on how to generate the Excel config files.


3. Run SHARKFin

```
python run_whiteshark.py OUTPUT_PREFIX
```

## NetLogo Installation

For instructions for running with a NetLogo based market, see `pnl_market/README.md`.
