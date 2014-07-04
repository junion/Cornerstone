'''
Created on May 30, 2014

@author: Sungjin Lee
'''

import logging

from config.global_config import get_config
import rule_engine.rule_engine_api as reapi
from core.datatypes.event_list import EventList
from core.datatypes.speech_output import SpeechEvent
from core.datatypes.asr_config_output import ASRConfigOutputEvent
from core.datatypes.tts_config_output import TTSConfigOutputEvent


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
        self.agent.ExecuteCommandLine('set-stop-phase -Ao')
        self.app_logger.info('Controller created')

    def __del__(self):        
        self.kernel.DestroyAgent(self.agent)
        self.kernel.Shutdown()
        del self.kernel
        
    def control_action(self, in_events):
        out_events = Events()
#         out_events.add_event(
#             'speech',
#             SpeechOutputEvent(
#                 'hello', {},
#                 nlg_args={'type': 'inform','object': 'welcome','args': {}}))
#         out_events.add_event(
#             'asr_config',
#             ASRConfigOutputEvent('set_dtmf_len = 1, set_lm = first_query'))
#         out_events.add_event(
#             'tts_config',
#             TTSConfigOutputEvent('''   :non-listening "true"
#    :non-repeatable "true"
# '''))
        return out_events
        
    def _get_cmds(self):
        cmds = {}
        output_link_wme = self.agent.GetOutputLink()
        if output_link_wme:
            for i in range(output_link_wme.GetNumberChildren()):
                cmd = output_link_wme.GetChild(i).ConvertToIdentifier()
                cmd_name = cmd.GetAttribute()
    #            print cmd_name
                params = {}
                for j in range(cmd.GetNumberChildren()):
                    param = cmd.GetChild(j)
                    param_name = param.GetAttribute()
    #                print param_name
    #                print param.GetValueAsString()
                    params[param_name] = param.GetValueAsString() 
                if 'status' not in params:
                    cmds[cmd_name] = params
                    self.agent.CreateStringWME(cmd, 'status', 'complete')
                    self.agent.Commit()
#         pprint(cmds)
        return cmds
        
    
    def _get_output(self, matches=False):
        while True:
            if matches:
                print 'before input phase------------------'
                print self.agent.ExecuteCommandLine('print -d 4 i2')
                self.agent.ExecuteCommandLine('run -p 1')
                print 'before proposal phase------------------'
                print self.agent.ExecuteCommandLine('print -d 4 i2')
                self.agent.ExecuteCommandLine('run -p 1')
                print 'before decision phase------------------'
                print self.agent.ExecuteCommandLine('matches --assertions --wmes')
                if isinstance(matches, basestring):
                    print 'matches production %s:' % matches
                    print self.agent.ExecuteCommandLine('matches %s' % matches)
                print self.agent.ExecuteCommandLine('predict')
                print self.agent.ExecuteCommandLine('preferences S1 operator --names')
                self.agent.ExecuteCommandLine('run -p 1')
                print 'before apply phase------------------'
                print self.agent.ExecuteCommandLine('print -d 4 s1')
                self.agent.ExecuteCommandLine('run -p 1')
                print 'before output phase------------------'
                print self.agent.ExecuteCommandLine('print -d 4 i3')
    
            self.agent.RunSelf(1)
    
            if matches:
                print self.agent.ExecuteCommandLine('print -d 4 s1')
                print self.agent.ExecuteCommandLine('print -d 4 i3')
    
            cmds = self._get_cmds(self.agent)
            if cmds:
                break
        return cmds