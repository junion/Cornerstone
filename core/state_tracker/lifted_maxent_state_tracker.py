'''
Created on Jul 1, 2014

@author: Sungjin Lee
'''

import logging
import numpy as np
from collections import defaultdict
from math import floor
import cPickle

from config.global_config import get_config
from state_tracker import StateTracker
from core.datatypes.sorted_discrete_dist import SortedDiscreteDist
from ml.features import FeatureVectorizer
from ml.trw import TRW


MODULE_ID = 'LiftedMaxentStateTracker'


vectorizer = FeatureVectorizer()

# basic confidence self.features            
vectorizer.append('none')
for level in range(0,10):
    vectorizer.append('open-inform-conf-level-%d' % level)
for level in range(0,10):
    vectorizer.append('co-inform-conf-level-%d' % level)
for level in range(0,10):
    vectorizer.append('nco-inform-conf-level-%d' % level)
# self.features for explicit-affirmation
for level in range(0,10):
    vectorizer.append('affirm-conf-level-%d' % level)
# self.features for negation
for level in range(0,10):
    vectorizer.append('negate-conf-level-%d' % level)
# self.features for implicit-affirmation
vectorizer.append('impl-affirm')
# maximum score so far        
for level in range(0,10):
    vectorizer.append('max-score-level-%d' % level)   
# accumulated score
vectorizer.append('acc-score')
# prior
for level in range(0,10):
    vectorizer.append('prior-level-%d' % level)   
# canthelp feature
vectorizer.append('canthelp')

    
class LiftedMaxentConceptStateTracker(object):
    def __init__(self, concept):
        # load configs
        self.config = get_config()
        # logging
        self.app_logger = logging.getLogger(MODULE_ID)
        self.app_logger.info('State tracker created')
        self.concept = concept
        if self.config.has_option(MODULE_ID, 'conceptModelPath-%s' % concept):
            model_path = self.config.get(MODULE_ID, 
                                         'conceptModelPath-%s' % concept)
        else:
            model_path = self.config.get(MODULE_ID, 'conceptModelPath-default')
        self.weight_vec = cPickle(model_path)
        if self.config.has_option(MODULE_ID, 'conceptPriorPath-%s' % concept):
            prior_path = self.config.get(MODULE_ID, 
                                         'conceptPriorPath-%s' % concept)
            self.prior = cPickle(prior_path)
        else:
            self.prior = defaultdict(float)
        self.max_levels = self.config.getint(MODULE_ID, 'maxLevels')
        self.context = {}
    
    def init_context(self):
        context = {}
        # inform following an open question
        context['open-inform-conf'] = []
        # inform following a coherent question
        context['co-inform-conf'] = []
        # inform following a noncoherent question
        context['nco-inform-conf'] = []
        context['affirm-conf'] = []
        context['negate-conf'] = []
        context['impl-affirm'] = 0
        context['acc-score'] = 0
        context['max-score'] = 0
        context['canthelp'] = 0
        return context

    def update_context_max_score(self, item, score):
        self.context[item]['max-score'] = max(self.context[item]['max-score'],
                                              score)

    def update_context_acc_score(self, item, score):
        self.context[item]['acc-score'] += score
                
    def update_context(self, state, inform_obs, affirm_obs, negate_obs):
        for item in [obs[0] for obs in inform_obs+affirm_obs+negate_obs]:
            if item not in self.context:
                self.context[item] = self.init_context()
        out_nbest = state.last_speech_out_event.speech_nbest
        request_acts = out_nbest.marginal('request', self.concept)
        expl_conf_acts = out_nbest.marginal('expl-conf', self.concept)
        impl_conf_acts = out_nbest.marginal('impl-conf', self.concept)
        open_acts = out_nbest.marginal('open')
        for item, score in inform_obs:
            if open_acts:
                self.context[item]['open-inform-conf'].append(score)
            elif request_acts or expl_conf_acts or impl_conf_acts:
                self.context[item]['co-inform-conf'].append(score)
            else:
                self.context[item]['nco-inform-conf'].append(score)
            self.update_context_max_score(item, score)
            self.update_context_acc_score(item, score)
        for item, score in affirm_obs:
            self.context[item]['affirm-conf'].append(score)
            self.update_context_max_score(item, score)
            self.update_context_acc_score(item, score)
        for item, score in negate_obs:
            self.context[item]['negate-conf'].append(score)
            self.update_context_acc_score(item, -score)
        if impl_conf_acts and not inform_obs and not negate_obs:
            self.context[item]['impl-affirm'] = 1
        canthelp_acts = out_nbest.marginal('canthelp')
        if canthelp_acts:
            self.context[item]['canthelp'] = 1

    def convert_score_to_level(self, score):
        score = max(0.0, score)
        level = floor(score*self.max_level)
        level = min(self.max_level-1, level)
        return level

    def compute_features(self):
        self.features = defaultdict(defaultdict(float))
        self.features['None']['none-bias'] = 1
        for item in self.context:
            level = self.convert_score_to_level(
                            self.context[item]['open-inform-conf'])
            self.features[item]['open-inform-conf-level-%d' % level] += 1
            level = self.convert_score_to_level(
                            self.context[item]['co-inform-conf'])
            self.features[item]['co-inform-conf-level-%d' % level] += 1
            level = self.convert_score_to_level(
                            self.context[item]['nco-inform-conf'])
            self.features[item]['nco-inform-conf-level-%d' % level] += 1
            level = self.convert_score_to_level(
                            self.context[item]['affirm-conf'])
            self.features[item]['affirm-conf-level-%d' % level] += 1
            level = self.convert_score_to_level(
                            self.context[item]['negate-conf'])
            self.features[item]['negate-conf-level-%d' % level] += 1
            self.features[item]['impl-affirm'] = self.context[item]['impl-affirm']
            level = self.convert_score_to_level(
                            self.context[item]['max-score'])
            self.features[item]['max-score-level-%d' % level] += 1
            self.features[item]['acc-score'] = self.context[item]['acc-score']
            if item in self.prior:
                prior_score = 1.0*self.prior[item] / self.prior_max_freq
            else:
                prior_score = 0.0
            level = self.convert_score_to_level(prior_score)
            self.features[item]['prior-level-%d' % level] = 1
            self.features[item]['canthelp'] = self.context[item]['canthelp']
    
    def feature_vectorize(self):
        vectors = {}
        for item in self.features:
            vectors[item] = vectorizer.vectorize(self.features[item])
        return vectors
    
    def update_belief_state(self, state, inform_obs, affirm_obs, negate_obs):
        self.update_context(state, inform_obs, affirm_obs, negate_obs)
        self.compute_feature()
        vectors = self.feature_vectorize()
        lpots = dict([(item, np.dot(self.weight, vectors[item])) 
                       for item in vectors])
        reasoner = TRW(nodes=[self.concept], 
                       node_vals={self.concept: vectors.keys()}, 
                       node_lpots={self.concept: lpots},
                       edges=[], edge_lpots={})
        marginals, _, _ = reasoner.get_marginals_and_partition()
        return SortedDiscreteDist(marginals)

        
class LiftedMaxentStateTracker(StateTracker):
    def __init__(self):
        StateTracker.__init__(self)
        self.concept_state_trackers = {}
        
    def update_concept_belief(self, state, concept, inform_obs, 
                              affirm_obs, negate_obs):
        if concept not in state.concept_belief_states:
            state.concept_belief_states[concept] = SortedDiscreteDist()
            # create a lifted maxent reasoner for the concept
            ctracker = LiftedMaxentConceptStateTracker(concept)
            self.concept_state_trackers[concept] = ctracker
        else:
            ctracker = self.concept_state_trackers[concept]
        # call the update function of the reasoner 
        cb_state = ctracker.updaate_belief_state(state, inform_obs,
                                                  affirm_obs, negate_obs)
        state.concept_belief_states[concept] = cb_state
        self.app_logger.info('\nConcept %s update:\n%s' % 
                             (concept, 
                              str(state.concept_belief_states[concept])))

                

if __name__ == '__main__':
    from core.state_tracker.state import State
    from core.datatypes.speech_event import (
         SpeechEvent, SpeechNbest, SpeechTurn, SpeechAct)
    from core.datatypes.event_list import EventList
    
    # create context
    state = State()
    print state
    # speech out event
    nbest = SpeechNbest()
    t = SpeechTurn()
    t.append(SpeechAct('expl-conf', [('route', '54c')]))
    nbest.append(t, 1.0)
    out_event = SpeechEvent(nbest)
    # last speech out event
    state.last_speech_out_event = out_event
    # speech in event
    nbest = SpeechNbest()
    t = SpeechTurn()
    t.append(SpeechAct('inform', [('from', 'cmu'), ('to', 'port')]))
    t.append(SpeechAct('affirm', []))
    nbest.append(t, 0.71)
    t = SpeechTurn()
    t.append(SpeechAct('inform', [('from', 'cmu'), ('to', 'airport')]))
    t.append(SpeechAct('negate', []))
    nbest.append(t, 0.2)
    in_event = SpeechEvent(nbest)
    in_events = EventList()
    in_events.add_event('speech', in_event)
    # context tracker
    sr_tracker = LiftedMaxentStateTracker()
    sr_tracker.update_belief_state(state, in_events)
    print state
