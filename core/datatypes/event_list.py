
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

    def empty(self):
        return len(self.list) == 0
    
    def insert(self, i, v):
        self.list.insert(i, v)

    def add_event(self, event_type, event):
        # session: begin / close
        # speech:
        # execute:
        # config: asr / tts 
        if event_type not in ['session', 'speech', 'config',
                              'state', 'turn', 'execute']:
            raise RuntimeError('Invalid event type: %s' % event_type)
        self.list.append({'event_type': event_type, 'event': event})

    def get_events(self, event_type):
        requested_list = []
        for item in self.list:
            if item['event_type'] == event_type:
                requested_list.append(item['event'])
        return requested_list

    def __str__(self):
        return '\n'.join([event['event_type'] + ': ' + str(event['event']) 
                          for event in self.list])
