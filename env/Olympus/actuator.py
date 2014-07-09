'''
Created on Jul 4, 2014

@author: Sungjin Lee
'''

import logging
import importlib
from pprint import pformat

from config.global_config import get_config
from env.Olympus.frame_template import *


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
        # domain
        self.domain = self.config.get('Common', 'domain')
        self.executor = importlib.import_module(
                            self.domain + '.domain_execute')
        # modules for composing messages to other components in a SDS
        self.asr_config = importlib.import_module(
                            self.domain + '.domain_asr_config')
        self.nlg_config = importlib.import_module(
                            self.domain + '.domain_nlg_config')
        self.tts_config = importlib.import_module(
                            self.domain + '.domain_tts_config')

    
    #=========================================================================
    # APIs
    #=========================================================================
#     def parse_date_time(self, frame_fragment):
#         content = parse_datetime_template
#         frame_fragment = frame_fragment.replace('"','\\"')    
#         content = content.replace('${gal_slotsframe}', frame_fragment)
#         message = {'type':'GALAXYCALL',
#                    'content':content}
#         self.out_queue.put(message)
#         result = self.result_queue.get()
#         self.result_queue.task_done()
#         return result
    
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
            elif (event['event_type'] == 'session' and 
                  event['event'].status == 'end'):
                self.send_finish_message()
            elif event['event_type'] == 'execute':
                execute_event = event['event']
        if speech_event:
            self._send_system_utterance_message(
                    state, nlg_config, tts_config)
            state.last_speech_out_event = speech_event
        elif execute_event:
            self.executor.execute(state, execute_event, 
                                  self.out_queue, self.result_queue)
        return None
    
    def send_wait_event_message(self):
        message = {'type':'WAITINTERACTIONEVENT'}
        self.out_queue.put(message)

    def send_finish_message(self):                                                        
        message = {'type':'DIALOGFINISHED'}
        self.out_queue.put(message)

    def _compose_dialog_state(self, state):
        content = dialog_state_template
        content = content.replace('${turn_number}', str(state.turn_number))
        content = content.replace('${notify_prompts}', 
                                  ' '.join(state.notify_prompts))
        if state.asr_config:
            asr_msg = self.asr_config.compose_msg(state)
            content = content.replace('${input_line_config}', asr_msg)
        else:
            content = content.replace('${input_line_config}', '')
        return content

    def _send_system_utterance_message(self, state, nlg_config, tts_config):
        content = system_utterance_frame_template
        content = content.replace('${sess_id}', state.session_id)
        content = content.replace('${id_suffix}', '%03d' % state.id_suffix)
        content = content.replace('${utt_count}', str(state.utt_count))
        content = content.replace('${dialog_state_index}',
                                  str(state.dialog_state_index))
        content = content.replace('${dialog_state}', 
                                  self._compose_dialog_state(state))
        if state.turn_yield:
            floor_state = 'user'
        else: 
            floor_state = 'free'
        content = content.replace('${final_floor_status}', floor_state)
        nlg_msg = self.nlg_config.compose_msg(state, nlg_config)
        content = content.replace('${nlg_config}', nlg_msg)
        tts_msg = self.tts_config.compose_msg(state, tts_config)
        content = content.replace('${tts_config}', tts_msg)
        message = {'type':'GALAXYACTIONCALL',
                   'content':content}
        state.notify_prompts.append(str(state.utt_count))
        state.id_suffix += 1
        state.utt_count += 1
        self.out_queue.put(message)
        self.result_queue.get()
        self.result_queue.task_done()

