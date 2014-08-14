#! C:\Python27\python.exe

import sys
import os
import argparse
import json
import copy
import time
import itertools
from math import exp
import logging
import logging.config
from pprint import pprint

from config.global_config import init_config, get_config
from dataset_walker import dataset_walker
from core.state_tracker.state import State
from core.state_tracker.lifted_maxent_state_tracker \
    import LiftedMaxentStateTracker
from input_parser import parse_input_event
from output_parser import parse_output_event
from core.datatypes.composite_value import CompVal


init_config()
config = get_config()
config.read(['../config/system.conf'])
logging.config.fileConfig('../config/logging.conf')

nodes = ['route', 'from', 'to', 'date', 'time']
slots = ['route',
         'from.desc', 'from.neighborhood', 'from.monument',
         'to.desc', 'to.neighborhood', 'to.monument',
         'date',
         'time']
exclusive_subnodes = ['from', 'to']

unnormalizer = {}

def get_belief_state(state):
    belief_state = {}
    for slot in slots:
        belief_state[slot] = {'hyps': []}
    heuristic_joint_none_score = 1.0 
    for node in nodes:
        if node not in state.concept_belief_states:
            continue
        for val in state.concept_belief_states[node]:
            if val:#if val and state.concept_belief_states[node][val] > 0:
                if val in unnormalizer:
                    dstcform = unnormalizer[val] 
                else:
                    print 'missing in unnormalizer'
                    print val
                    pprint(unnormalizer)
                    continue
                if node in exclusive_subnodes:
#                     for inst in tracker.state['observation'][node]['instance'][val]:
#                         for found_slot in inst['slots'].keys():
#                             belief_state[found_slot]['hyps'].append(
#                                 {'score': state.concept_belief_states[node][val], 
#                                  'slots': {found_slot: inst['slots'][found_slot]}, 
#                                  'value': val})
#                         break # this break boost the performance in discrimination
                    for found_slot in dstcform:
                        try:
                            belief_state[found_slot]['hyps'].append(
                                {'score': state.concept_belief_states[node][val], 
                                 'slots': {found_slot: dstcform[found_slot]}, 
                                 'value': val})
                        except:
                            print node
                            print found_slot
                            print dstcform
                            print val
                else:
#                     for inst in tracker.state['observation'][node]['instance'][val]:
#                         belief_state[node]['hyps'].append(
#                             {'score': state.concept_belief_states[node][val], 
#                              'slots': copy.deepcopy(inst['slots']), 
#                              'value': val})
#                         break # this break boost the performance in discrimination    
                    belief_state[node]['hyps'].append(
                        {'score': state.concept_belief_states[node][val], 
                         'slots': copy.deepcopy(dstcform), 
                         'value': val})
            else: #elif val == None:
                heuristic_joint_none_score *= state.concept_belief_states[node][val]
        if node == 'time' and len(belief_state[node]['hyps']) > 1:
            belief_state[node]['hyps'].sort(key=lambda x: x['score'], reverse=True)
            if abs(belief_state[node]['hyps'][0]['score'] - belief_state[node]['hyps'][1]['score']) < 1e-5 and\
            len(belief_state[node]['hyps'][0]['value']) < len(belief_state[node]['hyps'][1]['value']):
                belief_state[node]['hyps'][0]['score'] -= 1e-5
                belief_state[node]['hyps'][1]['score'] += 1e-5
            else:
                belief_state[node]['hyps'][0]['score'] += 1e-5
                belief_state[node]['hyps'][1]['score'] -= 1e-5
    # constructs the joint using joint inference
    belief_state['joint'] = {'hyps': []}
#     slot_hyps_list = []
#     for slot in slots:
#         slot_hyps = []
#         if len(belief_state[slot]['hyps']) > 0:
#             belief_state[slot]['hyps'].sort(key=lambda x: x['score'], reverse=True)
#             for i, hyp in enumerate(belief_state[slot]['hyps']):
#                 if i > 2:
#                     break
#                 slot_hyps.append(hyp['value'])
#             if (i == 3 and state.concept_belief_states[slot.split('.')[0]][None] > 
#                 belief_state[slot]['hyps'][-1]['score']):
#                 slot_hyps[-1] = None
#             elif (state.concept_belief_states[slot.split('.')[0]][None] > 
#                   belief_state[slot]['hyps'][-1]['score']): #len(slot_hyps)-1
#                 slot_hyps.append(None)
#         else:
#             slot_hyps.append(None)
#         slot_hyps_list.append(slot_hyps)
#     
#     mbest_total_joint_score = 0.0
#     ex = copy.deepcopy(tracker.state)
#     for i, slot in enumerate(slots):
#         ex['label'][slot.split('.')[0]] = []
#         
#     none_joint_score = exp(tracker.get_log_likelihood(ex, zval=zval))
#     for joint_conf in itertools.product(*slot_hyps_list):
#         ex = copy.deepcopy(tracker.state)
#         joint = {}
#         joint_score = 1.0
#         for i,slot in enumerate(slots):
#             ex['label'][slot.split('.')[0]] = []
# 
#         none_joint_score = exp(tracker.get_log_likelihood(ex, zval=zval))
#         for i,slot in enumerate(slots):
#             if joint_conf[i] != 'None':
#                 ex['label'][slot.split('.')[0]].append(joint_conf[i])
#                 joint.update(tracker.state['observation'][slot.split('.')[0]]['instance'][joint_conf[i]][0]['slots'])
#                 
#         if len(ex['label']['from']) > 1 or len(ex['label']['to']) > 1:
#             continue 
#         
#         joint_score = exp(tracker.get_log_likelihood(ex, zval=zval))
#         mbest_total_joint_score += joint_score
#         if joint_conf == tuple(['None'] * len(slots)):
#             mbest_total_joint_score -= joint_score
#         if joint != {}:
#             belief_state['joint']['hyps'].append({
#                     'score': joint_score,
#                     'slots': joint,
#                     })
# 
#     if mbest_total_joint_score > 1.0 and len(belief_state['joint']['hyps']) > 0:
#         print 'Maybe BUG!!!!!'
#         for hyp in belief_state['joint']['hyps']:
#             hyp['score'] /= mbest_total_joint_score
#     elif len(belief_state['joint']['hyps']) > 0:
#         prob_mass_to_make_up = 1.0 - mbest_total_joint_score - none_joint_score
#         unit_mass = 0.01 
#         make_up_joint = copy.deepcopy(belief_state['joint']['hyps'][-1]['slots'])
#         while prob_mass_to_make_up > 0:
#             belief_state['joint']['hyps'].append({
#                     'score': min(unit_mass,prob_mass_to_make_up),
#                     'slots': make_up_joint,
#                     })                
#             prob_mass_to_make_up -= unit_mass
# 
#     for slot in slots:
#         if slot not in belief_state:
#             continue
#         for hyp in belief_state[slot]['hyps']:
#             del hyp['value']
    return belief_state


def main():
    #
    # CMD LINE ARGS
    # 
#     install_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#     utils_dirname = os.path.join(install_path, 'lib')
#     sys.path.append(utils_dirname)
#     list_dir = os.path.join(install_path, 'config')
    parser = argparse.ArgumentParser(description='Simple hand-crafted dialog state tracker baseline.')
    parser.add_argument('--dataset', dest='dataset', action='store', metavar='JSON_FILE', required=True,
                        help='The dataset to analyze, for example train1 or test2 or train3a')
    parser.add_argument('--dataroot', dest='dataroot', action='store', required=True,
                        help='Will look for corpus in <destroot>/<dataset>/...')
    parser.add_argument('--asrmode', dest='asrmode', action='store', required=True, metavar='PATH',
                        help='live or batch')
    parser.add_argument('--trackfile', dest='scorefile', action='store', required=True,
                        help='File to write with tracker output')
    parser.add_argument('--haslabel', dest='haslabel', action='store', required=True,
                        help='label available or not')
    args = parser.parse_args()

    haslabel = True if args.haslabel == 'yes' else False
    sessions = dataset_walker(args.dataset, dataroot=args.dataroot, labels=haslabel)    

    start_time = time.time()
    r = {
        'sessions':[],
        'dataset':args.dataset,
        }

    global unnormalizer
    state = State()
    state_tracker = LiftedMaxentStateTracker()
    for session in sessions:
        session_start_time = time.time()
        unnormalizer = {}
        r['sessions'].append({'turns':[], 'session-id': session.log['session-id'],})
        for turn_index, (log_turn, label_turn) in enumerate(session):
            if (log_turn['restart'] == True or turn_index == 0):
                state = State()
                state_tracker = LiftedMaxentStateTracker()
                unnormalizer = {}
            out_events = parse_output_event(log_turn['output'], unnormalizer)
            in_events = parse_input_event(log_turn['input']['live']['slu-hyps'], unnormalizer)
            state_tracker.update_last_out_events(state, out_events)
            state_tracker.update_state(state, in_events)  
            belief_state = get_belief_state(state)
#             print out_events
#             print in_events
#             pprint(unnormalizer)
#             print state  
#             pprint(belief_state)
            r['sessions'][-1]['turns'].append(belief_state)
        session_end_time = time.time()
        print session_end_time - session_start_time
    end_time = time.time()
    elapsed_time = end_time - start_time
    r['wall-time'] = elapsed_time
    
    f = open(args.scorefile,'w')
    json.dump(r,f,indent=2)
    f.close()


if (__name__ == '__main__'):
#    sys.argv = ['offline_tracker.py',
#                '--dataset=train1a.half2',
#                '--dataroot=D:/Work/DSTC/dstc_data',
#                '--asrmode=live',
#                '--trackfile=track-tr1a.json']
    
    main()




