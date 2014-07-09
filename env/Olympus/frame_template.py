'''
Created on Jul 8, 2014

@author: Sungjin Lee
'''

dialog_state_template = '''"turn_number = ${turn_number}
notify_prompts = ${notify_prompts}
dialog_state = /LetsGoPublic
nonu_threshold = 0.0000
stack = {
/LetsGoPublic
}
agenda = {
0:X[0_covered_route]S,X[0_discontinued_route]S,X[0_uncovered_route]S,X[1_singleplace.stop_name.covered_place.ambiguous_covered_place]S,X[1_singleplace.stop_name.covered_place.ambiguous_covered_place]S,X[1_singleplace.stop_name.covered_place.covered_neighborhood]S,X[1_singleplace.stop_name.covered_place.covered_neighborhood]S,X[1_singleplace.stop_name.covered_place.monument]S,X[1_singleplace.stop_name.covered_place.monument]S,X[1_singleplace.stop_name.covered_place.registered_stop]S,X[1_singleplace.stop_name.covered_place.registered_stop]S,X[1_singleplace.stop_name.uncovered_place]S,X[2_departureplace.stop_name.covered_place.ambiguous_covered_place]S,X[2_departureplace.stop_name.covered_place.covered_neighborhood]S,X[2_departureplace.stop_name.covered_place.monument]S,X[2_departureplace.stop_name.covered_place.registered_stop]S,X[2_departureplace.stop_name.uncovered_place]S,X[3_arrivalplace.stop_name.covered_place.ambiguous_covered_place]S,X[3_arrivalplace.stop_name.covered_place.covered_neighborhood]S,X[3_arrivalplace.stop_name.covered_place.monument]S,X[3_arrivalplace.stop_name.covered_place.registered_stop]S,X[3_arrivalplace.stop_name.uncovered_place]S,X[4_busafterthatrequest]S,X[4_busafterthatrequest]V,X[4_busbeforethatrequest]V,X[ambiguous_covered_place]S,X[anystop]V,X[covered_neighborhood]S,X[date_time]S,X[disambiguatearrival]V,X[disambiguatedeparture]V,X[dontknow]V,X[dtmf_one]V,X[dtmf_one]V,X[dtmf_three]V,X[dtmf_three]V,O[dtmf_zero]V,O[establishcontext]V,O[finalquit]V,O[help.general_help]V,O[help.give_me_tips]V,O[help.what_can_i_say]V,O[help.where_are_we]V,X[no]V,O[quit]V,O[repeat]V,X[repeat]V,O[session:session_timeout]V,O[session:terminatesession]V,O[startover]V,X[startover]V,X[stop_name.monument]S,X[stop_name.registered_stop]S,O[turn_timeout:timeout]V,O[yes]V,X[yes]V
}
input_line_config = {
${input_line_config}
}"'''

dialog_state_frame_template = '''{c main
     :dialog_state ${dialog_state}}'''

system_utterance_frame_template = '''
{c main
    :action_level "high"
    :action_type "system_utterance"
    :properties {c properties
                   :dialog_act "${dialog_act}"
                   :dialog_state ${dialog_state}
       :dialog_state_index "${dialog_state_index}"
       :final_floor_status "${final_floor_status}"
       :id "DialogManager-${sess_id}:${id_suffix}"
       :inframe "start
${nlg_config}
end
"
${tts_config}   :utt_count "${utt_count}" }}'''

