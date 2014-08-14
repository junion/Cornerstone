'''
Created on Aug 12, 2014

@author: Sungjin Lee
'''

class CompVal(dict):
    def __hash__(self):
        return hash(frozenset(self.items()))
#         return hash(tuple(sorted(self.items(), key=lambda x: x[0])))
