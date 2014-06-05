
from pprint import pprint
import rule_engine_api as reapi

def test1():
    kernel = reapi.create_kernel()
    agent = reapi.create_agent(kernel, "agent")
    reapi.register_print_callback(kernel, agent,
                                  reapi.callback_print_message, None)
    input_link_wme = agent.GetInputLink()
    
    # load domain rules
    domain_rule_source = '../../../model/rules/Letsgo.soar'
    print agent.LoadProductions(domain_rule_source)
    print agent.ExecuteCommandLine('print')
    agent.ExecuteCommandLine('set-stop-phase -Ao')
    # begin-session   
    print agent.RunSelf(3)
    print '-----'
    cmds = {}
    for i in range(agent.GetNumberCommands()):
        cmd = agent.GetCommand(i)
        cmd_name = cmd.GetCommandName()
        params = {}
        for j in range(cmd.GetNumberChildren()):
            param = cmd.GetChild(j)
            param_name = param.GetAttribute()
            params[param_name] = cmd.GetParameterValue(param_name)
        cmds[cmd_name] = params
        cmd.AddStatusComplete()
    agent.ClearOutputLinkChanges()
    pprint(cmds)
    print '#####'    
    events = agent.CreateIdWME(input_link_wme, 'events')
    begin = agent.CreateStringWME(events, 'begin-session', 'nil')
    print agent.RunSelf(1)
    cmds = {}
    for i in range(agent.GetNumberCommands()):
        cmd = agent.GetCommand(i)
        cmd_name = cmd.GetCommandName()
        params = {}
        for j in range(cmd.GetNumberChildren()):
            param = cmd.GetChild(j)
            param_name = param.GetAttribute()
            print param_name
            print param.GetValueAsString()
            params[param_name] = param.GetValueAsString() #cmd.GetParameterValue(param_name)
        cmds[cmd_name] = params
        cmd.AddStatusComplete()
    agent.ClearOutputLinkChanges()
    pprint(cmds)


    
    kernel.DestroyAgent(agent)
    kernel.Shutdown()
    del kernel

test1()
