'''
Created on Aug 11, 2014

@author: Sungjin Lee
'''

from pprint import pprint
import cPickle

from env.DSTCV1.prior_process import construct_prior

prior_path = {
    'route': '../model/liftedmaxent/conceptPrior-route',
    'from': '../model/liftedmaxent/conceptPrior-from',
    'to': '../model/liftedmaxent/conceptPrior-to',
    'date': '../model/liftedmaxent/conceptPrior-date',
    'time': '../model/liftedmaxent/conceptPrior-time',
}

concepts = ['route', 'from', 'to', 'date', 'time']
for concept in concepts:
    prior = construct_prior('train3.half1', '/Users/junion/Development/DSTC-DATA', concept)
    pprint(prior)
    cPickle.dump(prior, open(prior_path[concept], 'wb'))
