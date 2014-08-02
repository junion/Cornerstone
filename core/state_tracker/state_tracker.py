'''
Created on Jul 1, 2014

@author: Sungjin Lee
'''

import logging

from config.global_config import get_config


MODULE_ID = 'StateTracker'


class StateTracker(object):
    def __init__(self):
        # load configs
        self.config = get_config()
        # logging
        self.app_logger = logging.getLogger(MODULE_ID)
        self.app_logger.info('State tracker created')

    def update_state(self, state, in_events):
        if state.new_events:
            state.in_event_history.append(state.new_events)
        state.new_events = in_events
        self.update_session_state(state, in_events)
        self.update_execute_state(state, in_events)
        self.update_belief_state(state, in_events)
        
    def update_session_state(self, state, in_events):
        for event in in_events.get_events('session'):
            state.session_status = event.status
        
    def update_execute_state(self, state, in_events):
        state.execute_result = None
        for event in in_events.get_events('state'):
            if event.state == 'execute-result':
                state.execute_result = event.args
        
    def update_belief_state(self, state, in_events):
        for event in in_events.get_events('speech'):
            in_nbest = event.speech_nbest
            in_concepts = in_nbest.get_concepts()
            # LIMIT: currently assume that 
            # affirm and negate don't have arguments
            if state.last_speech_out_event:
                out_nbest = state.last_speech_out_event.speech_nbest
                out_concepts = out_nbest.get_concepts()
            concepts = out_concepts.union(in_concepts)
            for concept in concepts:
                inform_obs = in_nbest.marginal('inform', concept)
                confirm_acts = out_nbest.marginal('expl-conf', concept)
                affirm_obs = []
                negate_obs = []
                if confirm_acts:
                    affirm_obs = in_nbest.marginal('affirm')
                    if affirm_obs:
                        affirm_score = affirm_obs[0][1]
                        affirm_obs = [(c_act[0], affirm_score) 
                                      for c_act in confirm_acts]
                    negate_obs = in_nbest.marginal('negate')
                    if negate_obs:
                        negate_score = negate_obs[0][1]
                        negate_obs = [(c_act[0], negate_score) 
                                      for c_act in confirm_acts]
                self.update_concept_belief(state, concept, inform_obs,
                                           affirm_obs, negate_obs)
    
    def update_last_out_events(self, state, out_events):
        # LIMIT: currently assume that 
        # the system makes only a speech out event
        speech_events = out_events.get_events('speech')
        if speech_events:
            state.last_speech_out_event = speech_events[0]
