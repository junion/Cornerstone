'''
Created on Aug 8, 2014

@author: Sungjin Lee
'''

from core.datatypes.event_list import EventList
from core.datatypes.speech_event import (
     SpeechEvent, SpeechNbest, SpeechTurn, SpeechAct)
from core.datatypes.composite_value import CompVal
from normalizer import normalize


def parse_output_event(outputs, unnormalizer=None):
    events = EventList()
    if not ('dialog-acts' in outputs and outputs['dialog-acts']):
        return events
    nbest = SpeechNbest()
    turn = SpeechTurn()
    for act in outputs['dialog-acts']:
        slots = dict(act['slots'])
        turn.append(SpeechAct(act['act'], normalize(slots)))
    nbest.append(turn, 1.0)
    if unnormalizer:
        for concept in nbest.get_concepts():
            confirm_acts = nbest.marginal('expl-conf', concept)
            if not confirm_acts:
    #                 print self.concept
                confirm_acts = nbest.marginal('impl-conf', concept)
    #             print 'confirm_acts'
    #             print out_nbest
    #             pprint(confirm_acts)
            if confirm_acts:
                dstcform = []
                for slot in slots:
                    if slot.startswith(concept):
                        dstcform.append((slot, slots[slot]))
                if dstcform:
                    dstcform = dict(dstcform)
                    unnormalizer[CompVal(dstcform)] = dstcform
#                     print 'output normalization'
#                     print dstcform
#                     print CompVal(dstcform)
    events.add_event('speech', SpeechEvent(nbest))
    return events
