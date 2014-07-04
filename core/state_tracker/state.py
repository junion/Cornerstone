'''
Created on Jul 2, 2014

@author: Sungjin Lee
'''

class State(object):
    def __init__(self):
        self.concepts = {}

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

