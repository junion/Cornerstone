'''
Created on May 28, 2014

@author: Sungjin Lee
'''

import logging

from config.global_config import get_config
from core.state_tracker.state import State
from core.state_tracker.state_tracker import SimpleRuleStateTracker
from core.controller.controller import Controller


MODULE_ID = 'CornerstoneAgent'


class CornerstoneAgent(object):
    def __init__(self):
        # load configs
        self.config = get_config()
        # logging
        self.app_logger = logging.getLogger(MODULE_ID)
        # create a state
        self.state = State()
        # create a state tracker.
        self.state_tracker = SimpleRuleStateTracker()
        # create a controller. Soar, a rule-based engine, is adopted.
        self.controller = Controller()
        self.app_logger.info('Cornerstone agent created')
        
    def run(self, in_events):
        self.app_logger.info('\nInbound events >>>>\n%s' % str(in_events))
        self.state_tracker.update_state(self.state, in_events)
        out_events = self.controller.control_action(self.state)
        self.app_logger.info('\nOutbound events >>>>\n%s' % str(out_events))
        while True: 
            # check if out_events are outputs to environment
            if False:
                # handle out_events
                
                # get new out_events
                out_events = self.controller.control_action(None)
            else:
                break
        self.state_tracker.update_last_out_events(self.state, out_events)    
        return out_events
    