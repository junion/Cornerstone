
from pprint import pprint
import rule_engine_api as reapi

def get_cmds(agent):
    cmds = {}
    output_link_wme = agent.GetOutputLink()
    if output_link_wme:
        for i in range(output_link_wme.GetNumberChildren()):
            cmd = output_link_wme.GetChild(i).ConvertToIdentifier()
            cmd_name = cmd.GetAttribute()
#            print cmd_name
            params = {}
            for j in range(cmd.GetNumberChildren()):
                param = cmd.GetChild(j)
                param_name = param.GetAttribute()
#                print param_name
#                print param.GetValueAsString()
                params[param_name] = param.GetValueAsString() 
            if 'status' not in params:
                cmds[cmd_name] = params
                agent.CreateStringWME(cmd, 'status', 'complete')
                agent.Commit()
    pprint(cmds)
    return cmds
    

def get_output(agent):
    while True:
#        print agent.ExecuteCommandLine('print -d 4 i1')
        print agent.RunSelf(1)
        print agent.ExecuteCommandLine('print -d 6 s9')
        cmds = get_cmds(agent)
        if cmds:
            break
    return cmds


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
    while True:   
        cmds = get_output(agent)
        if 'wait' in cmds:
            events = agent.CreateIdWME(input_link_wme, 'events')
            agent.CreateStringWME(events, 'begin-session', 'nil')
            agent.Commit()
            break
 
    cmds = get_output(agent)
    agent.DestroyWME(events)
    agent.Commit()

    while True:
        cmds = get_output(agent)
        if 'wait' in cmds:
            print agent.ExecuteCommandLine('print -d 4 s1')
            input_link_wme = agent.GetInputLink()
            events = agent.CreateIdWME(input_link_wme, 'events')
            cu = agent.CreateIdWME(events, 'concept-update')
            agent.CreateStringWME(cu, 'name', 'from')
            hyp1 = agent.CreateIdWME(cu, 'top-hyp')
            agent.CreateStringWME(hyp1, 'value', 'cmu')
            agent.CreateFloatWME(hyp1, 'score', 0.7)
            hyp2 = agent.CreateIdWME(cu, 'second-hyp')
            agent.CreateStringWME(hyp2, 'value', 'none')
            agent.CreateFloatWME(hyp2, 'score', 0.0)
            hyp3 = agent.CreateIdWME(cu, 'rest-hyp')
            agent.CreateStringWME(hyp3, 'value', 'none')
            agent.CreateFloatWME(hyp3, 'score', 0.0)
            agent.Commit()
            break
    cmds = get_output(agent)
    agent.DestroyWME(events)
    agent.Commit()
    

    print agent.ExecuteCommandLine('print -d 4 i2')
    print agent.ExecuteCommandLine('print -d 4 s1')

    cmds = get_output(agent)

    print agent.ExecuteCommandLine('print -d 4 s1')
    
    kernel.DestroyAgent(agent)
    kernel.Shutdown()
    del kernel

test1()
