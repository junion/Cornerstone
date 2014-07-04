'''
Created on Jul 2, 2014

@author: Sungjin Lee
'''

from collections import defaultdict
from pprint import pformat, pprint

class SpeechAct(object):
    def __init__(self, act_type=None, concept_values=None):
        self.act_type = act_type
        self.concept_values = concept_values

    def __contains__(self, concept):
        for c in self.concept_values.keys():
            if c.startswith(concept):
                return True
        return False

    def __iter__(self):
        for concept_value in self.concept_values:
            yield (self.act_type, concept_value)

    def get_concept_values(self, concept):
        for (c, v) in self.concept_values:
            if c == concept:
                yield v
        
    def serialize_args(self):
        return '&'.join([str(self.concept_values[k]) 
                         for k in sorted(self.concept_values.keys())])

    def has_relevant_arg(self, key):
        for arg in self.concept_values.keys():
            if arg.startswith(key):
                return True
        return False

    def __str__(self):
        return self.act_type + '(' + pformat(self.concept_values) + ')'

        
class SpeechTurn(object):
    def __init__(self):
        self.speech_acts = []

    def __len__(self):
        return len(self.speech_acts)

    def __getitem__(self, i):
        return self.speech_acts[i]

    def __setitem__(self, i, s_act):
        if not isinstance(s_act, SpeechAct):
            raise TypeError
        self.speech_acts[i] = s_act
        
    def __iter__(self):
        for s_act in self.speech_acts:
            yield s_act

    def append(self, s_act):
        if not isinstance(s_act, SpeechAct):
            raise TypeError
        self.speech_acts.append(s_act)
        return self

    def extend(self, s_acts):
        if not all(isinstance(obj, SpeechAct) for obj in s_acts):
            raise TypeError
        self.speech_acts.extend(s_acts)
        return self
        
    def __str__(self):
        return ', '.join([str(s_act) for s_act in self.speech_acts]) 
    

class SpeechNbest(object):
    def __init__(self):
        self.nbest = []

    def __len__(self):
        return len(self.nbest)

    def __getitem__(self, i):
        return self.nbest[i]

    def __iter__(self):
        for score, s_turn in self.nbest:
            yield score, s_turn

    def append(self, s_turn, score):
        if not isinstance(s_turn, SpeechTurn):
            raise TypeError
        i = 0
        for t, s in self.nbest:
            if score > s:
                break
            i += 1
        self.nbest.insert(i, (s_turn, score))
        return self

    def marginal(self, act_type, concept=None, max_best=5):
        concept_score = defaultdict(float)
        for s_turn, score in self.nbest[:max_best]:
            for s_act in s_turn:
                if s_act.act_type == act_type:
                    if not (concept or s_act.concept_values):
                        concept_score[None] += score
                        continue
                    for value in s_act.get_concept_values(concept):
                        concept_score[value] += score
        return sorted(concept_score.items(), key=lambda x: x[1],
                      reverse=True)
        
    def __str__(self):
        return '\n'.join(['%.2f ' % score + str(s_turn) 
                          for s_turn, score in self.nbest])
                   
                   
class SpeechEvent(object):
    def __init__(self, speech_nbest, nlg_args={}, priority=0):
        self.speech_nbest = speech_nbest
        self.priority = priority
        self.nlg_args = nlg_args

    def __str__(self):
        return str(self.speech_nbest)


if __name__ == '__main__':
    nbest = SpeechNbest()
    t = SpeechTurn()
    t.append(SpeechAct('inform', [('from', 'cmu'), ('to', 'port')]))
    t.append(SpeechAct('negate', []))
    nbest.append(t, 0.7)
    t = SpeechTurn()
    t.append(SpeechAct('inform', [('from', 'cmu'), ('to', 'airport')]))
    t.append(SpeechAct('negate', []))
    nbest.append(t, 0.2)
    
    print nbest
    pprint(nbest.marginal('inform', 'from'))
    pprint(nbest.marginal('inform', 'to'))
    pprint(nbest.marginal('inform', 'time'))
    pprint(nbest.marginal('negate'))