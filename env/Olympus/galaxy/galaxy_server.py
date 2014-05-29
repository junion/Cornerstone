import os
import sys
import traceback
import logging
import Queue

import Galaxy, GalaxyIO

from config.global_config import init_config, get_config
from env.Olympus.agent_thread import AgentThread


#===============================================================================
# Init and load configs
#===============================================================================
init_config()
config = get_config()
config.read(['config/system.conf'])

#===============================================================================
# Global variables
#===============================================================================
app_logger = None
agent_thread = None
in_session = False
last_env = None
metaInfo = []
timeout_period = 8
in_queue = None
out_queue = None
result_queue = None


# request a response of an other agent
def call_galaxy_module_function(str_frame):
    global last_env

    frame_to_Hub = Galaxy.Frame(str=str_frame)
    try:
        frame_from_Hub = last_env.DispatchFrame(frame_to_Hub)
        app_logger.info('frame_from_Hub:\n %s'%frame_from_Hub.PPrint()) 
        return frame_from_Hub
    except GalaxyIO.DispatchError:
        app_logger.info('dispatch error')
        return None


# request an action of an other agent    
def send_action_through_hub(str_frame):
    global last_env

    frame_to_Hub = Galaxy.Frame(str=str_frame)
    last_env.WriteFrame(frame_to_Hub)


# let the dialog thread work with the given event
def do_dialog_flow(frame=None):
    global in_queue
    global out_queue
    global result_queue

    app_logger.info('Beginning of dialog flow')

    try:
        # place input frame for the dialog thread to process it
        in_queue.put(frame)
        app_logger.info('Sent a frame to dialog thread')
    
        # keep getting output messages from the dialog thread until all consumed 
        while True:
            app_logger.info('Waiting for a message in')
            
            message = out_queue.get()
            app_logger.info('Got a message')
            out_queue.task_done()

            # request for a galaxy call to other agents
            if message['type'] == 'GALAXYCALL':
                app_logger.info('GALAXYCALL')
                app_logger.info('%s'%message['content'])
                result = call_galaxy_module_function(message['content'])
                app_logger.info('GALAXYCALL completed')
                # put the result into the result queue
                result_queue.put(result)
                app_logger.info('Returned the result')
            # request for a galaxy action call to other agents
            elif message['type'] == 'GALAXYACTIONCALL':
                app_logger.info('GALAXYACTIONCALL')
                app_logger.info('%s'%message['content'])
                send_action_through_hub(message['content'])
                app_logger.info('GALAXYACTIONCALL completed')
                # action doesn't return results
                result_queue.put(None)
                app_logger.info('Returned the result')
            elif message['type'] == 'WAITINPUT':
                app_logger.info('Wait for input from outside')
                return False
            elif message['type'] == 'WAITINTERACTIONEVENT':
                app_logger.info('Wait for interaction events from other agents')
                return False
            elif message['type'] == 'DIALOGFINISHED':
                app_logger.info('Dialog finished')
                return True
            elif message['type'] == 'ENDSESSION':
                app_logger.info('End session')
                return True
            else:
                app_logger.info('Unknown message from dialog thread %s'%str(message))

    except Exception:
        app_logger.error(traceback.format_exc())

    app_logger.info('End of dialog flow')


#===============================================================================
# Event handlers
#===============================================================================
def reinitialize(env, frame):
    global last_env

    last_env = env

    return frame


def begin_session(env, frame):
    global app_logger
    global agent_thread
    global in_session
    global last_env
    global in_queue
    global out_queue
    global result_queue

    try:    
        # if there's an ongoing session, terminate it to start a new one 
        if in_session:
            end_session(env, frame)
        in_session = True
    
        # store the latest environment
        last_env = env

        # define the log file for the session
        try:
            log_prefix = frame[':hub_log_prefix'] + '-dialog.log'
            log_dir = frame[':hub_logdir']
            print log_dir
        except KeyError:
            print "Can't find log information"
        else:
            # open a new logger for the session
            app_logger = logging.getLogger()
            app_logger.setLevel(logging.DEBUG)
            file_handler = logging.FileHandler(os.path.join(log_dir, log_prefix))
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter("%(asctime)s %(lineno)4d %(module)s:%(funcName)s: %(message)s")
            file_handler.setFormatter(formatter)
            app_logger.addHandler(file_handler)

        # log session information    
        app_logger.info('begin_session called.')
        app_logger.info('frame:\n %s'%frame.PPrint())
        try:
            app_logger.info('Init timestamp: %s.'%str(frame[':session_start_timestamp']))
        except KeyError:
            app_logger.info("Can't find :session_start_timestamp")
        try:
            app_logger.info('Init session ID: %s.'%str(frame[':sess_id']))
        except KeyError:
            app_logger.info("Can't find :sess_id")

        # create queues for communication between the galaxy server and the dialog thread     
        in_queue = Queue.Queue()
        out_queue = Queue.Queue()
        result_queue = Queue.Queue()
       
        # create and start the dialog thread
        agent_thread = AgentThread(str(frame[':sess_id']), log_dir, in_queue, out_queue, result_queue)
        app_logger.info("Dialog thread created")
        agent_thread.setDaemon(True)
        app_logger.info("Daemonized")
        agent_thread.start()
        app_logger.info("Started")
        
        # let the dialog thread work with the given frame
        do_dialog_flow(frame)
        
        app_logger.info('DM processing finished.')

    except Exception:
        app_logger.error(traceback.format_exc())
#        EmailLogging.send_mail('Exception!',traceback.format_exc())
       
    return frame


def end_session(env,frame):
    global agent_thread
    global in_session
    global last_env
    global in_queue
    global out_queue
    global result_queue

    try:
        # if not in a session, just return
        if not in_session:
            return frame
        
        # store the latest environment
        last_env = env
        
        # update the returning frame with terminate indication
        frame[':event_type'] = 'end_session'
        frame[':event_complete'] = 1
        properties = Galaxy.Frame(type=Galaxy.GAL_CLAUSE, name="properties")
        properties[':terminate_session'] = 'true'
        frame[':properties'] = properties
        app_logger.info('end_session called; sending terminate to Core')
        
        
        # let the dialog thread work with the given frame
        do_dialog_flow(frame)
        app_logger.info('DM processing finished.')

        # wait for dialog thread to complete    
        agent_thread.join()
        app_logger.info('Dialog thread terminated.')
    
        # free the dialog thread and queues
        agent_thread = None
        in_queue = None
        out_queue = None
        result_queue = None
        
        # session ends
        in_session = False

    except Exception:
        app_logger.error(traceback.format_exc())
#        EmailLogging.send_mail('Exception!',traceback.format_exc())

    # close the logger for the session
    app_logger.handlers[0].stream.close()
    app_logger.removeHandler(app_logger.handlers[0])

    return frame


def handle_event(env, frame):
    global in_session
    global last_env

    try:
        app_logger.info('handle_event')
        app_logger.info('frame:\n%s'%frame.PPrint())
       
        # if not in a session, just return
        if not in_session:
            return frame
        
        # store the latest environment
        last_env = env
        
        # let the dialog thread work with the given frame
        finished = do_dialog_flow(frame)
        
        app_logger.info('DM processing finished.')

        # check if the dialog thread decided to terminate the session 
        if finished:
            message = '''{c main
         :close_session ""}'''
            send_action_through_hub(message)
            app_logger.info('close_session sent')

    except Exception:
        app_logger.error(traceback.format_exc())
#        EmailLogging.send_mail('Exception!',traceback.format_exc())
    
    return frame

    
def service_timeout():
    global in_session
    global metaInfo

    # if not in a session, just return
    if not in_session:
        return
    
    app_logger.info('service_timeout called.')
    metaInfo = []
    metaInfo[':timeout_elapsed'] = True
    
    # let the dialog thread work with the meta information
    do_dialog_flow()
    
    app_logger.info('DM processing finished.')

    
def start_inactivity_timeout(env, frame):
    global in_session
    global last_env
    
    # if not in a session, just return
    if not in_session:
        return frame

    # store the latest environment
    last_env = env

    app_logger.info('start_inactivity_timeout called; installing time trigger (%d secs)'%timeout_period)
    
    return frame


def cancel_inactivity_timeout(env, frame):
    global in_session
    global last_env

    # if not in a session, just return
    if not in_session:
        return frame
    
    # store the latest environment
    last_env = env

    app_logger.info('cancel_inactivity_timeout called; removing the trigger')
    
    return frame


#===============================================================================
# Class CornerstoneServer which inherits GalaxyIO.Server
#===============================================================================
class CornerstoneServer(GalaxyIO.Server):
    def __init__(self, in_args, server_name = "<unknown>",
                 default_port = 0,
                 verbosity = -1,
                 require_port = 0,
                 maxconns = 1,
                 validate = 0,
                 server_listen_status = GalaxyIO.GAL_CONNECTION_LISTENER,
                 client_pair_string = None,
                 session_id = None,
                 server_locations_file = None,
                 slf_name = None,
                 env_class = GalaxyIO.CallEnvironment):
        GalaxyIO.Server.__init__(self, in_args, server_name,
                         default_port, verbosity,
                         require_port, maxconns,
                         validate, server_listen_status,
                         client_pair_string, session_id,
                         server_locations_file,
                         slf_name,
                         env_class)

#===============================================================================
# Create a galaxy server for dialog manager
#===============================================================================
gal_serv = CornerstoneServer(sys.argv, "DialogManager", default_port=17000, verbosity=3)

#===============================================================================
# Add dispatch functions
#===============================================================================
gal_serv.AddDispatchFunction("begin_session",begin_session,
                    [[[":int", Galaxy.GAL_INT, Galaxy.GAL_KEY_ALWAYS]],
                    Galaxy.GAL_OTHER_KEYS_NEVER,
                    Galaxy.GAL_REPLY_NONE, [],
                    Galaxy.GAL_OTHER_KEYS_NEVER])
gal_serv.AddDispatchFunction("handle_event",handle_event,
                    [[[":int", Galaxy.GAL_INT, Galaxy.GAL_KEY_ALWAYS]],
                    Galaxy.GAL_OTHER_KEYS_NEVER,
                    Galaxy.GAL_REPLY_NONE, [],
                    Galaxy.GAL_OTHER_KEYS_NEVER])
gal_serv.AddDispatchFunction("start_inactivity_timeout",start_inactivity_timeout,
                    [[[":int", Galaxy.GAL_INT, Galaxy.GAL_KEY_ALWAYS]],
                    Galaxy.GAL_OTHER_KEYS_NEVER,
                    Galaxy.GAL_REPLY_NONE, [],
                    Galaxy.GAL_OTHER_KEYS_NEVER])
gal_serv.AddDispatchFunction("cancel_inactivity_timeout",cancel_inactivity_timeout,
                    [[[":int", Galaxy.GAL_INT, Galaxy.GAL_KEY_ALWAYS]],
                    Galaxy.GAL_OTHER_KEYS_NEVER,
                    Galaxy.GAL_REPLY_NONE, [],
                    Galaxy.GAL_OTHER_KEYS_NEVER])
gal_serv.AddDispatchFunction("end_session",end_session,
                    [[[":int", Galaxy.GAL_INT, Galaxy.GAL_KEY_ALWAYS]],
                    Galaxy.GAL_OTHER_KEYS_NEVER,
                    Galaxy.GAL_REPLY_NONE, [],
                    Galaxy.GAL_OTHER_KEYS_NEVER])
gal_serv.AddDispatchFunction("reinitialize",reinitialize,
                      [[], Galaxy.GAL_OTHER_KEYS_NEVER,
                       Galaxy.GAL_REPLY_NONE, [],
                       Galaxy.GAL_OTHER_KEYS_NEVER])

#===============================================================================
# Finally, run the server
#===============================================================================
gal_serv.RunServer()
