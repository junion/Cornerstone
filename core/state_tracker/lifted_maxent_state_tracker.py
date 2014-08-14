'''
Created on Jul 1, 2014

@author: Sungjin Lee
'''

import logging
import numpy as np
from collections import defaultdict
from math import floor
import cPickle
from datetime import datetime
from pprint import pformat, pprint
from scipy.optimize import fmin_cg

from config.global_config import get_config
from state_tracker import StateTracker
from core.datatypes.sorted_discrete_dist import SortedDiscreteDist
from ml.features import FeatureVectorizer
from ml.trw import TRW
from ml.owlqn import fmin_owlqn


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
    def __init__(self, concept, load_model=True):
        # load configs
        self.config = get_config()
        # logging
        self.app_logger = logging.getLogger(MODULE_ID)
        self.app_logger.info('State tracker created')
        self.concept = concept
        self.max_level = self.config.getint(MODULE_ID, 'maxLevels')
        self.context = {}
        home_dir = self.config.get('Common', 'home')
        if self.config.has_option(MODULE_ID, 'conceptPriorPath-%s' % concept):
            prior_path = self.config.get(MODULE_ID, 
                                         'conceptPriorPath-%s' % concept)
            self.prior = cPickle.load(open(home_dir+prior_path, 'rb'))
            self.max_prior = max([p[1] for p in self.prior.items()])
        else:
            self.prior = defaultdict(float)
            self.max_prior = 1
        if load_model:
            self.load_model()
            
    def load_model(self):
        home_dir = self.config.get('Common', 'home')
        if self.config.has_option(MODULE_ID, 'conceptModelPath-%s' % self.concept):
            model_path = self.config.get(MODULE_ID, 
                                         'conceptModelPath-%s' % self.concept)
        else:
            model_path = self.config.get(MODULE_ID, 'conceptModelPath-default')
        try:
            self.weights = cPickle.load(open(home_dir+model_path, 'rb'))
        except:
            self.weights = np.zeros(len(vectorizer))
#         print self.concept
#         vectorizer.print_weights(self.weights)
            
    def init_item_context(self):
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

    def get_obs(self, state, in_nbest):
        inform_obs = in_nbest.marginal('inform', self.concept)
        affirm_obs = []
        negate_obs = []
        if state.last_speech_out_event:
            out_nbest = state.last_speech_out_event.speech_nbest
            confirm_acts = out_nbest.marginal('expl-conf', self.concept)
            if not confirm_acts:
#                 print self.concept
                confirm_acts = out_nbest.marginal('impl-conf', self.concept)
#             print 'confirm_acts'
#             print out_nbest
#             pprint(confirm_acts)
            if confirm_acts:
                affirm_obs = in_nbest.marginal('affirm')
                if affirm_obs:
                    affirm_score = affirm_obs[0][1]
                    affirm_obs = [(c_act[0], affirm_score) 
                                  for c_act in confirm_acts]
                negate_obs = in_nbest.marginal('negate')
                if negate_obs:
                    negate_score = negate_obs[0][1]
                    negate_obs = [(c_act[0], negate_score) 
                                  for c_act in confirm_acts]
#         pprint(affirm_obs)
#         pprint(negate_obs)
        return inform_obs, affirm_obs, negate_obs

    def update_context_max_score(self, item, score):
        self.context[item]['max-score'] = max(self.context[item]['max-score'],
                                              score)

    def update_context_acc_score(self, item, score):
        self.context[item]['acc-score'] += score
                
    def update_context(self, state, in_nbest): 
        inform_obs, affirm_obs, negate_obs = self.get_obs(
                                                state, in_nbest)
        for item in [obs[0] for obs in inform_obs+affirm_obs+negate_obs]:
            if item not in self.context:
                self.context[item] = self.init_item_context()
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
            # NEW
            self.update_context_max_score(item, score)
            self.update_context_acc_score(item, score)
        for item, score in negate_obs:
            self.context[item]['negate-conf'].append(score)
            self.update_context_acc_score(item, -score)
        if impl_conf_acts and not inform_obs and not negate_obs:
            for ic_act in impl_conf_acts:
                if ic_act[0] in self.context:
                    self.context[ic_act[0]]['impl-affirm'] = 1
                else:
                    print 'KeyError %s in implicit confirmation feature computation' % str(ic_act[0])
        canthelp_acts = out_nbest.marginal('canthelp')
        if canthelp_acts:
            self.context[item]['canthelp'] = 1

    def convert_score_to_level(self, score):
        score = max(0.0, score)
        level = floor(score*self.max_level)
        level = min(self.max_level-1, level)
        return level

    def compute_feature(self):
        features = defaultdict(lambda: defaultdict(float))
        features[None]['none'] = 1
        for item in self.context:
            for score in self.context[item]['open-inform-conf']:
                level = self.convert_score_to_level(score)
                features[item]['open-inform-conf-level-%d' % level] += 1
            for score in self.context[item]['co-inform-conf']:
                level = self.convert_score_to_level(score)
                features[item]['co-inform-conf-level-%d' % level] += 1
            for score in self.context[item]['nco-inform-conf']:
                level = self.convert_score_to_level(score)
                features[item]['nco-inform-conf-level-%d' % level] += 1
            for score in self.context[item]['affirm-conf']:
                level = self.convert_score_to_level(score)
                features[item]['affirm-conf-level-%d' % level] += 1
            for score in self.context[item]['negate-conf']:
                level = self.convert_score_to_level(score)
                features[item]['negate-conf-level-%d' % level] += 1
            features[item]['impl-affirm'] = self.context[item]['impl-affirm']
            level = self.convert_score_to_level(
                            self.context[item]['max-score'])
            features[item]['max-score-level-%d' % level] += 1
            features[item]['acc-score'] = self.context[item]['acc-score']
            if item in self.prior:
                prior_score = float(self.prior[item]) / self.max_prior
            else:
                prior_score = 0.0
            level = self.convert_score_to_level(prior_score)
            features[item]['prior-level-%d' % level] = 1
            features[item]['canthelp'] = self.context[item]['canthelp']
        return features
    
    def feature_vectorize(self, features):
        vectors = {}
        for item in features:
            vectors[item] = vectorizer.vectorize(features[item])
        return vectors
    
    @classmethod
    def construct_reasoner(cls, concept, weights, vectors):
        lpots = dict([(item, np.dot(weights, vectors[item])) 
                       for item in vectors])
        return TRW(nodes=[concept],
                   node_vals={concept: vectors.keys()},
                   node_lpots={concept: lpots},
                   edges=[], edge_lpots={})
    
    def get_feature_vector(self):
        features = self.compute_feature()
        return self.feature_vectorize(features)

    def get_belief_state(self):
        features = self.compute_feature()
        vectors = self.feature_vectorize(features)
        reasoner = self.construct_reasoner(self.concept, self.weights, vectors)
        marginals, _, _ = reasoner.get_marginals_and_partition()
        return SortedDiscreteDist(marginals[self.concept])
    
        
class LiftedMaxentStateTracker(StateTracker):
    def __init__(self):
        StateTracker.__init__(self)
        self.concept_state_trackers = {}

    def get_concept_tracker(self, concept, state):
        if concept not in state.concept_belief_states:
            state.concept_belief_states[concept] = SortedDiscreteDist()
            # create a lifted maxent reasoner for the concept
            ctracker = LiftedMaxentConceptStateTracker(concept)
            self.concept_state_trackers[concept] = ctracker
        else:
            ctracker = self.concept_state_trackers[concept]
        return ctracker
    
    def update_concept_belief(self, concept, state, in_nbest):
        ctracker = self.get_concept_tracker(concept, state)
        ctracker.update_context(state, in_nbest)
        cb_state = ctracker.get_belief_state()
        state.concept_belief_states[concept] = cb_state
        self.app_logger.info('\nConcept %s update:\n%s' % 
                             (concept, 
                              str(state.concept_belief_states[concept])))

    def get_concept_feature_vector(self, concept, state):
        ctracker = self.get_concept_tracker(concept, state)
        return ctracker.get_feature_vector()


class LiftedMaxentTrainer(object):                
    def __init__(self, concept, inactive_features = {}, RW={}, 
                 default_RW=3.0, prior_RW=10.0,
                 init_weights=None, adapt_RW=5.0):
        self.concept = concept
        self.inactive_features = inactive_features
        self.RW = RW
        self.default_RW = default_RW
        self.prior_RW = prior_RW
        self.init_weights = init_weights
        self.adapt_RW = adapt_RW
        self.weigths = None
        
    def get_empirical_expectation(self, example, verbose=0):
        # take the feature vector associated with the true label
        emp_exp = np.zeros(len(vectorizer),
                           dtype=np.dtype('Float64'))
        labels = example['labels']
        num_used_labels = 0
        for label in labels:
            if verbose:
                print 'label: %s' % label
                print 'emp_exp:'
                print example['features'][label]
            try:
                emp_exp += example['features'][label]
            except KeyError:
                print 'label: %s' % label
                print 'items: %s' % example['features'].keys()
                raise KeyError
#                 emp_exp += example['features'][None]
            num_used_labels += 1
        if num_used_labels > 0:
            emp_exp /= 1.0 * num_used_labels
        return emp_exp
    
    def get_model_expectation(self, example, marginals, verbose=0):
        mod_exp = np.zeros(len(vectorizer),
                           dtype=np.dtype('Float64'))
        # take the expectation of the feature vector associated with 
        # each configuration w.r.t. marginals  
        for item in example['features']:
            if verbose:
                print 'item: %s' % item
                print 'marginal: %f' % marginals[item]
                print 'features:'
                print example['features'][item]
                if verbose > 1:
                    print 'named features:'
                    print vectorizer.print_weights(example['features'][item])
            mod_exp += example['features'][item] * marginals[item]
        return mod_exp

    def adjust_example(self, example):
        for label in example['labels']:
            if label in example['features']:
                break
        else:
            print 'adjust example'
            print 'labels:'
            print example['labels']
            print 'items:'
            print example['features'].keys()
            # label and observation mismatch
            example['labels'] = [None]
            print 'changed labels:'
            print example['labels']
            return True
        return False
            
    def duplicate_example(self, example, prev):
        if prev['features'].keys() != example['features'].keys():
            return False
        for item in prev['features']:
            for feat in prev['features'][item]: 
                if not np.array_equal(example['features'][item][feat],
                                      prev['features'][item][feat]):
                    return False
        return True
        
    def get_marginals(self, example, weights, verbose=0):
        reasoner = LiftedMaxentConceptStateTracker.construct_reasoner(
                                    self.concept, weights, example['features'])
        marginals, _, _ = reasoner.get_marginals_and_partition()
        if verbose:
            print 'marginals:'
            pprint(marginals)
        return SortedDiscreteDist(marginals[self.concept])

    def get_log_likelihood(self, example, weights, zval=None):
        reasoner = LiftedMaxentConceptStateTracker.construct_reasoner(
                                    self.concept, weights, example['features'])
        labels = example['labels'] if example['labels'] else [None]
        return reasoner.get_log_likelihood({self.concept: labels})

    def train(self, examples):
        print 'dataset size: %d' % len(examples)
        def NLL_grad(active_weights, **args):
            weights = args['weights']
#             init_weights = args['init_weights']
            active_index = args['active_index']
            weights[active_index] = active_weights
#             weights, active_index, init_weights = args
            gradients = np.zeros_like(active_weights, dtype=np.dtype('Float64'))
            prev = None
            verbose = 0
            for i, ex in enumerate(examples):
#                 adjusted = self.adjust_example(ex)
#                 if prev and self.duplicate_example(ex, prev):
#                     continue
                prev = ex
#                 verbose = 2 if adjusted else 0
                # compute a gradient
                # -(E_empirical[feature] - E_model[feature])
                emp_exp = self.get_empirical_expectation(ex, verbose)
                verbose = 0
                # compute marginals and partition function
                marginals = self.get_marginals(ex, weights, verbose)
                mod_exp = self.get_model_expectation(ex, marginals, verbose)
                gradients -= (emp_exp - mod_exp)[active_index]
            if self.init_weights.any():
                # L2 regularization
                gradients += (2 * self.adapt_RW * 
                              (weights[active_index] - 
                               self.init_weights[active_index])) 
            return gradients
                    
        def NLL_eval(active_weights, **args):
            weights = args['weights']
#               init_weights = args['init_weights']
            active_index = args['active_index']
            weights[active_index] = active_weights
#             weights, active_index, init_weights = args
#             vectorizer.print_weights(weights)
            NLL = 0.0
            prev = None
            for ex in examples:
#                 self.adjust_example(ex)
#                 if prev and self.duplicate_example(ex, prev):
#                     continue
                prev = ex
                # accumulate log-likelihoods
                NLL -= self.get_log_likelihood(ex, weights)
            if self.init_weights.any():
                # L2 regularization
                NLL += self.adapt_RW * np.sum(np.power(weights[active_index] - 
                                        self.init_weights[active_index], 2)) 
            print 'NLL: %f' % NLL
            return NLL

        # if this part can generalize across models
        # a separate trainer class should be designed
        if not self.init_weights:
            self.init_weights = np.zeros(len(vectorizer))
        weights = np.zeros(len(vectorizer))
        Cvec = np.ones_like(weights) * self.default_RW
        for prefix in self.RW:
            index = vectorizer.feature_index_startswith(prefix)
            Cvec[index] = self.RW[prefix]
        active_index = range(len(vectorizer))
        for prefix in self.inactive_features:
            active_index -= vectorizer.feature_index_startswith(prefix)
        active_weights = weights[active_index]
        active_Cvec = Cvec[active_index]
        print 'Number of active weights: %d' % len(active_weights)
        print 'Number of total weights: %d' % len(weights)
        print datetime.now()
        active_weights, fval, gfk, func_calls, grad_calls, warnflag = \
            fmin_owlqn(f=NLL_eval, x0=active_weights, 
                       fprime=NLL_grad,
                       args={'weights': weights, 
                             'active_index': active_index, 
                             'init_weights': self.init_weights},
                       Cvec=active_Cvec, gtol=1e0, ftol=1e-1, 
                       maxiter=80, full_output=1)
#         active_weights = \
#             fmin_cg(f=NLL_eval, x0=active_weights, 
#                     fprime=NLL_grad,
#                     args=(weights, active_index, self.init_weights),
#                     gtol=1e0, maxiter=80)
        weights[active_index] = active_weights
        self.weights = weights
        vectorizer.print_weights(weights)
#         print fval
#         print func_calls
#         print grad_calls
        print datetime.now()
        
    def save(self, model_path):
        cPickle.dump(self.weights, open(model_path, 'wb'))



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
