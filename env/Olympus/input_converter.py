'''
Created on May 28, 2014

@author: sungjinl
'''

import logging
import importlib
import time


MODULE_ID = 'InputConverter'


class InputConverter(object):
    def __init__(self, domain):
        # logging
        self.app_logger = logging.getLogger(MODULE_ID)

        # domain_semantics
        self.domain_semantics = importlib.import_module(domain)
        
        # load domain specifications
        self.parse_input_hyps = self.domain_semantics.parse_input_hyps
        
    # update dialog state by incorporating the input frame        
    def _update_state_for_event(self, frame):
        # call event handlers
        if frame.name == 'begin_session':
            event_type = 'begin_session'
            self._begin_session_handler(frame)

        elif frame.name == 'DialogManager.handle_event':
            event_type = frame[':event_type']
            self.self.app_logger.info('event_type: %s'%event_type)
            
            if event_type == 'user_utterance_end':
                self._user_utterance_end_handler(frame)
                        
            elif event_type == 'system_utterance_start':
                self._system_utterance_start_handler(frame)
                
            elif event_type == 'system_utterance_end':
                self._system_utterance_end_handler(frame)
                
            elif event_type == 'system_utterance_canceled':
                self._system_utterance_canceled_handler(frame)
                
            elif event_type == 'dialog_state_change':
                self._dialog_state_change_handler(frame)
                
            elif event_type == 'turn_timeout':
                self._turn_timeout_handler(frame)
                    
            else:
                self._unknown_event_handler(frame)

        elif frame.name == 'end_session':
            event_type = 'end_session'
            self._end_session_handler(frame)
    
        # store the event_type in the dialog state, 
        # so we don't need to reference the frame later
        self.dialog_state.last_event_type = event_type
    

    #===========================================================================
    # Event handlers
    #===========================================================================
    def _begin_session_handler(self, frame):
        self.app_logger.info('begin_session')
        # store session begin time
        self.dialog_state.session_start_time = time.time()
                
                
    def _user_utterance_end_handler(self, frame):
        self.app_logger.info('user_utterance_end')
        
        # store the latest user action time
        self.dialog_state.last_input_time = time.time()
        
        # append the parsed results to the history of input hypotheses in the dialog state.
        self.dialog_state.history_input_hyps.append(self.parse_input_hyps(self.dialog_state, self.dialog_actuator, frame))
        
        # append the parsed results to the list of input hypotheses for the current turn.
        self.dialog_state.input_hyps_current_turn.append(self.dialog_state.history_input_hyps[-1])
        
        # update belief states
        self.dialog_state.update_belief()
                
                
    def _system_utterance_start_handler(self, frame):
        self.app_logger.info('system_utterance_start(%s) %s'%(frame[':properties'][':utt_count'],\
                                                             frame[':properties'][':tagged_prompt']))
        self.dialog_state.last_output_start_time = time.time()
        self.dialog_state.last_output_status = 'start'
        self.dialog_state.bargein = False
        
        
    def _system_utterance_end_handler(self, frame):
        self.app_logger.info('system_utterance_end(%s)'%frame[':properties'][':utt_count'])
        self.dialog_state.last_output_end_time = time.time()
        self.dialog_state.last_output_status = 'end'
        # check if the user barged in
        if frame[':properties'][':bargein_pos'] != '-1':
            self.dialog_state.bargein = True
            self.app_logger.info('Barge in detected at %s'%frame[':properties'][':tagged_prompt'])
        if frame[':properties'][':utt_count'] in self.dialog_state.notify_prompts:
            self.dialog_state.notify_prompts.remove(frame[':properties'][':utt_count'])


    def _system_utterance_canceled_handler(self, frame):
        self.app_logger.info('system_utterance_canceled(%s)'%frame[':properties'][':utt_count'])
        self.dialog_state.last_output_end_time = time.time()
        self.dialog_state.last_output_status = 'canceled'
        # check if the user barged in
        if ':bargein_pos' in frame[':properties'] and frame[':properties'][':bargein_pos'] != '-1':
            self.dialog_state.bargein = True
            self.app_logger.info('Barge in detected at %s'%frame[':properties'][':tagged_prompt'])


    def _dialog_state_change_handler(self, frame):
        self.app_logger.info('dialog_state_change')
        # broadcast dialog state
        self.dialog_actuator.broadcast_dialog_state(self.dialog_state)


    def _turn_timeout_handler(self, frame):
        self.app_logger.info('turn_timeout')
#        self.id_suffix += 1
#        self.asrResult = ASRResult.FromHelios([UserAction('non-understanding')],[1.0])
#        self.app_logger.info('ASRResult: %s'%str(self.asrResult))


    def _unknown_event_handler(self, frame):
        self.app_logger.info('Unknow event')


    def _end_session_handler(self, frame):
        self.app_logger.info('end_session')
        # respond to end session message (should we?)
        self.dialog_actuator.reply_end_session()
        self.continue_dialog = False



         

