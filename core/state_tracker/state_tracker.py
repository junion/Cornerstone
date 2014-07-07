'''
Created on Jul 1, 2014

@author: Sungjin Lee
'''

import logging

from config.global_config import get_config
from core.datatypes.concept_belief_state import ConceptBeliefState


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
        self.update_belief_state(state, in_events)
        
    def update_session_state(self, state, in_events):
        for event in in_events.get_events('session'):
            state.session_status = event.status
        
    def update_belief_state(self, state, in_events):
        raise NotImplementedError
    
    def update_last_out_events(self, state, out_events):
        # LIMIT: currently assume that 
        # the system makes only a speech out event
        state.last_speech_out_event = out_events.get_events('speech')[0]


class SimpleRuleStateTracker(StateTracker):
    def __init__(self):
        StateTracker.__init__(self)

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
                confirm_acts = out_nbest.marginal('confirm', concept)
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

    def update_concept_belief(self, state, concept, inform_obs, 
                              affirm_obs, negate_obs):
        if concept not in state.concepts:
            cb_state = ConceptBeliefState()
#             state.concepts[concept] = cb_state
        else:
            cb_state = state.concepts[concept]
        for item, score in inform_obs:
            cb_state[item] = cb_state[item] + score
        for item, score in affirm_obs:
            cb_state[item] += score
        for item, score in negate_obs:
            cb_state[item] -= min(cb_state[item], score)
        state.concepts[concept] = cb_state.normalize()
                

if __name__ == '__main__':
    from core.state_tracker.state import State
    from core.datatypes.speech_event import (
         SpeechEvent, SpeechNbest, SpeechTurn, SpeechAct)
    from core.datatypes.event_list import EventList
    
    # create state
    state = State()
    print state
    # speech out event
    nbest = SpeechNbest()
    t = SpeechTurn()
    t.append(SpeechAct('confirm', [('route', '54c')]))
    nbest.append(t, 1.0)
#     print nbest
    out_event = SpeechEvent(nbest)
    # last speech out event
    state.last_speech_out_event = out_event
    # speech in event
    nbest = SpeechNbest()
    t = SpeechTurn()
    t.append(SpeechAct('inform', [('from', 'cmu'), ('to', 'port')]))
    t.append(SpeechAct('affirm', []))
    nbest.append(t, 0.71)
    t = SpeechTurn()
    t.append(SpeechAct('inform', [('from', 'cmu'), ('to', 'airport')]))
    t.append(SpeechAct('negate', []))
    nbest.append(t, 0.2)
#     print nbest
#     pprint(nbest.marginal('inform', 'from'))
#     pprint(nbest.marginal('inform', 'to'))
#     pprint(nbest.marginal('inform', 'time'))
#     pprint(nbest.marginal('affirm'))
#     pprint(nbest.marginal('negate'))
#     print nbest.get_concepts()
    in_event = SpeechEvent(nbest)
    in_events = EventList()
    in_events.add_event('speech', in_event)
    # state tracker
    sr_tracker = SimpleRuleStateTracker()
    sr_tracker.update_belief_state(state, in_events)
    print state
