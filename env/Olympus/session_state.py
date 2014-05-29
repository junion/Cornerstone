
import logging
#import domain.domain_tasks as domain_tasks


MODULE_ID = 'SessionState'


class SessionState(object):
    def __init__(self, session_id):

        self.app_logger = logging.getLogger(MODULE_ID)
    
        self.session_id = session_id
        self.session_start_time = None
        
        #=======================================================================
        # Variables for composing galaxy messages 
        #=======================================================================
        # dialog_state_index is update when a dialog state update request 
        # is received from the interaction manager 
        self.dialog_state_index = 0
        self.id_suffix = 0
        self.utt_count = 0
        self.turn_number = 0
        self.notify_prompts = []

        self.reset()
        
        #=======================================================================
        # Let's Go specific
        #=======================================================================
#        self.uncovered_route = {}
#        self.discontinued_route = {}
#        self.uncovered_from = {}
#        self.uncovered_to = {}

        
    def reset(self):
        self.last_event_type = None
        self.last_input_time = None
        self.last_output_end_time = None
        self.last_output_status = None
        self.bargein = False
        
        self.history_system_acts = []
        self.history_input_hyps = []
        
        self.system_acts_current_turn = []
        self.input_hyps_current_turn=  []
        
#        self.belief_state = BeliefState()
#        self.init_plan_execution_state()
        
        
#    def init_plan_execution_state(self):
#        self.method_executed = {}
#        for task in domain_tasks.task_to_methods.keys():
#            for method in domain_tasks.task_to_methods[task]:
#                app_logger.info(method.name)
#                assert method.name not in self.method_executed
#                self.method_executed[method.name] = False
#        
#    
#    def set_plan_execution_state(self, name, value):
#        self.method_executed[name] = value
#        
#
#    def get_plan_execution_state(self, name):
#        return self.method_executed[name]
        
        
    
