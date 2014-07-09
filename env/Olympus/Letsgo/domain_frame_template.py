
#===============================================================================
# The templates should be replaced by frame composition
# using galaxy APIs 
#===============================================================================

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
