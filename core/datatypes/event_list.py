
import collections

class EventList(collections.MutableSequence):
    
    ''' Contain a list of events.
    Methods:
    add_event -- add event to this container
    '''
    
    def __init__(self, *args):
        '''Initialize an empty event list'''
        self.list = list(args)

    def __len__(self):
        return len(self.list)
    
    def __getitem__(self, i): 
        return self.list[i]

    def __delitem__(self, i): 
        del self.list[i]

    def __setitem__(self, i, v):
        self.list[i] = v

    def insert(self, i, v):
        self.list.insert(i, v)

    def add_event(self, event_type, event):
        # session: begin / close
        # speech:
        # execute:
        # config: asr / tts 
        if event_type not in ['session', 'speech', 'config',
                              'execute']:
            raise RuntimeError('Invalid event type')
        self.list.append({'event_type': event_type, 'event': event})

    def __str__(self):
        return '\n'.join([str(event) 
                          for event in self.list])
