'''
Created on Jul 1, 2014

@author: Sungjin Lee
'''

import copy

class NbestList(object):
    """Nbest list"""

    def __init__(self, items=None, prob_dist=True):
        if items:
            self._items = copy.deepcopy(items)
            if 'None' in self._items:
                del self._items['None']
        else:
            self._items = {}
        self._items = self._normalize()
        self._nbest = None
        self._sorted = False

    def __len__(self):
        return len(self._items)

    def __getitem__(self, item):
        if item in self._items:
            return self._items[item]
        else:
            return 0.0

    def __setitem__(self, item, prob):
        if prob < 0.0:
            raise ValueError
        self._items[item] = prob
        self._normalize()
        self._sorted = False
        
    def __delitem__(self, item):
        del self._items[item]
        self._normalize()
        self._sorted = False

    def __str__(self):
        return "<%s>" % " ".join(["%s: %.2f" % (item, prob)
                                  for item, prob in self._get_nbest()])
        
    def _normalize(self):
        if 'None' in self._items:
            del self._items['None']
        total = sum(self._items.values())
        self._items['None'] = max(0.0, 1.0 - total) 
        total += self._items['None']
        for item in self._items:
            self._items[item] /= total

    def _get_nbest(self):
        if not self._sorted:
            self._nbest = sorted(self._items.items(), key=lambda x: x[1],
                                 reverse=True)
        return self._nbest

    def get_items(self):
        return self._items.keys()

    def get_nbest(self):
        return self._get_nbest()
    


