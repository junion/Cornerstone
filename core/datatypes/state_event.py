'''
Created on Jul 5, 2014

@author: Sungjin Lee
'''

class StateEvent(object):
    def __init__(self, state, args={}):
        self.state = state
        self.args = args
        
    def __str__(self):
        return (self.state + '(' + 
                ' '.join(['%s=%s' % (i, v) for (i, v) in self.args.items()]) +
                ')')
