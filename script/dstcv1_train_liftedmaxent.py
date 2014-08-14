'''
Created on Aug 11, 2014

@author: Sungjin Lee
'''

from pprint import pprint
import cPickle

from env.DSTCV1.batch_process import construct_dataset
from core.state_tracker.lifted_maxent_state_tracker import LiftedMaxentTrainer
from config.global_config import init_config, get_config


init_config()
config = get_config()
config.read(['../config/system.conf'])

model_path = {
    'route': '../model/liftedmaxent/conceptModel-route',
    'from': '../model/liftedmaxent/conceptModel-from',
    'to': '../model/liftedmaxent/conceptModel-to',
    'date': '../model/liftedmaxent/conceptModel-date',
    'time': '../model/liftedmaxent/conceptModel-time',
    'default': '../model/liftedmaxent/conceptModel-default',
}

concepts = ['route', 'from', 'to', 'date', 'time']
#concepts = ['from']
dataset_root = '/Users/junion/Development/DSTC-DATA'

dataset_path = 'train3.half1'
dataset_path = 'train2.half1'
dataset_path = 'train1a.half1'

# individual models
for concept in concepts:
    print '\n\n\n@@@@@@@@@'
    print concept
    dataset = construct_dataset(dataset_path, dataset_root, [concept])
    cPickle.dump(dataset, open(model_path[concept].replace('Model', 'Trainingset'), 'wb'))
   
for concept in concepts:
    print '\n\n\n@@@@@@@@@'
    print concept
    dataset = cPickle.load(open(model_path[concept].replace('Model', 'Trainingset'), 'rb'))
    trainer = LiftedMaxentTrainer(concept)
#     trainer = LiftedMaxentTrainer(concept, default_RW=4.0, prior_RW=15.0)
    trainer.train(dataset)
    trainer.save(model_path[concept])

# default model
# concept = 'default'
# dataset = construct_dataset('train3.half1', '/Users/junion/Development/DSTC-DATA', concepts)
# cPickle.dump(dataset, open(model_path[concept].replace('Model', 'Trainingset'), 'wb'))
# trainer = LiftedMaxentTrainer(concept)
# trainer.train(dataset)
# trainer.save(model_path[concept])
