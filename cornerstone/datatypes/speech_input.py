
from pprint import pformat


class UserAction(object):
    def __init__(self, act_type, act_args):
        self.act_type = act_type
        self.act_args = act_args
        # for off-line belief tracking on DSTC dataset
        self.slots = act_args

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
        

class SLUHyp(object):
    def __init__(self, user_acts, conf_score):
        self.user_acts = user_acts
        self.conf_score = conf_score

    def __str__(self):
        return (','.join([str(user_act) 
                          for user_act in self.user_acts]) + 
                '[' + str(self.conf_score) + ']') 
                   
                   
class SpeechInputEvent(object):
    def __init__(self, SLU_Nbests=[], ASR_Nbests=[], ASR_CN=None):
        self.SLU_Nbests = SLU_Nbests
        self.ASR_Nbests = ASR_Nbests
        self.ASR_CN = ASR_CN

    def __str__(self):
        return '\n'.join([str(slu_hyp) 
                          for slu_hyp in self.SLU_Nbests])

    
