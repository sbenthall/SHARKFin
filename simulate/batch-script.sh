#!/bin/bash
# Proper header for a Bash script.
pip install -r ../requirements.txt
cd /home/sb/SHARKFin/simulate
python3 run_simulations.py $1 ${2:+"-t $2"}
