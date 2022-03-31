from setuptools import setup, find_packages
import site
import sys
site.ENABLE_USER_SITE = "--user" in sys.argv[1:]

# setup(
#    name='sharkfin',
#    version='0.1.2',
#    description='Simulating Heterogeneous Agents Research Toolkit with Finance',
#    packages=['sharkfin'],  #same as name, #external packages as dependencies
#    scripts=[
#             'simulate/test_simulation.py',
#            ]
# )

setup()