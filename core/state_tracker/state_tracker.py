'''
Created on Jul 1, 2014

@author: Sungjin Lee
'''

import logging

from config.global_config import get_config
from core.datatypes.event_list import Events


MODULE_ID = 'StateTracker'


class StateTracker(object):
    
    ''' '''
    
    def __init__(self):
        # load configs
        self.config = get_config()
        # logging
        self.app_logger = logging.getLogger(MODULE_ID)
        # concept list
        self._concept_list = {}
        self.app_logger.info('State tracker created')

    def state_update(self, state, in_events):
        
        pass
