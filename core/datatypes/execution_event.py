'''
Created on Jul 4, 2014

@author: Sungjin Lee
'''

class ExecutionEvent(object):
    def __init__(self, asr_config):
        self.asr_config = asr_config

    def __str__(self):
        return self.asr_config 


