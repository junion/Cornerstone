'''
Created on Aug 9, 2014

@author: Sungjin Lee
'''

from core.datatypes.composite_value import CompVal

    
def normalize(slots):
    nslots = {}
    time = CompVal()
    date = CompVal()
    for slot in slots:
        if slot.startswith('from'):
            nslots['from'] = CompVal({'from': slots[slot]})
        elif slot.startswith('to'):
            nslots['to'] = CompVal({'to': slots[slot]})
        elif slot.startswith('date'):
            date[slot] = slots[slot]
        elif slot.startswith('time'):
            time[slot] = slots[slot]
        else:
            nslots[slot] = CompVal({slot: slots[slot]})
    if date:
        nslots['date'] = date
    if time:
        nslots['time'] = time
    return nslots
        
