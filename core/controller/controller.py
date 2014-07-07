'''
Created on May 30, 2014

@author: Sungjin Lee
'''

from copy import deepcopy
from pprint import pprint, pformat
import logging

from config.global_config import get_config
import rule_engine.rule_engine_api as reapi
from core.state_tracker.state import State
from core.datatypes.event_list import EventList
from core.datatypes.speech_event import (
        SpeechEvent, SpeechNbest, SpeechTurn, SpeechAct)
from core.datatypes.config_event import ConfigEvent
from core.datatypes.turn_event import TurnEvent


MODULE_ID = 'Controller'


class Controller(object):
    def __init__(self):
        # load configs
        self.config = get_config()
        # logging
        self.app_logger = logging.getLogger(MODULE_ID)
        # previous state
        self.prev_state = State()
        # create a rule engine kernel
        self.re_kernel = reapi.create_kernel()
        # this agent is the one maintained by the rule engine
        # should not be confused with the cornerstone re_agent
        self.re_agent = reapi.create_agent(self.re_kernel, "agent")
        self.app_logger.info('rule engine kernel and agent created')
        reapi.register_print_callback(self.re_kernel, self.re_agent,
                                      reapi.callback_print_message, None)
        # get the input link of the rule engine
        self.input_link_wme = self.re_agent.GetInputLink()
        # load domain rules
        self.domain_rule_source = self.config.get(MODULE_ID, 
                                                  'domainRuleSource')
        self.app_logger.info('domain rules loaded')
        # variable for an event link
        self.events = None
        # source rules for a given domain
        self.re_agent.ExecuteCommandLine("source " + self.domain_rule_source)
        # set the stop phase to 'After output'
        self.re_agent.ExecuteCommandLine('set-stop-phase -Ao')
        self.app_logger.info('Controller created')

    def __del__(self):        
        self.re_kernel.DestroyAgent(self.re_agent)
        self.re_kernel.Shutdown()
        del self.re_kernel
        
    def create_input_to_rule_engine(self, state):
        # destroy the event link 
        if self.events:
            self.re_agent.DestroyWME(self.events)
        # create an event link
        self.events = self.re_agent.CreateIdWME(self.input_link_wme, 'events')
        # session begin/end
        if self.prev_state.session_status != state.session_status:
            if state.session_status == 'begin':
                self.re_agent.CreateStringWME(self.events, 'begin-session', 'nil')
            elif state.session_status == 'end':
                self.re_agent.CreateStringWME(self.events, 'end-session', 'nil')
            else:
                raise ValueError
        # belief state
        # currently top, second, rest will be enough for decision making
        # TODO: update only changed concepts
        for concept in state.concepts.keys():
#            self.app_logger.info('\nConcept %s update:\n%s' % str(state.concepts[concept]))
            cu = self.re_agent.CreateIdWME(self.events, 'concept-update')
            self.re_agent.CreateStringWME(cu, 'name', concept)
            rest_score = 1.0
            for i, label in enumerate(['top-hyp', 'second-hyp']):
                item = state.concepts[concept].get_item(i+1)
                if item:
                    value, score = item
                else:
                    value = 'nil'
                    score = 0.0
                hyp = self.re_agent.CreateIdWME(cu, label)
                self.re_agent.CreateStringWME(hyp, 'value', value)
                self.re_agent.CreateFloatWME(hyp, 'score', score)
                rest_score -= score
            hyp = self.re_agent.CreateIdWME(cu, 'rest-hyp')
            self.re_agent.CreateStringWME(hyp, 'value', 'nil')
            self.re_agent.CreateFloatWME(hyp, 'score', rest_score)
        # backup the state  
        self.prev_state = deepcopy(state)
        
    def control_action(self, state):
        self.app_logger.info('\nCreate input to rule engine')
        self.create_input_to_rule_engine(state)
        self.app_logger.info('\nGet outboound events from rule engine')
        out_events = self.get_events('grounding-concept*propose*expl-conf')
        self.app_logger.info('\n'+str(out_events))
        return out_events
        
    def poll_events(self):
        events = EventList()
        output_link_wme = self.re_agent.GetOutputLink()
        if output_link_wme:
            for i in range(output_link_wme.GetNumberChildren()):
                event_struct = output_link_wme.GetChild(i).ConvertToIdentifier()
                event_type = event_struct.GetAttribute()
                if event_type == 'wait':
                    raise RuntimeError
    #            print cmd_name
                params = {}
                for j in range(event_struct.GetNumberChildren()):
                    param = event_struct.GetChild(j)
                    param_name = param.GetAttribute()
    #                print param_name
    #                print param.GetValueAsString()
                    params[param_name] = param.GetValueAsString() 
                if 'status' not in params:
                    if event_type == 'speech':
                        # speech out event
                        act_type = params['act_type']
                        del params['act_type']
                        turn = SpeechTurn()
                        turn.append(SpeechAct(act_type, params.items()))
                        nbest = SpeechNbest()
                        nbest.append(turn, 1.0)
                        events.add_event('speech', SpeechEvent(nbest))
                    elif event_type == 'config':
                        # config out event
                        module = params['module']
                        del params['module']
                        events.add_event('config', ConfigEvent(module, params))
                    elif event_type == 'turn':
                        events.add_event('turn', TurnEvent(params))
                    else:
                        self.app_logger.info(event_type)
#                         raise ValueError
                    self.re_agent.CreateStringWME(event_struct, 'status', 'complete')
#                     self.re_agent.Commit()
#         pprint(cmds)
        return events
    
    def get_events(self, matches=False):
        while True:
            if matches:
                self.app_logger.info('\nbefore input phase------------------')
                self.app_logger.info('\n'+self.re_agent.ExecuteCommandLine('print -d 4 i2'))
                self.app_logger.info('\n'+self.re_agent.ExecuteCommandLine('print -d 4 s1'))
                self.re_agent.ExecuteCommandLine('run -p 1')
                self.app_logger.info('\nbefore proposal phase------------------')
                self.app_logger.info('\n'+self.re_agent.ExecuteCommandLine('print -d 4 i2'))
                self.app_logger.info('\n'+self.re_agent.ExecuteCommandLine('print -d 4 s1'))
                self.re_agent.ExecuteCommandLine('run -p 1')
                self.app_logger.info('\nbefore decision phase------------------')
                self.app_logger.info('\n'+self.re_agent.ExecuteCommandLine('print -d 4 s1'))
                self.app_logger.info('\n'+self.re_agent.ExecuteCommandLine('matches --assertions --wmes'))
                if isinstance(matches, basestring):
                    self.app_logger.info('\nmatches production %s:' % matches)
                    self.app_logger.info('\n'+self.re_agent.ExecuteCommandLine('matches -t -w %s' % matches))
                self.app_logger.info('\n'+self.re_agent.ExecuteCommandLine('predict'))
                self.app_logger.info('\n'+self.re_agent.ExecuteCommandLine('preferences S1 operator --names'))
                self.re_agent.ExecuteCommandLine('run -p 1')
                self.app_logger.info('\nbefore apply phase------------------')
                self.app_logger.info('\n'+self.re_agent.ExecuteCommandLine('print -d 4 s1'))
                self.re_agent.ExecuteCommandLine('run -p 1')
                self.app_logger.info('\nbefore output phase------------------')
                self.app_logger.info('\n'+self.re_agent.ExecuteCommandLine('print -d 4 i3'))
            self.re_agent.RunSelf(1)
            if matches:
                self.app_logger.info('\n'+self.re_agent.ExecuteCommandLine('print -d 4 s1'))
                self.app_logger.info('\n'+self.re_agent.ExecuteCommandLine('print -d 4 i3'))
            events = self.poll_events()
            if not events.empty():
                return events