#!/bin/bash
# Proper header for a Bash script.
pip install -r ~/hark/HARK_ABM_INTRO_public/HARK/requirements.txt
cd /home/sb/HARK_ABM_INTRO_public/HARK
python3 run_simulations.py $1 ${2:+"-t $2"}
