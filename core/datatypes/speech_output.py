
from pprint import pformat


class SpeechOutputEvent(object):
    def __init__(self, act_type, act_args, nlg_args={}, priority=0):
        self.act_type = act_type
        self.act_args = act_args
        self.priority = priority
        self.nlg_args = nlg_args
        
    def serialize_args(self):
        return '&'.join([str(self.act_args[k]) 
                         for k in sorted(self.act_args.keys())])

    def has_relevant_arg(self, key):
        for arg in self.act_args.keys():
            if arg.startswith(key):
                return True
        return False
    
    def __str__(self):
        return self.act_type + '(' + pformat(self.act_args) + ')' 


