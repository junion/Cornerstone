'''
Created on Jul 1, 2014

@author: Sungjin Lee
'''

import logging

from state_tracker import StateTracker
from core.datatypes.sorted_discrete_dist import SortedDiscreteDist


MODULE_ID = 'SimpleRuleStateTracker'


class SimpleRuleStateTracker(StateTracker):
    def __init__(self):
        StateTracker.__init__(self)

    def update_concept_belief(self, state, concept, inform_obs, 
                              affirm_obs, negate_obs):
        if concept not in state.concept_belief_states:
            cb_state = SortedDiscreteDist()
        else:
            cb_state = state.concept_belief_states[concept]
        for item, score in inform_obs:
            cb_state[item] = cb_state[item] + score
        for item, score in affirm_obs:
            cb_state[item] += score
        for item, score in negate_obs:
            cb_state[item] -= min(cb_state[item], score)
        state.concept_belief_states[concept] = cb_state
        self.app_logger.info('\nConcept %s update:\n%s' % 
                             (concept, str(state.concept_belief_states[concept])))
                

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
    t.append(SpeechAct('expl-conf', [('route', '54c')]))
    nbest.append(t, 1.0)
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
    in_event = SpeechEvent(nbest)
    in_events = EventList()
    in_events.add_event('speech', in_event)
    # state tracker
    sr_tracker = SimpleRuleStateTracker()
    sr_tracker.update_belief_state(state, in_events)
    print state
