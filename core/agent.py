'''
Created on May 28, 2014

@author: sungjinl
'''

import logging

from config.global_config import get_config
from core.state_tracker.state_tracker import StateTracker
from core.controller.controller import Controller
from core.datatypes.events import Events
from core.datatypes.speech_output import SpeechOutputEvent
from core.datatypes.asr_config_output import ASRConfigOutputEvent
from core.datatypes.tts_config_output import TTSConfigOutputEvent


MODULE_ID = 'CornerstoneAgent'


class CornerstoneAgent(object):
    
    '''
    '''
    
    def __init__(self):
        # load configs
        self.config = get_config()
        # logging
        self.app_logger = logging.getLogger(MODULE_ID)
        # create a dialog state tracker.
        self.ds_tracker = StateTracker()
        # create a controller. Soar, a rule-based engine, is adopted.
        self.controller = Controller()
        self.app_logger.info('Cornerstone agent created')
        
    def run(self, in_events):
        out_events = self.controller.run(in_events)
        while True: 
            # check if out_events are outputs to environment
            if False:
                # handle out_events
                
                # get new out_events
                out_events = self.controller.run(None)
            else:
                break    
        return out_events
    