'''

'''

import threading
import traceback
from copy import deepcopy
import Queue
import logging

from config.global_config import get_config

from cornerstone.agent import CornerstoneAgent


MODULE_ID = 'AgentThread'


#===============================================================================
# Agent thread which inherits thread class
#===============================================================================
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

        # timing
        self.event_wait_timeout = self.config.getint(MODULE_ID, 'eventWaitTimeout')

        # domain
        self.domain = self.config.get(MODULE_ID, 'domainSemantics')
        
        # create a cornerstone agent
        self.agent = CornerstoneAgent()
        
        self.app_logger.info('Agent thread %s created'%self.getName())

        
    #=======================================================================
    # main loop
    #=======================================================================
    def run(self):
        while self.dialog_controller.continue_dialog:
            try:
                try:
                    self.app_logger.info('Wait event')
                    # get an event from the galaxy server
                    frame = deepcopy(self.in_queue.get(timeout=self.event_wait_timeout))
                    self.in_queue.task_done()
                except:
                    self.app_logger.info('Warning: no event for a long time')
                    continue
                
                # a frame can be None if it did not came from begin_session, end_session, handle_event
                # currently, we have nothing to do for the case
                if frame == None:
                    self.app_logger.info('Warning: null frame')
                    continue

                # convert the galaxy frame to cornerstone input
                
                # call the agent with the input and get output
                
                # convert the cornerstone output to a galaxy frame

            except Exception:
                self.app_logger.info('Try to recover from crash:')
                self.app_logger.error(traceback.format_exc())
#                email_log.send_mail('Exception!',traceback.format_exc())
                self.dialog_controller.restart_interaction()
                
        
