'''
Created on Aug 8, 2014

@author: Sungjin Lee
'''

from collections import defaultdict

from dataset_walker import dataset_walker
from label_parser import parse_label


def construct_prior(json, json_root, concept):
    sessions = dataset_walker(json, json_root, labels=True)    
    prior = defaultdict(float)
    for session in sessions:
        labels = {}
        for turn_index, (log_turn, label_turn) in enumerate(session):
            if log_turn['restart'] == True:
                break
            labels.update(parse_label(label_turn['slu-labels']))
        if concept in labels:
            prior[labels[concept]] += 1.0
    return prior
