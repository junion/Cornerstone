'''
Created on Jul 4, 2014

@author: Sungjin Lee
'''

class SessionEvent():
    def __init__(self, status):
        self.status = status

    def __str__(self):
        return self.status
