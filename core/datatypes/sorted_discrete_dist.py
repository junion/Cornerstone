'''
Created on Jul 1, 2014

@author: Sungjin Lee
'''

from copy import deepcopy
from pprint import pprint

class SortedDiscreteDist(object):
    """Sorted discrete probability distribution"""

    def __init__(self, items=None):
        if items:
            self.items = deepcopy(items)
            if None in self.items:
                del self.items[None]
        else:
            self.items = {}
        self.nbest = None
        self.sorted = False
        self.normalized = False

    def __len__(self):
        return len(self.items)

    def __getitem__(self, item):
        self.normalize()
        if item in self.items:
            return self.items[item]
        else:
            return 0.0

    def __setitem__(self, item, score):
        if score < 0.0:
            raise ValueError
        if score < 1e-6:
            return
        self.items[item] = score
        self.sorted = False
        self.normalized = False

    def __delitem__(self, item):
        del self.items[item]
        self.sorted = False
        self.normalized = False

    def __iter__(self):
        self.normalize()
        self.sort()
        for item, _ in self.nbest:
            yield item
            
    def __str__(self):
        return "%s" % ", ".join(["%s: %.2f" % (item, prob)
                                  for item, prob in self.get_nbest()])
        
    def normalize(self):
        if not self.normalized:
            if None in self.items:
                del self.items[None]
            total = sum(self.items.values())
            self.items[None] = max(0.0, 1.0-total) 
            total += self.items[None]
            for item in self.items:
                self.items[item] /= total
            del_list = []
            for item in self.items:
                if item != None and self.items[item] < 1e-6:
                    del_list.append(item)
            for item in del_list:
                del self.items[item]
            self.normalized = True

    def sort(self):
        if not self.sorted:
            self.nbest = sorted(self.items.items(), key=lambda x: x[1],
                                 reverse=True)
            self.sorted = True
        
    def get_nbest(self):
        self.normalize()
        self.sort()
        return deepcopy(self.nbest)

    def get_sorted_item(self, n):
        nbest = self.get_nbest()
        nbest = [item for item in nbest if item[0] != None]
        if len(nbest) < n:
            return None
        return nbest[n-1]

    
if __name__ == '__main__':
    cb = SortedDiscreteDist()
    cb['CMU'] = 0.21
    print cb  
    print cb['CMU']
    print cb[None]  
    print cb.get_sorted_item(1)
    print cb.get_sorted_item(2)

