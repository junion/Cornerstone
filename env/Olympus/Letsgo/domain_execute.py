'''
Created on Jul 8, 2014

@author: Sungjin Lee
'''

import logging
from pprint import pformat

from env.Olympus.Letsgo.domain_frame_template import *
from core.datatypes.event_list import EventList
from core.datatypes.state_event import StateEvent


MODULE_ID = 'DomainExecute'


app_logger = logging.getLogger(MODULE_ID)

def execute(state, execute_event, out_queue, result_queue):
    if execute_event.operation == 'place-query':
        _send_place_query_message(
                state, execute_event.args['place'],
                out_queue, result_queue)
        in_events = EventList()
        in_events.add_event(
                 'state',
                 StateEvent('execute-result', 
                            {'place-query': execute_event.args['place']}))
        return in_events
    elif execute_event.operation == 'time_parse':
        _send_time_parse_message(state, execute_event.args['time'],
                                 out_queue, result_queue)
    elif execute_event.operation == 'schedule-query':
        _send_schedule_query_message(
                state, execute_event.args['from'], 
                execute_event.args['to'], execute_event.args['time'],
                out_queue, result_queue)
        in_events = EventList()
        if state.schedule_query_result[':outframe'].find('failed\t0') > -1:
            in_events.add_event(
                         'state',
                         StateEvent('execute-result', 
                                    {'schedule-query': 'success'}))
        else:
            in_events.add_event(
                         'state',
                         StateEvent('execute-result', 
                                    {'schedule-query': 'fail'}))
        return in_events
    elif execute_event.operation == 'subsequent_schedule_query':
        _send_schedule_query_message(
                state, execute_event.args['from'], 
                execute_event.args['to'], execute_event.args['time'], 
                out_queue, result_queue,
                next=state.next_query, 
                prev_result=state.schedule_query_result)
        in_events = EventList()
        if state.schedule_query_result[':outframe'].find('failed\t0') > -1:
            in_events.add_event(
                         'state',
                         StateEvent('execute-result', 
                                    {'schedule-query': 'success'}))
        else:
            in_events.add_event(
                         'state',
                         StateEvent('execute-result', 
                                    {'schedule-query': 'fail'}))
        return in_events
    elif execute_event.operation == 'user_defined_function':
        execute_event.args['function'](state)
    return None

def _send_place_query_message(state, place, out_queue, result_queue):
    # Backend lookup
    content = place_query_template
    
    content = content.replace('${name}', place)
    content = content.replace('${type}', state.place_type[place])

    message = {'type':'GALAXYCALL',
               'content':content}

    out_queue.put(message)
    result = result_queue.get()
    result_queue.task_done()

    if not hasattr(state, 'place_query_results'):
        state.place_query_results = {}
        
    if result[':outframe'].find('failed\t1') > -1: 
        state.place_query_results[place] = result[':outframe']
    else:
        state.place_query_results[place] = result[':outframe']
        
    app_logger.info('%s' % pformat(state.place_query_results))


def _send_time_parse_message(state, time, out_queue, result_queue):
    content = parse_datetime_template

    content = content.replace('${gal_slotsframe}', time.replace('"', '\\"'))

    message = {'type':'GALAXYCALL',
               'content':content}

    out_queue.put(message)
    result = result_queue.get()
    result_queue.task_done()
    app_logger.info('Timeinfo: %s' % result.PPrint())

    if not hasattr(state, 'time_parses'):
        state.time_parses = {}
    
    state.time_parses[time] = result

    
def _send_schedule_query_message(
        state, place_from, place_to, time, out_queue, result_queue, 
        route=None, next=False, prev_result=None):
    # Backend lookup
    content = schedule_query_template 
    
    constraints = schedule_constraints_template
    
    time_info = state.time_infos[time]
    if 'day' in time_info and 'now' in time_info:
        time_constraints = full_time_template
        time_constraints = time_constraints.replace('${month}', time_info['month'])
        time_constraints = time_constraints.replace('${day}', time_info['day'])
        time_constraints = time_constraints.replace('${year}', time_info['year'])
        time_constraints = time_constraints.replace('${weekday}', time_info['weekday'])
        time_constraints = time_constraints.replace('${period_spec}', time_info['period_spec'])
        time_constraints = time_constraints.replace('${now}', time_info['now'])
        time_constraints = time_constraints.replace('${value}', time_info['value'])
        time_constraints = time_constraints.replace('${time_type}', time_info['time_type'])
    elif 'now' in time_info:
        time_constraints = brief_time_template
        time_constraints = time_constraints.replace('${period_spec}', time_info['period_spec'])
        time_constraints = time_constraints.replace('${now}', time_info['now'])
        time_constraints = time_constraints.replace('${time_type}', time_info['time_type'])
    else:
        time_constraints = minimal_time_template
        time_constraints = time_constraints.replace('${value}', time_info['value'])
        time_constraints = time_constraints.replace('${time_type}', time_info['time_type'])

    type = '2'
    if next == 'nextbus': type = '4'
    elif next == 'prevbus': type = '5' 

    constraints = constraints.replace('${type}', type)
    constraints = constraints.replace('${time_spec}', time_constraints)
    constraints = constraints.replace('${departure_place_name}', place_from)
    constraints = constraints.replace('${departure_place_type}', state.place_type[place_from])
    constraints = constraints.replace('${arrival_place_name}', place_to)
    constraints = constraints.replace('${arrival_place_type}', state.place_type[place_to])

    if route:
        constraints = constraints.replace('${route_number}','route_number\t%s\n' % route)
    else:
        constraints = constraints.replace('${route_number}','')
    
    content = content.replace('${constraints}', constraints)
    
    state.schedule_constraints = constraints
        
    departure_stops = \
    '\n'.join([x.strip() for x in state.place_query_results[place_from].split('\n')[2:-3]]).replace('stops', 'departure_stops')
    content = content.replace('${departure_stops}', departure_stops)
    arrival_stops = \
    '\n'.join([x.strip() for x in state.place_query_results[place_to].split('\n')[2:-3]]).replace('stops', 'arrival_stops')
    content = content.replace('${arrival_stops}', arrival_stops)

    if prev_result:
        content = content.replace('${result}', '\n'.join([x.strip() for x in prev_result[':outframe'].split('\n')[2:-3]]))
    else:
        content = content.replace('${result}', '')

    message = {'type':'GALAXYCALL',
           'content':content}
    
    out_queue.put(message)
    result = result_queue.get()
    result_queue.task_done()
    
    if result:
        if prev_result:
            new_result = []
            new_section = False
            for x in prev_result[':outframe'].split('\n'):
                if x.find('rides') > -1:
                    new_section = True
                if not new_section:
                    new_result.append(x)
                if x.find('failed') > -1:
                    new_section = False
                    new_result += result[':outframe'].split('\n')[2:-3]
            prev_result[':outframe'] = '\n'.join(new_result)
            result = prev_result
        app_logger.info('Bus schedule: %s' % result.PPrint())
    else:
        app_logger.info('Backend query for schedule failed')

    state.schedule_query_result = result


