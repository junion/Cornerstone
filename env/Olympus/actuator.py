import logging
from pprint import pformat

from config.global_config import get_config
from env.Olympus.Letsgo.domain_frame_template import *


MODULE_ID = 'Actuator'


class Actuator(object):
    #=========================================================================
    # Inits
    #=========================================================================
    def __init__(self, out_queue, result_queue):
        # load configs
        self.config = get_config()
        # logging
        self.app_logger = logging.getLogger(MODULE_ID)
        # queues for communication with the galaxy server 
        self.out_queue = out_queue
        self.result_queue = result_queue
    
    #=========================================================================
    # APIs
    #=========================================================================
    def parse_date_time(self, frame_fragment):
        content = parse_datetime_template
        frame_fragment = frame_fragment.replace('"','\\"')    
        content = content.replace('${gal_slotsframe}', frame_fragment)
        message = {'type':'GALAXYCALL',
                   'content':content}
        self.out_queue.put(message)
        result = self.result_queue.get()
        self.result_queue.task_done()
        return result
    
    def broadcast_dialog_state(self, state):
        state.dialog_state_index += 1
        content = dialog_state_frame_template
        content = content.replace('${dialog_state}', 
                                  self._compose_dialog_state(state))
        message = {'type':'GALAXYACTIONCALL',
           'content':content}
        self.out_queue.put(message)
        self.result_queue.get()
        self.result_queue.task_done()

    def reply_end_session(self):   
        self.app_logger.info('Reply end session message')    
        message = {'type':'ENDSESSION'}
        self.out_queue.put(message)
        
    def execute(self, state, events):
        speech_event = None
        nlg_config = None
        tts_config = None
        execute_event = None
        for event in events:
            if event['event_type'] == 'speech':
                speech_event = event['event']
            elif (event['event_type'] == 'config' and 
                  event['event'].module == 'NLG'):
                nlg_config = event['event'].config
            elif (event['event_type'] == 'config' and 
                  event['event'].module == 'TTS'):
                tts_config = event['event'].config
            elif (event['event_type'] == 'config' and 
                  event['event'].module == 'ASR'):
                state.asr_config = event['event'].config
            elif event['event_type'] == 'turn':
                state.turn_yield = (True if event['event'].args['yield'] 
                                    == 'true' else False)
            elif event['event_type'] == 'execute':
                execute_event = event['event']
        if speech_event:
            self._send_system_utterance_message(
                    state, nlg_config, tts_config)
            state.last_speech_out_event = speech_event
        elif execute_event:
            if execute_event['operation'] == 'place_query':
                self._send_place_query_message(
                        state, execute_event['place'], 
                        execute_event['place_type'])
            elif execute_event['operation'] == 'time_parse':
                self._send_time_parse_message(state, execute_event['time'])
            elif execute_event['operation'] == 'schedule_query':
                self._send_schedule_query_message(
                        state, execute_event['from'], execute_event['to'], 
                        execute_event['time'])
            elif execute_event['operation'] == 'subsequent_schedule_query':
                self._send_schedule_query_message(
                        state, execute_event['from'], execute_event['to'], 
                        execute_event['time'], next=state.next_query, 
                        prev_result=state.schedule_query_result)
            elif execute_event['operation'] == 'user_defined_function':
                execute_event['function'](state, self)
            elif execute_event['operation'] == 'close':
                self.send_finish_message()
    
    def send_wait_event_message(self):
        message = {'type':'WAITINTERACTIONEVENT'}
        self.out_queue.put(message)

    def send_finish_message(self):                                                        
        message = {'type':'DIALOGFINISHED'}
        self.out_queue.put(message)


    #=========================================================================
    # Private functions
    #=========================================================================
    def _compose_dialog_state(self, state):
        content = dialog_state_template
        content = content.replace('${turn_number}', str(state.turn_number))
        content = content.replace('${notify_prompts}', 
                                  ' '.join(state.notify_prompts))
        if state.asr_config:
            asr_config_str = []
            for key in state.asr_config.keys():
                asr_config_str.append(key+' = '+
                                      state.asr_config[key])
            self.app_logger.info(', '.join(asr_config_str))
            content = content.replace(
                            '${input_line_config}', 
                            ', '.join(asr_config_str))
        else:
            content = content.replace('${input_line_config}', '')
        return content

    def _send_system_utterance_message(self, state, nlg_config, tts_config):
        content = system_utterance_frame_template
        content = content.replace('${sess_id}', state.session_id)
        content = content.replace('${id_suffix}', '%03d'%state.id_suffix)
        content = content.replace('${utt_count}', str(state.utt_count))
        content = content.replace('${dialog_state_index}',
                                  str(state.dialog_state_index))
        content = content.replace('${dialog_state}', 
                                  self._compose_dialog_state(state))
        content = content.replace('${dialog_act}', 
                                  nlg_config['act'])
        content = content.replace('${object}', nlg_config['object'].replace('-', '.'))
#         if nlg_config['act'] == 'request':
#             floor_state = 'user'
#         elif nlg_config['act'] == 'inform':
#             floor_state = 'free'
#         else: 
#             floor_state = 'free'
        if state.turn_yield:
            floor_state = 'user'
        else: 
            floor_state = 'free'
        content = content.replace('${final_floor_status}', floor_state)
        query = result = version = ''
        if 'query' in nlg_config:
            query = nlg_config['query']
        if 'result' in nlg_config:
            result = nlg_config['result']
        if 'version' in nlg_config:
            version = nlg_config['version']
        content = content.replace('${nlg_args}', 
                                  ''.join([query, result, version]))
#         content = content.replace('${tts_config}', 
#                                   tts_config_event.configs)
        tts_config_str = []
        if tts_config:
            for key in tts_config.keys():
                tts_config_str.append('   :'+key+' "'+
                                      tts_config[key]+'"\n')
        content = content.replace('${tts_config}', ''.join(tts_config_str))
        self.app_logger.info(''.join(tts_config_str))
        message = {'type':'GALAXYACTIONCALL',
                   'content':content}
        state.notify_prompts.append(str(state.utt_count))
        state.id_suffix += 1
        state.utt_count += 1
        self.out_queue.put(message)
        self.result_queue.get()
        self.result_queue.task_done()

    def _send_place_query_message(self, state, place, place_type):
        # Backend lookup
        content = place_query_template
        
        content = content.replace('${name}', place)
        content = content.replace('${type}', place_type)
    
        message = {'type':'GALAXYCALL',
                   'content':content}

        self.out_queue.put(message)
        result = self.result_queue.get()
        self.result_queue.task_done()

        if not hasattr(state, 'place_query_results'):
            state.place_query_results = {}
            
        if result[':outframe'].find('failed\t1') > -1: 
            state.place_query_results[place] = result[':outframe']
        else:
            state.place_query_results[place] = result[':outframe']
            
        self.app_logger.info('%s' % pformat(state.place_query_results))


    def _send_time_parse_message(self, state, time):
        content = parse_datetime_template

        content = content.replace('${gal_slotsframe}', time.replace('"', '\\"'))

        message = {'type':'GALAXYCALL',
                   'content':content}
    
        self.out_queue.put(message)
        result = self.result_queue.get()
        self.result_queue.task_done()
        self.app_logger.info('Timeinfo: %s'%result.PPrint())

        if not hasattr(state, 'time_parses'):
            state.time_parses = {}
        
        state.time_parses[time] = result

        
    def _send_schedule_query_message(self, state, place_from, place_to, time, route=None, next=False, prev_result=None):
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
            constraints = constraints.replace('${route_number}','route_number\t%s\n'%route)
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
        
        self.out_queue.put(message)
        result = self.result_queue.get()
        self.result_queue.task_done()
        
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
            self.app_logger.info('Bus schedule: %s'%result.PPrint())
        else:
            self.app_logger.info('Backend query for schedule failed')

        state.schedule_query_result = result

