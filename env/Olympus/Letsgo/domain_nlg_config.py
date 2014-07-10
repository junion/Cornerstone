'''
Created on Jul 7, 2014

@author: Sungjin Lee
'''

def compose_msg(state, nlg_config):
    msg = '''{\nact\t${dialog_act}\nobject\t${object}\n_repeat_counter\t0\n${nlg_args}system_version\t1\n}'''
    msg = msg.replace('${dialog_act}', nlg_config['act'])
    msg = msg.replace('${object}', nlg_config['object'].replace('-', '.'))
    query = result = version = ''
    if 'type' in nlg_config:
        if nlg_config['type'] == 'concept':
            if nlg_config['concept'] == 'from':
                place = nlg_config['value']
                query = ('query.departure_place\t{\nname\t%s\ntype\t%s\n}\n' % 
                         (place, state.place_type[place]))
            if nlg_config['concept'] == 'to':
                place = nlg_config['value']
                query = ('query.arrival_place\t{\nname\t%s\ntype\t%s\n}\n' % 
                         (place, state.place_type[place]))
            if nlg_config['concept'] == 'time':
                time_info = state.time_infos[nlg_config['value']]
                if 'now' in time_info:
                    query = 'query.travel_time.time\t{\nvalue\t%s\nnow\t%s\ntype\t%s\n}\n'%\
                    (time_info['value'], time_info['now'], time_info['time_type'])
                elif 'value' in time_info:
                    query = 'query.travel_time.time\t{\nvalue\t%s\ntype\t%s\n}\n'%\
                    (time_info['value'], time_info['time_type'])
                else:
                    query = 'query.travel_time.time\t{\nnow\t%s\ntype\t%s\n}\n'%\
                    (time_info['now'], time_info['time_type'])
        elif nlg_config['type'] == 'schedule':
            query = state.schedule_constraints
    if 'result' in nlg_config:
        if nlg_config['result'] == 'schedule-query':
            result = ('\n' + 
                      '\n'.join([x.strip() for x in state.schedule_query_result[':outframe'].split('\n')[1:-2]]).replace('new_result', 'result') + 
                      '\n')
    if 'version' in nlg_config:
        version = nlg_config['version']
    msg = msg.replace('${nlg_args}', ''.join([query, result, version]))
    return msg
