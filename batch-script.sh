#!/bin/bash
# Proper header for a Bash script.
cd /home/sb/HARK_ABM_INTO_public/HARK
pip install -r requirements.txt
python3 run_simulation.py $1
