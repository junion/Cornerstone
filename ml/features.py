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
    
    def append(self, feature):
        self.feature_index[feature] = len(self.feature_index)
        
    def vectorize(self, features):
        vec = np.zeros(len(self.feature_index))
        for feat in features:
            if feat in self.feature_index:
                vec[self.feature_index[feat]] = features[feat]
        return vec
