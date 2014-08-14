'''
Created on Aug 8, 2014

@author: Sungjin Lee
'''

from collections import defaultdict

from normalizer import normalize


def parse_label(slu_labels):
    labels = defaultdict(set)
    for slu_label in slu_labels:
        if slu_label['label']:
            nslots = normalize(slu_label['slots'])
            for concept in nslots:
                labels[concept] = set([nslots[concept]])
    return labels