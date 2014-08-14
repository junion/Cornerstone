'''
Created on Aug 4, 2014

@author: Sungjin Lee
'''

import numpy as np


class FeatureVectorizer(object):
    def __init__(self, features = []):
        self.feature_index = {}
        for idx, feat in enumerate(features):
            self.feature_index[feat] = idx

    def __len__(self):
        return len(self.feature_index)
    
    def print_weights(self, weights):
        for feat, idx in sorted(self.feature_index.items(), key=lambda x: x[0]):
            print '%s: %f' % (feat, weights[idx])
            
    def append(self, feature):
        self.feature_index[feature] = len(self.feature_index)
        
    def vectorize(self, features):
        vec = np.zeros(len(self.feature_index))
        for feat in features:
            if feat in self.feature_index:
                vec[self.feature_index[feat]] = features[feat]
        return vec
    
    def feature_index_startswith(self, prefix):
        matched_index = []
        for feat in self.feature_index:
            if feat.startswith(prefix):
                matched_index.append(self.feature_index[feat])
        return matched_index
