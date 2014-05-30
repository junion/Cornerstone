'''
Created on May 28, 2014

@author: sungjinl
'''

import logging

from config.global_config import get_config
from cornerstone.controller.controller import Controller
from cornerstone.datatypes.events import Events
from cornerstone.datatypes.speech_output import SpeechOutputEvent
from cornerstone.datatypes.asr_config_output import ASRConfigOutputEvent
from cornerstone.datatypes.tts_config_output import TTSConfigOutputEvent


MODULE_ID = 'CornerstoneAgent'


class CornerstoneAgent(object):
    
    '''
    '''
    
    def __init__(self):
        # load configs
        self.config = get_config()
        # logging
        self.app_logger = logging.getLogger(MODULE_ID)
        # create a controller. Soar, a rule-based engine, is adopted.
        self.controller = Controller()
        self.app_logger.info('Cornerstone agent created')
        
    def run(self, in_events):
        out_events = self.controller(in_events)
        while True: 
            # check if out_events are outputs to environment
            if False:
                # handle out_events
                
                # get new out_events
                out_events = self.controller()
            else:
                break    
        return out_events
    