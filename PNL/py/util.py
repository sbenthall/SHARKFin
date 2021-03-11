#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# This file is part of the Macro Liquidity Toolkit.
#
# The Macro Liquidity Toolkit is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# The Macro Liquidity Toolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with the Macro Liquidity Toolkit.  If not, 
# see <https://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
# Copyright 2019, Mark D. Flood
#
# Author: Mark D. Flood
# Last revision: 27-Jul-2019
# -----------------------------------------------------------------------------

import sys
import os
import getopt

import configparser as cp
import logging
import logging.config as logcfg


def parse_command_line(argv, modulefile):
    """Parses command-line arguments and overrides items in the config.
    
    This method assumes that the Python ConfigParser has already read in
    a config object (during module import), and that additional arguments
    (argv) are available as command-line parameters. The following 
    parameters (all optional) are recognized:
        
        * -c   Print the config dictionary for this module to stdout
        * -l <loglevel_file>      Set the logging threshold for file output
        * -L <loglevel_console>   Set the logging threshold for console output
        * -C <configfile>   Read configuration from a specific file
        * -O <configlocal>   Read local override configuration from a file
        * -h | --help   Print usage help and quit
        * -p <paramkey>:<paramval>  Override/set individual config parameters
    """
    usagestring = ('python '+modulefile+
                  ' [-c]'+
                  ' [-C <configfile>]'+
                  ' [-O <configlocal>]'+
                  ' [-l <loglevel_file>]'+
                  ' [-L <loglevel_console>]'+
                  ' [-h | --help]'+
                  ' [-p <paramkey>:<paramval>]')
    section = os.path.splitext(os.path.basename(modulefile))[0]
    config = None
    config_local = None
    showconfig = False
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hcl:L:C:O:p:", ["help"])
        except getopt.error as msg:
            raise Usage(msg)
        for o, a in opts:
            # Scan through once, to see if help was requested
            if o in ("-h", "--help"):
                print(usagestring)
                sys.exit()
        for o, a in opts:
            # Scan through once, to see if a special config_local is named
            if "-O"==o:
                config_local = a
        for o, a in opts:
            # Scan through once, to see if a special config is named
            if "-C"==o:
                cfgfile = a
                config = read_config(cfgfile, config_local)
        if (None==config):
            # If we still have no config, attempt to read the default
            config = read_config(config_local_file=config_local)
        for o, a in opts:
            # Now we have the right config file, get the parameters
            if "-p"==o:
                [paramkey, paramval] = a.split(':')
                config[section][paramkey] = paramval
            if "-C"==o:
                pass
            elif "-c"==o:
                showconfig = True
            elif "-l"==o:
                config['handler_file']['level'] = a
            elif "-L"==o:
                config['handler_console']['level'] = a
            elif o in ("-h", "--help"):
                print(usagestring)
                sys.exit()
            else:
                assert False, "unhandled option: "+o
    except Usage as err:
        print(err.msg, file=sys.stderr)
        print("for help use --help", file=sys.stderr)
        return 2
    if (showconfig):
        print_config(config, modulefile)
    return config
class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg



def read_config(config_file='macroliquidity.ini',
                config_local_file=None):
    """Reads the application parameters from a local configuration file
    
    Parameters
    ----------
    config_file : filename
        The name of a configuration file. The default value is
        macroliquidity.ini, which should reside in the same directory with
        the Python source code.
    config_local_file : filename
        The name of a local configuration file. These configuration 
        parameters will override any values set in the main config_file. 
        The default value is "macroliquidity_local.ini", which should reside 
        in the same directory with the Python source code.
    """
    config = cp.ConfigParser(interpolation=cp.ExtendedInterpolation())
    if (None==config_local_file):
        config_local_file=config_file.split('.')[0]+'_local.ini'
    print(f'config_file: {config_file}')
    print(f'config_local_file: {config_local_file}')
    config.read([config_file, config_local_file])
#    configure_logger()
    return config



def configure_logger(logger_name=None, logconfig_file='logging.ini'):
    """Reads the logging parameters from a local configuration file
    
    Parameters
    ----------
    logger_name : string
        The name of a logger to create. If this parameter is set to None,
        no logger is configured and the function returns None. 
        Else a logger of the given name is returned.
    logconfig_file : filename
        The name of a local configuration file. The default value is
        logging.ini, which should reside in the local (.) directory.
        
    Returns
    -------
    log : logging.Logger
        The logger for the given logger_name, if specified. If 
        logger_name==None, then this function returns None. 
    """
    log = None
    if not(logging.getLogger().hasHandlers()):
        # Logging has not been configured yet
        Lconfig = cp.ConfigParser(interpolation=cp.ExtendedInterpolation())
        Lconfig.read(logconfig_file)
#        print(f'CONFIG OF TYPE {type(Lconfig)} HAS {len(Lconfig)} ENTRIES')
#        print(f'DIR IS {os.getcwd()}')
        log_dir = Lconfig['handler_file']['args']
        log_dir = log_dir.split(sep="'")[1]
        log_dir = os.path.split(log_dir)[0]
        os.makedirs(log_dir, exist_ok=True)
        logcfg.fileConfig(logconfig_file)
        # Set level on the root logger to the smallest of the handler levels
        LEVELS = {'NOTSET':logging.NOTSET, 'DEBUG':logging.DEBUG,
                  'INFO':logging.INFO, 'WARNING':logging.WARNING,
                  'ERROR':logging.ERROR, 'CRITICAL':logging.CRITICAL}
        loglevel_file = Lconfig['handler_file']['level']
        loglevel_console = Lconfig['handler_console']['level']
        loglevel_min = min(LEVELS[loglevel_file], LEVELS[loglevel_console])
        logging.getLogger().setLevel(loglevel_min)
    if not(logger_name is None):
        # Logging is configured, but we need to add this logger
        log = logging.getLogger(logger_name)
    return log




def print_config(config, modulefile):
    """Prints the parameters for a specific configuration section
    
    Simple formatted dump of the config parameters relevant for a given 
    configuration section. This is useful to confirm that the app has 
    ingested the correct configuation.
    
    Parameters
    ----------
    config : configparser.ConfigParser
        The configuration object to display
    modulefile : str
        The module name whose configuration section should be displayed

    """
    section = os.path.splitext(os.path.basename(modulefile))[0]
    print('-------------------------- CONFIG ----------------------------')
    print('Current working directory:', os.getcwd())
    print('[DEFAULT]')
    config_dict = dict(config['DEFAULT'])
    for k,v in sorted(config_dict.items()):
        print(k, '=', v)
    print('['+section+']')
    config_dict = dict(config[section])
    for k,v in sorted(config_dict.items()):
        print(k, '=', v)
    print('--------------------------------------------------------------')


def log_config(LOG, config, section):
    """Prints the parameters for a specific configuration section
    
    Simple formatted dump of the config parameters relevant for a given 
    configuration section. This is useful to confirm that the app has 
    ingested the correct configuation.
    
    Parameters
    ----------
    LOG : logging.Logger
        The Logger object to process (log) the configuration information 
    section : str
        The module whose configuration section should be displayed

    """
    LOG.info('-------------------------- CONFIG ----------------------------')
    LOG.info('Current working directory: '+os.getcwd())
    LOG.info('[DEFAULT]')
    config_dict = dict(config['DEFAULT'])
    for k,v in sorted(config_dict.items()):
        LOG.info(str(k)+'='+str(v))
    LOG.info('['+str(section)+']')
    config_dict = dict(config[section])
    for k,v in sorted(config_dict.items()):
        LOG.info(str(k)+'='+str(v))
    LOG.info('--------------------------------------------------------------')


