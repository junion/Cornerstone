'''
Created on May 30, 2014

@author: sungjinl
'''

import logging

from config.global_config import get_config
import rule_engine.rule_engine_api as reapi
from cornerstone.datatypes.events import Events
from cornerstone.datatypes.speech_output import SpeechOutputEvent
from cornerstone.datatypes.asr_config_output import ASRConfigOutputEvent
from cornerstone.datatypes.tts_config_output import TTSConfigOutputEvent


MODULE_ID = 'Controller'


class Controller(object):
    
    ''' '''
    
    def __init__(self):
        # load configs
        self.config = get_config()
        # logging
        self.app_logger = logging.getLogger(MODULE_ID)
        # create a rule engine kernel
        self.kernel = reapi.create_kernel()
        self.agent = reapi.create_agent(self.kernel, "agent")
        reapi.register_print_callback(self.kernel, self.agent,
                                      reapi.callback_print_message, None)
        self.input_link_wme = self.agent.GetInputLink()
        # load domain rules
        self.domain_rule_source = self.config.get(MODULE_ID, 
                                                  'domainRuleSource')
        self.agent.ExecuteCommandLine("source " + self.domain_rule_source)
        self.app_logger.info('Controller created')

    def __del__(self):        
        self.kernel.DestroyAgent(self.agent)
        self.kernel.Shutdown()
        del self.kernel
        
    def run(self, in_events):
        self.agent.ExecuteCommandLine('run')
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
        
