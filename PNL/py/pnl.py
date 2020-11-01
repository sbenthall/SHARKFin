#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 29 2020

@author: Mark Flood
"""

#import pandas as pd
import seaborn as sns
import os
import time
import sys
import logging
import csv

import pyNetLogo as pnl

import util as UTIL


def run_NLsims(CFG):
    tic0 = time.clock()
    
    sns.set_style('white')
    sns.set_context('talk')
    
    sys.path.append(CFG['DEFAULT']['pythondir'])
    import util as UTIL
    
    # Set up logging
    sid = f"{CFG['pnl']['nLiqSup']}_{CFG['pnl']['nMktMkr']}"
    LOG = logging.getLogger(sid)
    LOG.setLevel(CFG['pnl']['loglevel'])
    logfile = CFG['pnl']['logfilepfx']+sid+'.'+CFG['pnl']['logfilesfx']
    logfile = os.path.join(CFG['pnl']['logdir'], logfile)
    log_fh = logging.FileHandler(logfile, mode='w')
    log_fh.setLevel(CFG['pnl']['loglevel'])
    log_fh.setFormatter(logging.Formatter(CFG['pnl']['logformat']))
    LOG.addHandler(log_fh)
    LOG.warn(f'Sim ID: {sid}')
    
    # Log the configuration dictionary
    UTIL.log_config(LOG, CFG, 'pnl')

    # Locate the NetLogo executable and create a pyNetLogo link to it
    LOG.warn('NetLogoLink: '+CFG['pnl']['NLhomedir'])
    LOG.warn('NetLogoLink version: '+str(CFG['pnl']['NLver']))
    LM = pnl.NetLogoLink(gui=False,
                         netlogo_home=CFG['pnl']['NLhomedir'],
                         netlogo_version=str(CFG['pnl']['NLver']))
    
    # Find the NetLogo script for our LiquidityModel, and load it
    LM_file = os.path.join(CFG['pnl']['NLmodeldir'], CFG['pnl']['NLfilename'])
    LOG.warn('NetLogo model: '+LM_file)
    LM.load_model(LM_file)
    LOG.warn('NetLogo model loaded')
    
    # Feed the parameter choices for this parallel run to our model
    LM.command(f"set #_LiqSup {CFG['pnl']['nLiqSup']}")
    LM.command(f"set #_LiqDem {CFG['pnl']['nLiqDem']}")
    LM.command(f"set #_MktMkr {CFG['pnl']['nMktMkr']}")
    LM.command(f"set BkrBuy_Limit {CFG['pnl']['BkrBuy_Limit']}")
    LM.command(f"set BkrSel_Limit {CFG['pnl']['BkrSel_Limit']}")
    LM.command(f"set LiqBkr_OrderSizeMultiplier {CFG['pnl']['LiqBkr_OrderSizeMultiplier']}")
    LM.command(f"set PeriodtoEndExecution {CFG['pnl']['PeriodtoEndExecution']}")

    # Run the setup function for the NetLogo model
    LOG.warn('NetLogo model -- setup begin')
    LM.command('setup')
    LOG.warn('NetLogo model -- setup end')

    # Run the warmup iterations for the NetLogo model
    LOG.warn('NetLogo model -- warmups begin: '+str(CFG['pnl']['LMtickswarmups']))
    LM.repeat_command('go', int(CFG['pnl']['LMtickswarmups']))
    LOG.warn('NetLogo model -- warmups end')

    # =========================================================================
    # ===================== TIME-SERIES LOGS ==================================
    # =========================================================================
    csvflushinterval = int(CFG['pnl']['csvflushinterval'])
    
    AOfile = CFG['pnl']['LMallorderpfx']+sid+'.'+CFG['pnl']['LMallordersfx']
    AOfile = os.path.join(CFG['pnl']['logdir'], AOfile)
    LOG.warn('Opening all-order (audit) log:'+AOfile)
    AOcsvf = open(AOfile, mode='w')
    AOcsvw = csv.writer(AOcsvf, delimiter='\t')
    AOcsvw.writerow(["Tick","OrderID","OrderTime","OrderPrice","OrderTraderID",
                     "OrderQuantity","OrderBA","TraderWhoType"])

    IVfile = CFG['pnl']['LMinventorypfx']+sid+CFG['pnl']['LMinventorysfx']
    IVfile = os.path.join(CFG['pnl']['logdir'], IVfile)
    LOG.warn('Opening inventory log:'+IVfile)
    IVcsvf = open(IVfile, mode='w')
    IVcsvw = csv.writer(IVcsvf, delimiter='\t')
    IVcsvw.writerow(["Tick","TraderID","TraderWhoType","SharesOwned"])
    
    FACT_TraderNumber=1
    FACT_TypeOfTrader=2
    FACT_SharesOwned =3
    
    # Run the simulation for fullrun ticks, recording as we go
    LOG.warn('NetLogo model -- simruns begin: '+str(CFG['pnl']['LMtickssimruns']))
    for tik in range(int(CFG['pnl']['LMtickssimruns'])):
        LM.command('go')
        ticks = int(LM.report('ticks'))
        LOG.debug(f' -- ticks: {ticks}')

        # ================= ALL ORDER LOG =====================================
        ct_allorders = int(LM.report('length allOrders'))
        LOG.debug(f' -- ct_allorders: {ct_allorders}')
        for i in range(ct_allorders):
            rdr0 = int(LM.report(f'prop_allOrders {i} "OrderID"'))
            rdr1 = float(LM.report(f'prop_allOrders {i} "OrderTime"'))
            rdr2 = float(LM.report(f'prop_allOrders {i} "OrderPrice"'))
            rdr3 = int(LM.report(f'prop_allOrders {i} "OrderTraderID"'))
            rdr4 = float(LM.report(f'prop_allOrders {i} "OrderQuantity"'))
            rdr5 = str(LM.report(f'prop_allOrders {i} "OrderB/A"'))
#            rdr6 = int(LM.report(f'prop_allOrders {i} "TraderWho"'))
            rdr7 = str(LM.report(f'prop_allOrders {i} "TraderWhoType"'))
            AOcsvw.writerow([ticks,rdr0,rdr1,rdr2,rdr3,rdr4,rdr5,  rdr7])
        LOG.debug('Completed allorders for tick:'+str(tik))
        
        # ================== INVENTORY LOG ====================================
        ct_lsttrders = int(LM.report('length list_traders'))
        for i in range(ct_lsttrders):
            tdr0 = int(LM.report(f'prop_list_traders {i} {FACT_TraderNumber}'))
            tdr1 = str(LM.report(f'prop_list_traders {i} {FACT_TypeOfTrader}'))
            tdr2 = float(LM.report(f'prop_list_traders {i} {FACT_SharesOwned}'))
            IVcsvw.writerow([ticks,tdr0,tdr1,tdr2])
        LOG.debug('Completed lsttrders for tick:'+str(tik))

        if ((ticks % csvflushinterval) == 0):
            AOcsvf.flush()
            IVcsvf.flush()

    LOG.warn('Closing all-order (audit) log:'+AOfile)
    AOcsvf.close()
    LOG.warn('Closing inventory log:'+IVfile)
    IVcsvf.close()
    
    LOG.warn('=============== END OF NetLogo RUN ============================')
           
    toc0 = time.clock()
    print('Elapsed (sys clock): ', toc0-tic0)



def main(argv=None):
    """A main function for command line execution
    
    This function parses the command line, loads the configuration, and 
    invokes the local functions:
        
         * run_NLsims(config)
         
    Parameters
    ----------
    argv : dict
        The collection of arguments submitted on the command line
    """
    config = UTIL.parse_command_line(argv, __file__)

    try:
        run_NLsims(config)
    except Exception as e:
        print('Exception: ', e)
    
# This tests whether the module is being run from the command line
if __name__ == "__main__":
    main()
