'''
Created on Jul 4, 2014

@author: Sungjin Lee
'''

class ExecuteEvent(object):
    def __init__(self, operation, args={}):
        self.operation = operation
        self.args = args

    def __str__(self):
        return ('%s operation: ' % self.operation + 
                ' '.join(['%s=%s' % (c, v) 
                          for (c, v) in self.args.items()]))
