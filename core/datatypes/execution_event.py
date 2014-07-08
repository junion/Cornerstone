'''
Created on Jul 4, 2014

@author: Sungjin Lee
'''

class ExecutionEvent(object):
    def __init__(self, items):
        self.items = items

    def __getitem__(self, item):
        return self.items[item]

    def __setitem__(self, item, value):
        self.items[item] = value
    
    def __str__(self):
        return ('(' + 
                ' '.join(['%s=%s' % (c, v) for (c, v) in self.items.items()]) +
                ')')


