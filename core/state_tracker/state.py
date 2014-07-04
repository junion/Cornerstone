'''
Created on Jul 2, 2014

@author: Sungjin Lee
'''

class State(object):
    def __init__(self):
        # concepts to track
        self.concepts = {}
        # last speech outbound event
        self.last_speech_out_event = None    

    def __str__(self):
        state_str = []
        state_str.append('State [')
        state_str.append('Concept belief states >>>>')    
        for concept in self.concepts.keys():
            state_str.append(concept+':')
            state_str.append(str(self.concepts[concept]))
        state_str.append('Last speech outbound event >>>>')    
        state_str.append(str(self.last_speech_out_event))
        state_str.append(']')    
        return '\n'.join(state_str)
    
    def update(self, item, value):
        assert item in self.state

        state_item = self.state[item]
        if type(state_item) is list:
            state_item.extend(value)
        else:
            self.state[item] = value

    def __setitem__(self, concept, value):
        self.state[concept] = value

    def __getitem__(self, concept):
        return self.state[concept]

