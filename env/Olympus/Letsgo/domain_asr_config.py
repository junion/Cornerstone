'''
Created on Jul 7, 2014

@author: Sungjin Lee
'''

def compose_msg(state):
    asr_config_str = []
    for key in state.asr_config.keys():
        asr_config_str.append(key+' = '+
                              state.asr_config[key])
    msg = ', '.join(asr_config_str)
    return msg
