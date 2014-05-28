
import logging
from pprint import pformat

from dialog_core.dialog_datatype import SystemAction, Method

app_logger = logging.getLogger('DomainOutput')


#===============================================================================
# Concepts which belief tracking performs on 
#===============================================================================
concepts = ['route', 'from', 'to', 'date', 'time']


#===============================================================================
# Concepts which belief tracking performs on 
#===============================================================================
model_path = './model/2-1.model'
prior_model_path = './model/2-1-prior.model'


#===============================================================================
# Main task
#===============================================================================
main_tasks = [('task_root',),]


#===============================================================================
# Composite methods for Let's Go
# In each planning recipe and action, the first argument is the current state. 
# The rest of the arguments must match the arguments of the task that the method is for. 
#===============================================================================
bus_schedule = Method('composite', 'bus_schedule')
def bus_schedule_subtasks(state):
    return [
            ('opening',),
            ('handle_from',),
            ('handle_to',),
            ('handle_time',),
            ('provide_schedule',),
            ('handle_next_query',),
            ]
bus_schedule.custom_get_subtasks = bus_schedule_subtasks


ack_affirm = Method('atomic', 'ack_affirm')
def ack_affirm_precondition(state):
    if len(state.history_system_acts) > 0 and len(state.history_input_hyps) > 0:
        system_act = state.history_system_acts[-1]
        app_logger.info(pformat(state.history_input_hyps[-1]))
        top_input_hyp = state.history_input_hyps[-1][0]
        user_act = top_input_hyp.user_acts[0]
        if system_act.act_type == 'expl-conf' and user_act.act_type == 'affirm':
            return True
    return False
ack_affirm.custom_check_precondition = ack_affirm_precondition
def ack_affirm_generate_system_act(state): 
    return SystemAction('ack', {},
                        nlg_args = {'type': 'inform', 'object': 'confirm_okay', 'args': {}})
ack_affirm.custom_generate_system_act = ack_affirm_generate_system_act
def ack_affirm_check_completion(state):
    return False
ack_affirm.custom_check_completion = ack_affirm_check_completion
ack_affirm.priority = 1000

opening = Method('composite', 'opening')
def opening_subtasks(state):
    return [('inform_greet',), ('inform_how_to_get_help',)]
opening.custom_get_subtasks = opening_subtasks


inform_greet = Method('atomic', 'inform_greet')
def inform_greet_generate_system_act(state):
    return SystemAction('hello', {}, 
                        nlg_args = {'type': 'inform', 'object': 'welcome', 'args': {}}, 
                        asr_config = 'set_dtmf_len = 1, set_lm = first_query', 
                        tts_config = '''   :non-listening "true"
   :non-repeatable "true"
''')
inform_greet.custom_generate_system_act = inform_greet_generate_system_act
def inform_greet_check_completion(state):
    if hasattr(state, 'restarted') or state.get_plan_execution_state('inform_greet'):
        return True
    return False
inform_greet.custom_check_completion = inform_greet_check_completion


inform_how_to_get_help = Method('atomic', 'inform_how_to_get_help')
def inform_how_to_get_help_generate_system_act(state):
    return SystemAction('example', {'act': 'help'},
                        nlg_args = {'type': 'inform', 'object': 'how_to_get_help', 'args': {}}, 
                        asr_config = 'set_dtmf_len = 1, set_lm = first_query', 
                        tts_config = '''   :non-listening "true"
   :non-repeatable "true"
''')
inform_how_to_get_help.custom_generate_system_act = inform_how_to_get_help_generate_system_act
def inform_how_to_get_help_check_completion(state):
    if hasattr(state, 'restarted') or state.get_plan_execution_state('inform_how_to_get_help'):
        return True
    return False
inform_how_to_get_help.custom_check_completion = inform_how_to_get_help_check_completion


# Handling from
handle_from = Method('composite', 'handle_from')
def handle_from_subtasks(state):
    return [('elicit_from',), ('execute_from_db_query',)]
handle_from.custom_get_subtasks = handle_from_subtasks


request_from = Method('atomic', 'request_from')
def request_from_generate_system_act(state):
    return SystemAction('request', {'from': None},
                        nlg_args = {'type': 'request', 
                                    'object': 'query.departure_place', 
                                    'args': {}}, 
                        asr_config = 'set_dtmf_len = 1, set_lm = place')
request_from.custom_generate_system_act = request_from_generate_system_act
def request_from_check_completion(state):
    if len(state.belief_state.concepts['from']['hyps']) > 0 and\
    state.belief_state.concepts['from']['hyps'][0]['score'] > 0.8:
        return True
    return False
request_from.custom_check_completion = request_from_check_completion
    
    
explicit_confirm_from = Method('atomic', 'explicit_confirm_from')
def explicit_confirm_from_generate_system_act(state):
    value = state.belief_state.concepts['from']['hyps'][0]['value']
    query = 'query.departure_place\t{\nname\t%s\ntype\t%s\n}\n'%(value, state.place_type[value])
    return SystemAction('expl-conf', {'from.desc': value},
                        nlg_args = {'type': 'explicit_confirm', 
                                    'object': 'query.departure_place', 
                                    'args': {'query': query}}, 
                        asr_config = 'set_dtmf_len = 1, set_lm = yes_no')
explicit_confirm_from.custom_generate_system_act = explicit_confirm_from_generate_system_act
def explicit_confirm_from_check_completion(state):
    if len(state.belief_state.concepts['from']['hyps']) > 0 and\
    state.belief_state.concepts['from']['hyps'][0]['score'] > 0.8:
        return True
    return False
explicit_confirm_from.custom_check_completion = explicit_confirm_from_check_completion
def explicit_confirm_from_check_precondition(state):
    if len(state.belief_state.concepts['from']['hyps']) == 0:
        return False
    return True
explicit_confirm_from.custom_check_precondition = explicit_confirm_from_check_precondition
explicit_confirm_from.priority = 10


execute_from_db_query = Method('atomic', 'execute_from_db_query')
def execute_from_db_query_generate_system_act(state):
    place = state.belief_state.concepts['from']['hyps'][0]['value']
    return SystemAction('execute', {'operation': 'place_query', 
                                          'place': place, 
                                          'place_type': state.place_type[place]})
execute_from_db_query.custom_generate_system_act = execute_from_db_query_generate_system_act
def execute_from_db_query_check_completion(state):
    place = state.belief_state.concepts['from']['hyps'][0]['value']
    if hasattr(state, 'place_query_results') and place in state.place_query_results:
        return True
    return False
execute_from_db_query.custom_check_completion = execute_from_db_query_check_completion
def execute_from_db_query_check_precondition(state):
    if len(state.belief_state.concepts['from']['hyps']) == 0:
        return False
    return True
execute_from_db_query.custom_check_precondition = execute_from_db_query_check_precondition


# Handling to
handle_to = Method('composite', 'handle_to')
def handle_to_subtasks(state):
    return [('elicit_to',), ('execute_to_db_query',)]
handle_to.custom_get_subtasks = handle_to_subtasks


request_to = Method('atomic', 'request_to')
def request_to_generate_system_act(state):
    return SystemAction('request', {'to': None},
                        nlg_args = {'type': 'request', 
                                    'object': 'query.arrival_place', 
                                    'args': {}}, 
                        asr_config = 'set_dtmf_len = 1, set_lm = place')
request_to.custom_generate_system_act = request_to_generate_system_act
def request_to_check_completion(state):
    if len(state.belief_state.concepts['to']['hyps']) > 0 and\
    state.belief_state.concepts['to']['hyps'][0]['score'] > 0.8:
        return True
    return False
request_to.custom_check_completion = request_to_check_completion
    
    
explicit_confirm_to = Method('atomic', 'explicit_confirm_to')
def explicit_confirm_to_generate_system_act(state):
    value = state.belief_state.concepts['to']['hyps'][0]['value']
    query = 'query.arrival_place\t{\nname\t%s\ntype\t%s\n}\n'%(value, state.place_type[value])
    return SystemAction('expl-conf', {'to.desc': value},
                        nlg_args = {'type': 'explicit_confirm', 
                                    'object': 'query.arrival_place', 
                                    'args': {'query': query}}, 
                        asr_config = 'set_dtmf_len = 1, set_lm = yes_no')
explicit_confirm_to.custom_generate_system_act = explicit_confirm_to_generate_system_act
def explicit_confirm_to_check_completion(state):
    if len(state.belief_state.concepts['to']['hyps']) > 0 and\
    state.belief_state.concepts['to']['hyps'][0]['score'] > 0.8:
        return True
    return False
explicit_confirm_to.custom_check_completion = explicit_confirm_to_check_completion
def explicit_confirm_to_check_precondition(state):
    if len(state.belief_state.concepts['to']['hyps']) == 0:
        return False
    return True
explicit_confirm_to.custom_check_precondition = explicit_confirm_to_check_precondition
explicit_confirm_to.priority = 10


execute_to_db_query = Method('atomic', 'execute_to_db_query')
def execute_to_db_query_generate_system_act(state):
    place = state.belief_state.concepts['to']['hyps'][0]['value']
    return SystemAction('execute', {'operation': 'place_query', 
                                          'place': place, 
                                          'place_type': state.place_type[place]})
execute_to_db_query.custom_generate_system_act = execute_to_db_query_generate_system_act
def execute_to_db_query_check_completion(state):
    place = state.belief_state.concepts['to']['hyps'][0]['value']
    if hasattr(state, 'place_query_results') and place in state.place_query_results:
        return True
    return False
execute_to_db_query.custom_check_completion = execute_to_db_query_check_completion
def execute_to_db_query_check_precondition(state):
    if len(state.belief_state.concepts['to']['hyps']) == 0:
        return False
    return True
execute_to_db_query.custom_check_precondition = execute_to_db_query_check_precondition


# Handling time
request_time = Method('atomic', 'request_time')
def request_time_generate_system_act(state):
    return SystemAction('request', {'time': None},
                        nlg_args = {'type': 'request', 
                                    'object': 'query.travel_time', 
                                    'args': {}}, 
                        asr_config = 'set_dtmf_len = 1, set_lm = time')
request_time.custom_generate_system_act = request_time_generate_system_act
def request_time_check_completion(state):
    if len(state.belief_state.concepts['time']['hyps']) > 0 and\
    state.belief_state.concepts['time']['hyps'][0]['score'] > 0.3:
        return True
    return False
request_time.custom_check_completion = request_time_check_completion
    
    
explicit_confirm_time = Method('atomic', 'explicit_confirm_time')
def explicit_confirm_time_generate_system_act(state):
    value = state.belief_state.concepts['time']['hyps'][0]['value']
    time_info = state.time_infos[value]
    app_logger.info('time info: %s'%str(time_info))
    if 'now' in time_info:
        query = 'query.travel_time.time\t{\nvalue\t%s\nnow\t%s\ntype\t%s\n}\n'%\
        (time_info['value'], time_info['now'], time_info['time_type'])
    elif 'value' in time_info:
        query = 'query.travel_time.time\t{\nvalue\t%s\ntype\t%s\n}\n'%\
        (time_info['value'], time_info['time_type'])
    else:
        query = 'query.travel_time.time\t{\nnow\t%s\ntype\t%s\n}\n'%\
        (time_info['now'], time_info['time_type'])

    return SystemAction('expl-conf', {'time.value': value},
                        nlg_args = {'type': 'explicit_confirm', 
                                    'object': 'query.travel_time', 
                                    'args': {'query': query}}, 
                        asr_config = 'set_dtmf_len = 1, set_lm = yes_no')
explicit_confirm_time.custom_generate_system_act = explicit_confirm_time_generate_system_act
def explicit_confirm_time_check_completion(state):
    if len(state.belief_state.concepts['time']['hyps']) > 0 and\
    state.belief_state.concepts['time']['hyps'][0]['score'] > 0.3:
        return True
    return False
explicit_confirm_time.custom_check_completion = explicit_confirm_time_check_completion
def explicit_confirm_time_check_precondition(state):
    if len(state.belief_state.concepts['time']['hyps']) == 0:
        return False
    return True
explicit_confirm_time.custom_check_precondition = explicit_confirm_time_check_precondition
explicit_confirm_time.priority = 10


# Provide schedule
provide_schedule = Method('composite', 'provide_schedule')
def provide_schedule_subtasks(state):
    return [('inform_looking_up_schedule',), ('execute_schedule_db_query',), ('inform_schedule',)]
provide_schedule.custom_get_subtasks = provide_schedule_subtasks
def provide_schedule_check_precondition(state):
    if len(state.belief_state.concepts['from']['hyps']) == 0 or\
    len(state.belief_state.concepts['to']['hyps']) == 0 or\
    len(state.belief_state.concepts['time']['hyps']) == 0:
        return False
    return True
provide_schedule.custom_check_precondition = provide_schedule_check_precondition


inform_looking_up_schedule = Method('atomic', 'inform_looking_up_schedule')
def inform_looking_up_schedule_generate_system_act(state):
    if hasattr(state, 'next_query'):
        return SystemAction('hold-on', {}, 
                            nlg_args = {'type': 'inform', 'object': 'looking_up_database_subsequent', 'args': {}}, 
                            asr_config = 'set_dtmf_len = 1, set_lm = first_query', 
                            tts_config = '''   :non-listening "true"
       :non-repeatable "true"
    ''')
    else:
        return SystemAction('hold-on', {}, 
                            nlg_args = {'type': 'inform', 'object': 'looking_up_database_first', 'args': {}}, 
                            asr_config = 'set_dtmf_len = 1, set_lm = first_query', 
                            tts_config = '''   :non-listening "true"
       :non-repeatable "true"
    ''')
inform_looking_up_schedule.custom_generate_system_act = inform_looking_up_schedule_generate_system_act


execute_schedule_db_query = Method('atomic', 'execute_schedule_db_query')
def execute_schedule_db_query_generate_system_act(state):
    place_from = state.belief_state.concepts['from']['hyps'][0]['value']
    place_to = state.belief_state.concepts['to']['hyps'][0]['value']
    time = state.belief_state.concepts['time']['hyps'][0]['value']
    if hasattr(state, 'next_query'):
        return SystemAction('execute', {'operation': 'subsequent_schedule_query',
                                              'from': place_from,
                                              'to': place_to,
                                              'time': time})
    else:
        return SystemAction('execute', {'operation': 'schedule_query',
                                              'from': place_from,
                                              'to': place_to,
                                              'time': time})
execute_schedule_db_query.custom_generate_system_act = execute_schedule_db_query_generate_system_act


inform_schedule = Method('atomic', 'inform_schedule')
def inform_schedule_generate_system_act(state):
    query = state.schedule_constraints
    result = '\n' + '\n'.join([x.strip() for x in state.schedule_query_result[':outframe'].split('\n')[1:-2]]).replace('new_result', 'result') + '\n'
    if state.schedule_query_result[':outframe'].find('failed\t0') > -1: 
        return SystemAction('schedule', {},
                            nlg_args = {'type': 'inform', 
                                        'object': 'result', 
                                        'args': {'query': query, 'result': result}},
                            tts_config = '''   :non-listening "true"
   :non-repeatable "true"
''')
    else:
        return SystemAction('canthelp.schedule', {},
                            nlg_args = {'type': 'inform', 
                                        'object': 'error', 
                                        'args': {'query': query, 'result': result}},
                            tts_config = '''   :non-listening "true"
   :non-repeatable "true"
''')
inform_schedule.custom_generate_system_act = inform_schedule_generate_system_act
def inform_schedule_check_precondition(state):
    if not hasattr(state, 'schedule_query_result'):
        return False
    return True
inform_schedule.custom_check_precondition = inform_schedule_check_precondition


# Next query
handle_next_query = Method('composite', 'handle_next_query')
def handle_next_query_subtasks(state):
    return [('request_next_query',), ('process_next_query',)]
handle_next_query.custom_get_subtasks = handle_next_query_subtasks


request_next_query = Method('atomic', 'request_next_query')
def request_next_query_generate_system_act(state):
    if state.schedule_query_result[':outframe'].find('failed\t0') > -1: 
        return SystemAction('example', {'act': 'nextquery'},
                                  nlg_args = {'type': 'request', 'object': 'next_query', 'args': {}},
                                  asr_config = 'set_dtmf_len = 1, set_lm = next_query')
    else:
        return SystemAction('canthelp.no_connection', {},
                                  nlg_args = {'type': 'request', 'object': 'next_query_error', 'args': {}})
request_next_query.custom_generate_system_act = request_next_query_generate_system_act
def request_next_query_check_completion(state):
    if hasattr(state, 'next_query'):
        return True
    return False
request_next_query.custom_check_completion = request_next_query_check_completion


# Process addition schedule queries
process_next_bus = Method('composite', 'process_next_bus')
def process_next_bus_subtasks(state):
    return [('execute_reset_provide_schedule',), ('provide_schedule',), ('execute_reset_next_query',)]
process_next_bus.custom_get_subtasks = process_next_bus_subtasks
def process_next_bus_check_precondition(state):
    if hasattr(state, 'next_query') and state.next_query in ['nextbus', 'prevbus']:
        return True
    return False
process_next_bus.custom_check_precondition = process_next_bus_check_precondition


execute_reset_provide_schedule = Method('atomic', 'execute_reset_provide_schedule')
def execute_reset_provide_schedule_function(state, actuator):
    state.set_plan_execution_state('inform_looking_up_schedule', False)
    state.set_plan_execution_state('execute_schedule_db_query', False)
    state.set_plan_execution_state('inform_schedule', False)
def execute_reset_provide_schedule_generate_system_act(state):
    return SystemAction('execute', {'operation': 'user_defined_function', 'function': execute_reset_provide_schedule_function})
execute_reset_provide_schedule.custom_generate_system_act = execute_reset_provide_schedule_generate_system_act


execute_reset_next_query = Method('atomic', 'execute_reset_next_query')
def execute_reset_next_query_function(state, actuator):
    delattr(state, 'next_query')
    state.set_plan_execution_state('execute_reset_provide_schedule', False)
def execute_reset_next_query_generate_system_act(state):
    return SystemAction('execute', {'operation': 'user_defined_function', 'function': execute_reset_next_query_function})
execute_reset_next_query.custom_generate_system_act = execute_reset_next_query_generate_system_act
def execute_reset_next_query_check_completion(state):
    return False
execute_reset_next_query.custom_check_completion = execute_reset_next_query_check_completion


# Process restart request
process_restart = Method('composite', 'process_restart')
def process_restart_subtasks(state):
    return [('inform_restart',), ('execute_restart',)]
process_restart.custom_get_subtasks = process_restart_subtasks
def process_restart_check_precondition(state):
    if hasattr(state, 'next_query') and state.next_query == 'restart':
        return True
    return False
process_restart.custom_check_precondition = process_restart_check_precondition


inform_restart = Method('atomic', 'inform_restart')
def inform_restart_generate_system_act(state):
    return SystemAction('restart', {}, 
                        nlg_args = {'type': 'inform', 'object': 'starting_new_query', 'args': {}})
inform_restart.custom_generate_system_act = inform_restart_generate_system_act


execute_restart = Method('atomic', 'execute_restart')
def execute_restart_function(state, actuator):
    state.reset()
    delattr(state, 'next_query')
    state.restarted = True
def execute_restart_generate_system_act(state):
    return SystemAction('execute', {'operation': 'user_defined_function', 'function': execute_restart_function})
execute_restart.custom_generate_system_act = execute_restart_generate_system_act
def execute_restart_check_completion(state):
    return False
execute_restart.custom_check_completion = execute_restart_check_completion


# Process close request
process_close = Method('composite', 'process_close')
def process_close_subtasks(state):
    return [('inform_close',), ('execute_close',)]
process_close.custom_get_subtasks = process_close_subtasks
def process_close_check_precondition(state):
    if hasattr(state, 'next_query') and state.next_query == 'bye':
        return True
    return False
process_close.custom_check_precondition = process_close_check_precondition


inform_close = Method('atomic', 'inform_close')
def inform_close_generate_system_act(state):
    return SystemAction('bye', {}, 
                        nlg_args = {'type': 'inform', 'object': 'goodbye', 'args': {}})
inform_close.custom_generate_system_act = inform_close_generate_system_act


execute_close = Method('atomic', 'execute_close')
def execute_close_generate_system_act(state):
    return SystemAction('execute', {'operation': 'close'})
execute_close.custom_generate_system_act = execute_close_generate_system_act


#===============================================================================
# Map from task to relevant methods
#===============================================================================
task_to_methods = {}
task_to_methods['task_root'] = [bus_schedule, ack_affirm]
task_to_methods['opening'] = [opening]
task_to_methods['inform_greet'] = [inform_greet]
task_to_methods['inform_how_to_get_help'] = [inform_how_to_get_help]

task_to_methods['handle_from'] = [handle_from]
task_to_methods['elicit_from'] = [request_from, explicit_confirm_from]
task_to_methods['execute_from_db_query'] = [execute_from_db_query]

task_to_methods['handle_to'] = [handle_to]
task_to_methods['elicit_to'] = [request_to, explicit_confirm_to]
task_to_methods['execute_to_db_query'] = [execute_to_db_query]

task_to_methods['handle_time'] = [request_time, explicit_confirm_time]

task_to_methods['provide_schedule'] = [provide_schedule]
task_to_methods['inform_looking_up_schedule'] = [inform_looking_up_schedule]
task_to_methods['execute_schedule_db_query'] = [execute_schedule_db_query]
task_to_methods['inform_schedule'] = [inform_schedule]

task_to_methods['handle_next_query'] = [handle_next_query]
task_to_methods['request_next_query'] = [request_next_query]
task_to_methods['process_next_query'] = [process_next_bus, process_restart, process_close]

task_to_methods['execute_reset_provide_schedule'] = [execute_reset_provide_schedule]
task_to_methods['execute_reset_next_query'] = [execute_reset_next_query]

task_to_methods['inform_restart'] = [inform_restart]
task_to_methods['execute_restart'] = [execute_restart]

task_to_methods['inform_close'] = [inform_close]
task_to_methods['execute_close'] = [execute_close]

