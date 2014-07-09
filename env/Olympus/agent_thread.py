'''
Created on Jul 4, 2014

@author: Sungjin Lee
'''

import threading
import traceback
import time
import logging
import importlib
from copy import deepcopy

from config.global_config import get_config

from session_state import SessionState
from actuator import Actuator
from core.agent import CornerstoneAgent
from core.datatypes.event_list import EventList
from core.datatypes.session_event import SessionEvent
from core.datatypes.state_event import StateEvent


MODULE_ID = 'AgentThread'


#=============================================================================
# Agent thread which inherits thread class
#=============================================================================
class AgentThread(threading.Thread):
    def __init__(self, session_id, log_dir, in_queue, out_queue, result_queue):
        threading.Thread.__init__(self)
        # load configs
        self.config = get_config()
        # logging
        self.app_logger = logging.getLogger(MODULE_ID)
        # session info
        self.session_id = session_id
        self.log_dir = log_dir
        # queues for communication with the galaxy server 
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.result_queue = result_queue
        # create an actuator
        self.actuator = Actuator(self.out_queue, self.result_queue)
        # timing
        self.event_wait_timeout = self.config.getint(MODULE_ID, 
                                                     'eventWaitTimeout')
        # domain
        self.domain = self.config.get('Common', 'domain')
        # create a parser for core input
        self.user_input_parser = importlib.import_module(
                                    self.domain + '.domain_input_parser')
#         self.user_input_parser = __import__(
#                                     self.domain + '.domain_input_parser')
        self.app_logger.info('Agent thread %s created'%self.getName())

    #=======================================================================
    # main loop
    #=======================================================================
    def run(self):
        while True:
            try:
                try:
                    self.app_logger.info('Wait event')
                    # get an event from the galaxy server
                    frame = deepcopy(self.in_queue.get(
                                            timeout=self.event_wait_timeout))
                    self.in_queue.task_done()
                except:
                    self.app_logger.info('Warning: no event for a long time')
                    continue
                # a frame can be None if it did not came from begin_session, 
                # end_session, handle_event
                # currently, we have nothing to do for the case
                if frame == None:
                    self.app_logger.info('Warning: null frame')
                    continue
                # handle Olympus events
                in_events = EventList()
#                 self.app_logger.info('New event: %s' % str(in_events)) 
                self._update_state_for_event(frame, in_events)
                if self._take_turn():
                    while True:
                        # call the agent with the input and get output events
                        out_events = self.agent.run(in_events)
        #                 self.app_logger.info('Out event: %s' % str(out_events))
                        # convert the core output to a galaxy frame
                        in_events = self.actuator.execute(self.session_state, out_events)
                        if not in_events:
                            break
                self.app_logger.info('Execution done')
                self.actuator.send_wait_event_message()
            except Exception:
                self.app_logger.info('Try to recover from crash:')
                self.app_logger.error(traceback.format_exc())
#                email_log.send_mail('Exception!',traceback.format_exc())
                self.dialog_controller.restart_interaction()

    def _take_turn(self):
        if self.session_state.last_event_type == None:
            return True
        if self.session_state.last_event_type == 'begin_session':
            return True
        if self.session_state.last_event_type == 'user_utterance_end':
            return True
        if self.session_state.last_event_type == 'turn_timeout':
            return True
        if self.session_state.last_event_type == 'system_utterance_end':
            if not self.session_state.turn_yield:
                return True
        return False

    # update dialog state by incorporating the input frame        
    def _update_state_for_event(self, frame, events):
        # call event handlers
        if frame.name == 'begin_session':
            event_type = 'begin_session'
            self._begin_session_handler(frame, events)
        elif frame.name == 'DialogManager.handle_event':
            event_type = frame[':event_type']
            self.app_logger.info('\nevent_type: %s' % event_type)
            if event_type == 'user_utterance_end':
                self._user_utterance_end_handler(frame, events)
            elif event_type == 'system_utterance_start':
                self._system_utterance_start_handler(frame, events)
            elif event_type == 'system_utterance_end':
                self._system_utterance_end_handler(frame, events)
            elif event_type == 'system_utterance_canceled':
                self._system_utterance_canceled_handler(frame, events)
            elif event_type == 'session_state_change':
                self._session_state_change_handler(frame, events)
            elif event_type == 'turn_timeout':
                self._turn_timeout_handler(frame, events)
            else:
                self._unknown_event_handler(frame, events)
        elif frame.name == 'end_session':
            event_type = 'end_session'
            self._end_session_handler(frame, events)
        # store the event_type in the dialog state, 
        # so we don't need to reference the frame later
        self.session_state.last_event_type = event_type

    #=========================================================================
    # Event handlers
    #=========================================================================
    def _begin_session_handler(self, frame, events):
        '''Create new variables for the new session. Add a begin event.
        
        Key variables:
        self.session_state -- maintain session state
        self.re_agent -- the core re_agent
        events -- a collection of events from the frame 
        '''
        self.app_logger.info('\nbegin_session')
        # create a session state
        self.session_state = SessionState(self.session_id)
        # create a core re_agent
        self.agent = CornerstoneAgent()
        # store session begin time
        self.session_state.session_start_time = time.time()
        # add an event
        events.add_event('session', SessionEvent('begin'))
                
    def _user_utterance_end_handler(self, frame, events):
        '''Parse the user utterance. Add a speech event.'''
        self.app_logger.info('\nuser_utterance_end')
        # store the latest user action time
        self.session_state.last_input_time = time.time()
        # convert the galaxy frame to core input
        in_speech_event = self.user_input_parser.parse(self.session_state,
                                                    self.actuator, frame)
        # append the parsed results to the history of input hypotheses 
        # in the dialog state.
        self.session_state.history_input_hyps.append(in_speech_event)
        # append the parsed results to the list of input hypotheses 
        # for the current turn.
        self.session_state.input_hyps_current_turn.append(
            self.session_state.history_input_hyps[-1])
        # add an event
        events.add_event('speech', in_speech_event)
        
    def _system_utterance_start_handler(self, frame, events):
        self.app_logger.info('\nsystem_utterance_start(%s) %s' % 
                             (frame[':properties'][':utt_count'],
                              frame[':properties'][':tagged_prompt']))
        self.session_state.last_output_start_time = time.time()
        self.session_state.last_output_status = 'start'
        self.session_state.bargein = False
        
    def _system_utterance_end_handler(self, frame, events):
        self.app_logger.info('system_utterance_end(%s)' % 
                             frame[':properties'][':utt_count'])
        self.session_state.last_output_end_time = time.time()
        self.session_state.last_output_status = 'end'
        # check if the user barged in
        if frame[':properties'][':bargein_pos'] != '-1':
            self.session_state.bargein = True
            self.app_logger.info('Barge in detected at %s' % 
                                 frame[':properties'][':tagged_prompt'])
        if (frame[':properties'][':utt_count'] in 
                self.session_state.notify_prompts):
            self.session_state.notify_prompts.remove(
                            frame[':properties'][':utt_count'])
        # add an event
        events.add_event('state', StateEvent('speech-completed', {}))

    def _system_utterance_canceled_handler(self, frame, events):
        self.app_logger.info('\nsystem_utterance_canceled(%s)' % 
                             frame[':properties'][':utt_count'])
        self.session_state.last_output_end_time = time.time()
        self.session_state.last_output_status = 'canceled'
        # check if the user barged in
        if (':bargein_pos' in frame[':properties'] and 
                frame[':properties'][':bargein_pos'] != '-1'):
            self.session_state.bargein = True
            self.app_logger.info('Barge in detected at %s' % 
                                 frame[':properties'][':tagged_prompt'])
        # add an event
        events.add_event('speech', StateEvent('speech-completed', {}))

    def _session_state_change_handler(self, frame, events):
        self.app_logger.info('\nbroadcast_dialog_state')
        # broadcast dialog state
        self.actuator.broadcast_dialog_state(self.session_state)

    def _turn_timeout_handler(self, frame, events):
        self.app_logger.info('\nturn_timeout')

    def _unknown_event_handler(self, frame, events):
        self.app_logger.info('\nUnknow event')

    def _end_session_handler(self, frame, events):
        self.app_logger.info('\nend_session')
        # respond to end session message (should we?)
        self.actuator.reply_end_session()
        self.continue_dialog = False


