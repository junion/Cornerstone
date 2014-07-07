'''
Created on Jul 1, 2014

@author: Sungjin Lee
'''

import copy

class ConceptBeliefState(object):
    """Nbest list"""

    def __init__(self, items=None, prob_dist=True):
        if items:
            self._items = copy.deepcopy(items)
            if 'None' in self._items:
                del self._items['None']
        else:
            self._items = {}
        self._nbest = None
        self._sorted = False
        self._normalized = False
        self._normalize()

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
        if prob < 1e-6:
            return
        self._items[item] = prob
        self._sorted = False
        self._normalized = False
#         self._normalize()
#         self._sorted = False
        
#     def __delitem__(self, item):
#         del self._items[item]
#         self._normalize()
#         self._sorted = False

    def __str__(self):
        return "%s" % ", ".join(["%s: %.2f" % (item, prob)
                                  for item, prob in self._get_nbest()])
        
    def _normalize(self):
        if not self._normalized:
            if 'None' in self._items:
                del self._items['None']
            total = sum(self._items.values())
            self._items['None'] = max(0.0, 1.0 - total) 
            total += self._items['None']
            for item in self._items:
                self._items[item] /= total
            del_list = []
            for item in self._items:
                if item != 'None' and self._items[item] < 1e-6:
                    del_list.append(item)
            for item in del_list:
                del self._items[item]
            self._normalized = True
        return self

    def _get_nbest(self):
        self._normalize()
        if not self._sorted:
            self._nbest = sorted(self._items.items(), key=lambda x: x[1],
                                 reverse=True)
        return self._nbest

#    def get_items(self):
#        return self._items.keys()

    def get_nbest(self):
        return self._get_nbest()
    
    def get_item(self, n):
        nbest = self._get_nbest()
        nbest = [item for item in nbest if item[0] != 'None']
        if len(nbest) < n:
            return None
        
        return nbest[n-1]
    
if __name__ == '__main__':
    cb = ConceptBeliefState()
    cb['CMU'] = 0.21
    print cb
    
    print cb.get_item(1)
    print cb.get_item(2)

