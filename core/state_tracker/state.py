'''
Created on Jul 2, 2014

@author: Sungjin Lee
'''

class State(object):
    def __init__(self):
        # new inbound events
        self.new_events = None
        # event history
        self.in_event_history = []
        # session status
        self.session_status = None
        # execution result
        self.execute_result = None
        # concept belief states to track
        self.concept_belief_states = {}
        # last speech outbound event
        self.last_speech_out_event = None    

    def __str__(self):
        state_str = []
        state_str.append('State [')
        state_str.append('Concept belief states >>>>')    
        for concept in self.concept_belief_states.keys():
            state_str.append(concept+':')
            state_str.append(str(self.concept_belief_states[concept]))
        state_str.append('Last outbound speech event >>>>')    
        state_str.append(str(self.last_speech_out_event))
        state_str.append(']')    
        return '\n'.join(state_str)
    
