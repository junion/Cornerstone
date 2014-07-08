'''
Created on Jul 7, 2014

@author: Sungjin Lee
'''

def compose_msg(state, tts_config):
    if not tts_config:
        return ''
    tts_config_str = []
    if tts_config:
        for key in tts_config.keys():
            tts_config_str.append('   :'+key+' "'+
                                  tts_config[key]+'"\n')
    msg = ''.join(tts_config_str)
    return msg
