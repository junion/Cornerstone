'''
Created on Jul 4, 2014

@author: Sungjin Lee
'''

from datetime import datetime
import logging

from core.datatypes.event_list import EventList
from core.datatypes.speech_event import (
     SpeechEvent, SpeechNbest, SpeechTurn, SpeechAct)
from core.datatypes.execution_event import ExecutionEvent

app_logger = logging.getLogger('DomainInputParser')

#=============================================================================
# building a priority list of semantic mapping functions
# a semantic function checks specific conditions with 
# the dialog state and frame to generate a particular user action 
#=============================================================================
def dtmf_input_help(state, actuator, frame):
    if frame[':properties'].has_key(':[dtmf_key.dtmf_zero]'):
        return (SpeechAct('request', [('help', None)]))
    return None

def dtmf_input_affirm(state, actuator, frame):
    if frame[':properties'].has_key(':[dtmf_key.dtmf_one]'):
        return (SpeechAct('affirm', []))
    return None

def dtmf_input_negate(state, actuator, frame):
    if frame[':properties'].has_key(':[dtmf_key.dtmf_three]'):
        return (SpeechAct('negate', []))
    return None

def dtmf_input_eval_success(state, actuator, frame):
    if frame[':properties'].has_key(':[dtmf_key.dtmf_four]'):
        return (SpeechAct('evaluate', [('success', None)]))
    return None

def dtmf_input_eval_fail(state, actuator, frame):
    if frame[':properties'].has_key(':[dtmf_key.dtmf_six]'):
        return (SpeechAct('evaluate', [('fail', None)]))
    return None

def speech_input_help(state, actuator, frame):
    if frame[':properties'].has_key(':[generic.help.general_help]'):
        return (SpeechAct('request', [('help', None)]))
    return None


def _register_uncovered_place(state, place):
    if not hasattr(state, 'uncovered_place'):
        state.uncovered_place = {}
    state.uncovered_place[place] = True
 
    
def _register_place_type(state, place, parse):
    if not hasattr(state, 'place_type'):
        state.place_type = {}
    state.place_type[place] = 'stop'
    sub_parse = parse[parse.find(place)-20:parse.find(place)] # dirty hack
#    app_logger.info('place %s, sub_parse %s'%(place, sub_parse))
    if sub_parse.find('neighborhood') > -1:
        state.place_type[place] = 'neighborhood'

    
def speech_input_uncovered_from_desc(state, actuator, frame):
    if frame[':properties'].has_key(
            ':[1_singleplace.stop_name.uncovered_place]'):
        system_act = state.history_system_acts[-1]
#        if (not (system_act.act_type == 'request' and 
#                 system_act.has_relevant_arg('to')) and 
#            not (system_act.act_type == 'expl-conf' and 
#                 system_act.has_relevant_arg('to'))):
        if ({'act_type': 'request', 'concept': 'to'} not in
            state.last_speech_out_event and
            {'act_type': 'expl-conf', 'concept': 'to'} not in
            state.last_speech_out_event):
            # register the uncovered_place for future reference
            _register_uncovered_place(
                state, 
                frame[':properties'][':[1_singleplace.stop_name.uncovered_place]'])
            _register_place_type(
                state, 
                frame[':properties'][':[1_singleplace.stop_name.covered_place]'], 
                frame[':properties'][':parse_str'])
            return (SpeechAct(
                        'inform',
                        [('from',
                         frame[':properties'][':[1_singleplace.stop_name.uncovered_place]'])]))
    elif frame[':properties'].has_key(':[2_departureplace.stop_name.uncovered_place]'):
        _register_uncovered_place(
            state, 
            frame[':properties'][':[2_departureplace.stop_name.uncovered_place]'])
        _register_place_type(
            state, 
            frame[':properties'][':[2_departureplace.stop_name.uncovered_place]'], 
            frame[':properties'][':parse_str'])
        return (SpeechAct(
                    'inform', 
                    [('from', 
                     frame[':properties'][':[2_departureplace.stop_name.uncovered_place]'])]))
    return None


def speech_input_uncovered_to_desc(state, actuator, frame):
    if frame[':properties'].has_key(':[1_singleplace.stop_name.uncovered_place]'):
        system_act = state.history_system_acts[-1]
#        if (not (system_act.act_type == 'request' and 
#                 system_act.has_relevant_arg('from')) and
#            not (system_act.act_type == 'expl-conf' and 
#                 system_act.has_relevant_arg('from'))):
        if ({'act_type': 'request', 'concept': 'from'} not in
            state.last_speech_out_event and
            {'act_type': 'expl-conf', 'concept': 'from'} not in
            state.last_speech_out_event):
            # register the uncovered_place for future reference
            _register_uncovered_place(
                state, 
                frame[':properties'][':[1_singleplace.stop_name.uncovered_place]'])
            _register_place_type(
                state, 
                frame[':properties'][':[1_singleplace.stop_name.covered_place]'], 
                frame[':properties'][':parse_str'])
            return (SpeechAct(
                        'inform', 
                        [('to', 
                         frame[':properties'][':[1_singleplace.stop_name.uncovered_place]'])]))
    elif frame[':properties'].has_key(':[3_arrivalplace.stop_name.uncovered_place]'):
        _register_uncovered_place(
            state, 
            frame[':properties'][':[3_arrivalplace.stop_name.uncovered_place]'])
        _register_place_type(
            state, 
            frame[':properties'][':[3_arrivalplace.stop_name.uncovered_place]'], 
            frame[':properties'][':parse_str'])
        return (SpeechAct(
                    'inform', 
                    [('to', 
                     frame[':properties'][':[3_arrivalplace.stop_name.uncovered_place]'])]))
    return None


def speech_input_covered_from_desc(state, actuator, frame):
    if frame[':properties'].has_key(':[1_singleplace.stop_name.covered_place]'):
#         system_act = state.history_system_acts[-1]
#         if (not (system_act.act_type == 'request' and 
#                  system_act.has_relevant_arg('to')) and
#             not (system_act.act_type == 'expl-conf' and 
#                  system_act.has_relevant_arg('to'))):
        if ({'act_type': 'request', 'concept': 'to'} not in
            state.last_speech_out_event and
            {'act_type': 'expl-conf', 'concept': 'to'} not in
            state.last_speech_out_event):
            _register_place_type(
                state, 
                frame[':properties'][':[1_singleplace.stop_name.covered_place]'], 
                frame[':properties'][':parse_str'])
            return (SpeechAct(
                        'inform', 
                        [('from', 
                         frame[':properties'][':[1_singleplace.stop_name.covered_place]'])]))
    elif frame[':properties'].has_key(':[2_departureplace.stop_name.covered_place]'):
        _register_place_type(
            state, 
            frame[':properties'][':[2_departureplace.stop_name.covered_place]'], 
            frame[':properties'][':parse_str'])
        return (SpeechAct(
                    'inform', 
                    [('from', 
                     frame[':properties'][':[2_departureplace.stop_name.covered_place]'])]))
    return None


def speech_input_covered_to_desc(state, actuator, frame):
    if frame[':properties'].has_key(':[1_singleplace.stop_name.covered_place]'):
#         system_act = state.history_system_acts[-1]
#         if (not (system_act.act_type == 'request' and 
#                  system_act.has_relevant_arg('from')) and
#             not (system_act.act_type == 'expl-conf' and 
#                  system_act.has_relevant_arg('from'))):
        if ({'act_type': 'request', 'concept': 'from'} not in
            state.last_speech_out_event and
            {'act_type': 'expl-conf', 'concept': 'from'} not in
            state.last_speech_out_event):
            _register_place_type(
                state, 
                frame[':properties'][':[1_singleplace.stop_name.covered_place]'], 
                frame[':properties'][':parse_str'])
            return (SpeechAct(
                        'inform', 
                        [('to', 
                         frame[':properties'][':[1_singleplace.stop_name.covered_place]'])]))
    elif frame[':properties'].has_key(':[3_arrivalplace.stop_name.covered_place]'):
        _register_place_type(
            state, 
            frame[':properties'][':[3_arrivalplace.stop_name.covered_place]'], 
            frame[':properties'][':parse_str'])
        return (SpeechAct(
                    'inform', 
                    [('to', 
                     frame[':properties'][':[3_arrivalplace.stop_name.covered_place]'])]))
    return None


def speech_input_route(state, actuator, frame):
    if frame[':properties'].has_key(':[0_busnumber.route.0_uncovered_route]'):
        if not hasattr(state, 'uncovered_route'): 
            state.uncovered_route = {}
        state.uncovered_route[frame[':properties'][':[0_busnumber.route.0_uncovered_route]']] = True
        return (SpeechAct(
                    'inform', 
                    [('route', 
                     frame[':properties'][':[0_busnumber.route.0_uncovered_route]'])]))
    elif frame[':properties'].has_key(':[0_busnumber.route.0_discontinued_route]'):
        if not hasattr(state, 'discontinued_route'): 
            state.discontinued_route = {}
        state.discontinued_route[frame[':properties'][':[0_busnumber.route.0_discontinued_route]']] = True
        return (SpeechAct(
                    'inform', 
                    [('route', 
                     frame[':properties'][':[0_busnumber.route.0_discontinued_route]'])]))
    elif frame[':properties'].has_key(':[0_busnumber.route.0_covered_route]'):
        return (SpeechAct('inform', [('route', frame[':properties'][':[0_busnumber.route.0_covered_route]'])]))
    return None


def _register_time_info(state, time, info):
    if not hasattr(state, 'time_info'):
        state.time_infos = {}
    state.time_infos[time] = info

    
def speech_input_time(state, actuator, frame):
    if frame[':properties'].has_key(':[4_datetime]'):
        out_events = EventList()
        out_events.add_event(
            'execute',
            ExecutionEvent(
                {'operation': 'time_parse',
                 'time': frame[':properties'][':gal_slotsframe']}))
        actuator.execute(state, out_events)

        time_parse = state.time_parses[frame[':properties'][':gal_slotsframe']]
        
        date_time = {}
        if (time_parse.has_key(':valid_date') and 
                time_parse[':valid_date'] == 'true'):
            date_time['weekday'] = time_parse[':weekday']
            date_time['year'] = time_parse[':year']
            date_time['day'] = time_parse[':day']
            date_time['month'] = time_parse[':month']
            
        got_time = False
        if (time_parse.has_key(':valid_time') and 
                time_parse.has_key(':start_time') and 
                time_parse.has_key(':end_time') and 
                time_parse[':valid_time'] == 'true' and 
                time_parse[':start_time'] == time_parse[':end_time'] and 
                time_parse[':start_time'] != '' and 
                time_parse[':start_time'] != '1199'):
            dt_time = int(time_parse[':start_time'])
            app_logger.info('dt_time: %d'%dt_time)
            iTime = datetime.now(); iTime = iTime.hour*100 + iTime.minute
            app_logger.info('iTime: %d' % iTime)
            if dt_time >= 1200: 
                dt_time -= 1200
            app_logger.info('dt_time: %d' % dt_time)
            if iTime < 1200:
                if dt_time < iTime - 15: 
                    dt_time += 1200
                app_logger.info('a dt_time: %d' % dt_time)
            else:
                if dt_time >= iTime - 1215: 
                    dt_time += 1200
                app_logger.info('b dt_time: %d' % dt_time)
            if time_parse[':timeperiod_spec'] == 'now ':
                date_time['value'] = '%d' % dt_time
                date_time['now'] = 'true'
            elif (time_parse[':timeperiod_spec'] == '' and 
                  time_parse[':day'] == '-1'):
                date_time['value'] = '%d' % dt_time
            else:
                date_time['value'] = time_parse[':start_time']
            got_time = True   

        if got_time:   
            parse = frame[':properties'][':parse_str']
            if (parse.find('[4_ArrivalTime]') > -1 or
                    parse.find('[3_ArrivalPlace]') > -1 or
                    parse.find('[DisambiguateArrival]') > -1):
                date_time['time_type'] = 'arrival'
            else:
                date_time['time_type'] = 'departure'
            if time_parse[':timeperiod_spec'] != '':
                date_time['period_spec'] = time_parse[':timeperiod_spec']
            if (time_parse.has_key(':timeperiod_spec') and 
                    time_parse[':timeperiod_spec'] == 'now '):
                _register_time_info(state, 'next', date_time.copy())
                app_logger.info('date_time: %s' % str(date_time))
                return (SpeechAct('inform', [('time.rel', 'next')]))
            else:
                _register_time_info(state, date_time['value'], 
                                    date_time.copy())
                app_logger.info('date_time: %s' % str(date_time))
                return (SpeechAct('inform', 
                                   [('time.hour', date_time['value'])]))
        else:
            app_logger.info('No exact date time')
            return (SpeechAct('inform', [('time.underspec', None)]))

    if frame[':properties'].has_key(':[4_busafterthatrequest]'):
        app_logger.info('%s' % frame[':properties'][':[4_busafterthatrequest]'])
#         system_act = state.history_system_acts[-1]
#         if (system_act.act_type == 'request' and 
#             system_act.has_relevant_arg('time')): 
        if ({'act_type': 'request', 'concept': 'time'} in
            state.last_speech_out_event):
            date_time = {}
            date_time['period_spec'] = 'now'
            date_time['time_type'] = 'departure'
            date_time['now'] = 'true'
            _register_time_info(state, 'next', date_time.copy())
            app_logger.info('date_time: %s' % str(date_time))
            return (SpeechAct('inform', [('time.rel', 'next')]))
    return None


def speech_input_next_bus(state, actuator, frame):
    if frame[':properties'].has_key(':[4_busafterthatrequest]'):
#         system_act = state.history_system_acts[-1]
#         if (system_act.act_type == 'example' and 
#             system_act.concepts['act'] == 'nextquery'):
        if ({'act_type': 'example', 'concept': 'act', 'value': 'nextquery'} in
            state.last_speech_out_event):
            state.next_query = 'nextbus'
            return (SpeechAct('nextbus', []))
    return None


def speech_input_previous_bus(state, actuator, frame):
    if frame[':properties'].has_key(':[4_busbeforethatrequest]'):
#         system_act = state.history_system_acts[-1]
#         if (system_act.act_type == 'example' and 
#                 system_act.concepts['act'] == 'nextquery'):
        if ({'act_type': 'example', 'concept': 'act', 'value': 'nextquery'} in
            state.last_speech_out_event):
            state.next_query = 'prevbus' 
            return (SpeechAct('prevbus', []))
    return None


def speech_input_quit(state, actuator, frame):
    if frame[':properties'].has_key(':[generic.quit]'):
#         system_act = state.history_system_acts[-1]
#         if (system_act.act_type == 'example' and 
#                 system_act.concepts['act'] == 'nextquery' or
#                 system_act.act_type == 'canthelp.no_connection'):
        if ({'act_type': 'example', 'concept': 'act', 'value': 'nextquery'} in
            state.last_speech_out_event or
            {'act_type': 'canthelp.no_connection'} in
            state.last_speech_out_event):
            state.next_query = 'bye' 
            return (SpeechAct('bye', []))
    return None


def speech_input_startover(state, actuator, frame):
    app_logger.info('semantic restart')
    if frame[':properties'].has_key(':[generic.startover]'):
#         system_act = state.history_system_acts[-1]
#         if (system_act.act_type == 'example' and 
#                 system_act.concepts['act'] == 'nextquery' or
#                 system_act.act_type == 'canthelp.no_connection'):
        if ({'act_type': 'example', 'concept': 'act', 'value': 'nextquery'} in
            state.last_speech_out_event or
            {'act_type': 'canthelp.no_connection'} in
            state.last_speech_out_event):
            state.next_query = 'restart' 
            return (SpeechAct('restart', []))
    return None


def speech_input_affirm(state, actuator, frame):
    if frame[':properties'].has_key(':[generic.yes]'):
        return (SpeechAct('affirm', []))
    return None


def speech_input_negate(state, actuator, frame):
    if frame[':properties'].has_key(':[generic.no]'):
        return (SpeechAct('negate', []))
    return None


# list of semantic mapping functions
speech_input_mapping_functions = [
dtmf_input_help,
dtmf_input_affirm,
dtmf_input_negate,
dtmf_input_eval_success,
dtmf_input_eval_fail,
speech_input_help,
speech_input_uncovered_from_desc,
speech_input_uncovered_to_desc,
speech_input_covered_from_desc,
speech_input_covered_to_desc,
speech_input_route,
speech_input_time,
speech_input_next_bus,
speech_input_previous_bus,
speech_input_quit,
speech_input_startover,
speech_input_affirm,
speech_input_negate,
]


#===============================================================================
# Parse the input frame to extract N-best list;
# currently, Everest only supports 1-best.
# Return the parsed results, input hyps.
#===============================================================================
def parse(state, actuator, frame):
    # when n-bests available, repeat the following as many times as the number of hypotheses
    turn = SpeechTurn()
    score = float(frame[':properties'][':confidence'])
    for fn in speech_input_mapping_functions:
        act = fn(state, actuator, frame)
        if act:
            turn.append(act)
    nbest = SpeechNbest()
    nbest.append(turn, score)
    event = SpeechEvent(nbest)
    app_logger.info('\nSpeech in event:\n' + str(event))
    return event
            

