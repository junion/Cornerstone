'''
Created on May 28, 2014

@author: sungjinl
'''

import logging

from config.global_config import get_config

MODULE_ID = 'DialogThread'



class CornerstoneAgent(object):
    #===========================================================================
    # Inits
    #===========================================================================
    def __init__(self):
        #
        # load configs
        #
        self.config = get_config()
        self.app_logger = logging.getLogger(MODULE_ID)

        self.continue_dialog = True

        # create dialog state, actuator and belief tracker
        self.dialog_state = DialogState(session_id)
        self.dialog_planner = DialogPlanner()
        self.dialog_decider = DialogDecider()
        self.dialog_actuator = DialogActuator(out_queue, result_queue)
        
        # load domain specifications
        self.parse_input_hyps = domain_semantics.parse_input_hyps
        
        app_logger.info('Dialog controller created')
    