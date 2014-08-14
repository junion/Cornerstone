'''
Created on Aug 8, 2014

@author: Sungjin Lee
'''

from copy import deepcopy
from pprint import pprint

from core.datatypes.event_list import EventList
from core.datatypes.speech_event import (
     SpeechEvent, SpeechNbest, SpeechTurn, SpeechAct)
from normalizer import normalize


def get_concept_slots(concept, slots):
    concept_slots = []
    for slot, val in slots:
        if slot.startswith(concept):
            concept_slots.append((slot, val))
    return dict(concept_slots)
    
def parse_input_event(slu_hyps, unnormalizer=None):
    events = EventList()
    nbest = SpeechNbest()
    for slu_hyp in slu_hyps:
        if slu_hyp['score'] <= 0.0: #CHECKOUT
            continue
        turn = SpeechTurn()
        for act in slu_hyp['slu-hyp']:
            normform = normalize(dict(act['slots']))
            turn.append(SpeechAct(act['act'], normform))
            if unnormalizer != None:
                for concept in normform:
                    unnormalizer[normform[concept]] = \
                        get_concept_slots(concept, act['slots'])
        nbest.append(turn, slu_hyp['score'])
    events.add_event('speech', SpeechEvent(nbest))
    return events


