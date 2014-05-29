'''
Created on May 28, 2014

@author: sungjinl
'''

import logging

from config.global_config import get_config
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
        self.controller = None
        self.app_logger.info('Cornerstone agent created')
        
    def run_by_output(self, in_events):
        out_events = Events()
        out_events.add_event(
            'speech',
            SpeechOutputEvent(
                'hello', {},
                nlg_args={'type': 'inform','object': 'welcome','args': {}}))
        out_events.add_event(
            'asr_config',
            ASRConfigOutputEvent('set_dtmf_len = 1, set_lm = first_query'))
        out_events.add_event(
            'tts_config',
            TTSConfigOutputEvent('''   :non-listening "true"
   :non-repeatable "true"
'''))
        return out_events
    