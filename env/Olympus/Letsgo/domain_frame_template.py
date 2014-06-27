
#===============================================================================
# The templates should be replaced by frame composition
# using galaxy APIs 
#===============================================================================

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
{
act	${dialog_act}
object	${object}
_repeat_counter	0
${nlg_args}system_version	1
}
end
"
${tts_config}   :utt_count "${utt_count}" }}'''

place_query_template = '{c gal_be.launch_query\n\
:inframe "{\n\
query {\n\
type\t100\n\
place\t{\n\
name\t${name}\n\
type\t${type}\n\
}\n\
}\n\
}\n\
"\n\
}'

full_time_template = 'travel_time\t{\n\
date\t{\n\
month\t${month}\n\
day\t${day}\n\
year\t${year}\n\
weekday\t${weekday}\n\
}\n\
\n\
period_spec\t${period_spec}\n\
time\t{\n\
value\t${value}\n\
now\t${now}\n\
type\t${time_type}\n\
}\n\
\n\
}\n\
'

brief_time_template = 'travel_time\t{\n\
period_spec\t${period_spec}\n\
time\t{\n\
now\t${now}\n\
type\t${time_type}\n\
}\n\
\n\
}\n\
'

minimal_time_template = 'travel_time\t{\n\
time\t{\n\
value\t${value}\n\
type\t${time_type}\n\
}\n\
\n\
}\n\
'

#schedule_query_template = '{c gal_be.launch_query\n\
#:inframe "{\n\
#query {\n\
#type\t${type}\n\
#${time_spec}\n\
#departure_place\t{\n\
#name\t${departure_place_name}\n\
#type\t${departure_place_type}\n\
#}\n\
#\n\
#arrival_place\t{\n\
#name\t${arrival_place_name}\n\
#type\t${arrival_place_type}\n\
#}\n\
#\n\
#${route_number}\
#}\n\
#\n\
#${departure_stops}\n\
#\n\
#${arrival_stops}\n\
#\n\
#result\t{\n\
#${result}\n\
#}\n\
#\n\
#}\n\
#"\n\
#}'

schedule_query_template = '{c gal_be.launch_query\n\
:inframe "{\
${constraints}\
\n\
${departure_stops}\n\
\n\
${arrival_stops}\n\
\n\
result\t{\n\
${result}\n\
}\n\
\n\
}\n\
"\n\
}'


schedule_constraints_template = '\nquery\t{\n\
type\t${type}\n\
${time_spec}\n\
\n\
departure_place\t{\n\
name\t${departure_place_name}\n\
type\t${departure_place_type}\n\
}\n\
\n\
arrival_place\t{\n\
name\t${arrival_place_name}\n\
type\t${arrival_place_type}\n\
}\n\
\n\
${route_number}\
}\n'


parse_datetime_template = '{c datetime.ParseDateTime\n\
:Date_Time_Parse "{c parse :slots ${gal_slotsframe}}"}'
