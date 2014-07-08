'''
Created on Jul 2, 2014

@author: Sungjin Lee
'''

from collections import defaultdict
from pprint import pformat, pprint

# speech_act_types = ['inform', 'request', 'expl-conf', 'impl-conf', 
#                     'affirm', 'negate', 'canthelp']

class SpeechAct(object):
    def __init__(self, act_type=None, concept_values=None):
#         assert act_type in speech_act_types
        self.act_type = act_type
        self.concept_values = concept_values

    def __contains__(self, content):
        act_type = content['act_type'] if 'act_type' in content else None
        concept = content['concept'] if 'concept' in content else None
        value = content['value'] if 'value' in content else None
        if act_type and self.act_type != act_type:
            return False
        for c, v in self.concept_values:
            if concept and value:
                if c == concept and v == value:
                    return True
            elif concept:
                if c == concept:
                    return True
            elif value:
                if v == value:
                    return True
        return False

    def __iter__(self):
        for concept_value in self.concept_values:
            yield (self.act_type, concept_value)

    def get_concept_values(self, concept):
        for (c, v) in self.concept_values:
            if c == concept:
                yield v

    def get_concepts(self):
        concepts = set()
        for (c, v) in self.concept_values:
            concepts.add(c)
        return concepts
                
#     def serialize_args(self):
#         return '&'.join([str(self.concept_values[k]) 
#                          for k in sorted(self.concept_values.keys())])
# 
#     def has_relevant_arg(self, key):
#         for arg in self.concept_values.keys():
#             if arg.startswith(key):
#                 return True
#         return False

    def __str__(self):
        return (self.act_type + '(' + 
                ' '.join(['%s=%s' % (c, v) for (c, v) in self.concept_values]) +
                ')')

        
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

    def __contains__(self, content):
        for s_act in self.speech_acts:
            if content in s_act:
                return True
        return False

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
        for s_turn, score in self.nbest:
            yield s_turn, score

    def __contains__(self, content):
        for s_turn, score in self.nbest:
            if content in s_turn:
                return True
        return False

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

    def get_concepts(self, max_best=5):
        concepts = set()
        for s_turn, score in self.nbest[:max_best]:
            for s_act in s_turn:
                concepts = concepts.union(s_act.get_concepts())
        return concepts
        
    def marginal(self, act_type, concept=None, max_best=5):
#         assert act_type in speech_act_types
        concept_score = defaultdict(float)
        for s_turn, score in self.nbest[:max_best]:
            for s_act in s_turn:
                if s_act.act_type == act_type:
                    # LIMIT: currently assume that 
                    # affirm and negate don't have arguments
                    if act_type in ['affirm', 'negate']:
                        concept_score[None] += score
                        continue
                    if not (concept or s_act.concept_values):
                        concept_score[None] += score
                        continue
                    for item in s_act.get_concept_values(concept):
                        concept_score[item] += score
        return sorted(concept_score.items(), key=lambda x: x[1],
                      reverse=True)
        
    def __str__(self):
        return '\n'.join(['%.2f ' % score + str(s_turn) 
                          for s_turn, score in self.nbest])
                   
                   
class SpeechEvent(object):
    def __init__(self, speech_nbest, nlg_args={}, priority=0):
        self.speech_nbest = speech_nbest

    def __str__(self):
        return str(self.speech_nbest)

    def __contains__(self, content):
        return content in self.speech_nbest


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
    print nbest.get_concepts()
    
    print {'act_type': 'inform', 'concept': 'from', 'value': 'cmu'} in nbest
    print {'act_type': 'request', 'concept': 'from'} in nbest
    print {'concept': 'from'} in nbest