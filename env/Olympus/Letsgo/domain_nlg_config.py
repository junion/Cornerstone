'''
Created on Jul 7, 2014

@author: Sungjin Lee
'''

def compose_msg(state, nlg_config):
    msg = '''{\nact\t${dialog_act}\nobject\t${object}\n_repeat_counter\t0\n${nlg_args}system_version\t1\n}'''
    msg = msg.replace('${dialog_act}', nlg_config['act'])
    msg = msg.replace('${object}', nlg_config['object'].replace('-', '.'))
    query = result = version = ''
    if 'query' in nlg_config:
        if nlg_config['concept'] == 'from':
            place = nlg_config['query']
            query = ('query.departure_place\t{\nname\t%s\ntype\t%s\n}\n' % 
                     (place, state.place_type[place]))
        if nlg_config['concept'] == 'to':
            place = nlg_config['query']
            query = ('query.arrival_place\t{\nname\t%s\ntype\t%s\n}\n' % 
                     (place, state.place_type[place]))
        if nlg_config['concept'] == 'time':
            time_info = state.time_infos[nlg_config['query']]
            if 'now' in time_info:
                query = 'query.travel_time.time\t{\nvalue\t%s\nnow\t%s\ntype\t%s\n}\n'%\
                (time_info['value'], time_info['now'], time_info['time_type'])
            elif 'value' in time_info:
                query = 'query.travel_time.time\t{\nvalue\t%s\ntype\t%s\n}\n'%\
                (time_info['value'], time_info['time_type'])
            else:
                query = 'query.travel_time.time\t{\nnow\t%s\ntype\t%s\n}\n'%\
                (time_info['now'], time_info['time_type'])
    if 'result' in nlg_config:
        result = nlg_config['result']
    if 'version' in nlg_config:
        version = nlg_config['version']
    msg = msg.replace('${nlg_args}', ''.join([query, result, version]))
    return msg
