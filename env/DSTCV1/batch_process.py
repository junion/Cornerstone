'''
Created on Aug 8, 2014

@author: Sungjin Lee
'''

from pprint import pprint
from collections import defaultdict
from copy import deepcopy

from dataset_walker import dataset_walker
from core.state_tracker.state import State
from core.state_tracker.lifted_maxent_state_tracker \
    import LiftedMaxentStateTracker
from input_parser import parse_input_event
from output_parser import parse_output_event
from label_parser import parse_label
from core.state_tracker.lifted_maxent_state_tracker import vectorizer 


def adjust_example(example):
    labels = []
    for label in example['labels']:
        if label in example['features']:
            labels.append(label)
    if len(labels) < len(example['labels']):
        print 'adjust example'
        print 'labels:'
        print example['labels']
        print 'items:'
        print example['features'].keys()
        # label and observation mismatch
        example['labels'] = labels if labels else [None]
        print 'changed labels:'
        print example['labels']
        return True
    return False

def construct_dataset(json, json_root, pull_concepts=[]):
    sessions = dataset_walker(json, json_root, labels=True)    
    examples = []
    for session in sessions:
        state = State()
        state_tracker = LiftedMaxentStateTracker()
        labels = defaultdict(set)
        for turn_index, (log_turn, label_turn) in enumerate(session):
#             print '\n\n\n##################'
#             print 'turn %d' % turn_index
            if log_turn['restart'] == True:
                state = State()
                state_tracker = LiftedMaxentStateTracker()
                labels = defaultdict(set)
            out_events = parse_output_event(log_turn['output'])
            in_events = parse_input_event(log_turn['input']['live']['slu-hyps'])
            new_labels = parse_label(label_turn['slu-labels'])
            for concept in new_labels:
                labels[concept] = labels[concept].union(new_labels[concept]) 
#             print out_events
#             print in_events
#             print 'new_labels'
#             pprint(new_labels)
#             print 'labels'
#             pprint(labels)
            state_tracker.update_last_out_events(state, out_events)
            state_tracker.update_state(state, in_events)
            for pcon in pull_concepts:
                ex = {}
                ex['features'] = state_tracker.get_concept_feature_vector(
                                                                pcon, state)
                ex['labels'] = (list(labels[pcon]) if pcon in labels and 
                                labels[pcon] else [None])
                if adjust_example(ex):
                    print ('happened in session %s at turn %d' % 
                           (session.applog_filename, turn_index))
                    print 'labels:'
                    print ex['labels']
                    print 'items:'
                    print ex['features'].keys()
                examples.append(ex)
    return examples

