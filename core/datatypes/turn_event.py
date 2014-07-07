'''
Created on Jul 6, 2014

@author: Sungjin Lee
'''

class TurnEvent(object):
    def __init__(self, args={}):
        self.args = args
        
    def __str__(self):
        return ('(' + 
                ' '.join(['%s=%s' % (i, v) for (i, v) in self.args.items()]) +
                ')')
