'''
Created on May 30, 2014

@author: Sungjin Lee
'''

class ConfigEvent(object):
    def __init__(self, module, config={}):
        self.module = module
        self.config = config

    def __str__(self):
        return ('%s config: ' % self.module + 
                ' '.join(['%s=%s' % (c, v) 
                          for (c, v) in self.config.items()]))



