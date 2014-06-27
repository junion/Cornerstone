
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
    

def get_output(agent, matches=False):
    while True:
        if matches:
            print 'before input phase------------------'
            print agent.ExecuteCommandLine('print -d 4 i2')
            agent.ExecuteCommandLine('run -p 1')
            print 'before proposal phase------------------'
            print agent.ExecuteCommandLine('print -d 4 i2')
            agent.ExecuteCommandLine('run -p 1')
            print 'before decision phase------------------'
            print agent.ExecuteCommandLine('matches --assertions --wmes')
            if isinstance(matches, basestring):
                print 'matches production %s:' % matches
                print agent.ExecuteCommandLine('matches %s' % matches)
            print agent.ExecuteCommandLine('predict')
            print agent.ExecuteCommandLine('preferences S1 operator --names')
            agent.ExecuteCommandLine('run -p 1')
            print 'before apply phase------------------'
            print agent.ExecuteCommandLine('print -d 4 s1')
            agent.ExecuteCommandLine('run -p 1')
            print 'before output phase------------------'
            print agent.ExecuteCommandLine('print -d 4 i3')

        agent.RunSelf(1)

        if matches:
            print agent.ExecuteCommandLine('print -d 4 s1')
            print agent.ExecuteCommandLine('print -d 4 i3')

        cmds = get_cmds(agent)
        if cmds:
            break
    return cmds


def test1():
    kernel = reapi.create_kernel()
    agent = reapi.create_agent(kernel, "agent")
#     reapi.register_print_callback(kernel, agent,
#                                   reapi.callback_print_message, None)
    
    # load domain rules
    domain_rule_source = '../../../model/rules/Letsgo.soar'
    reprint = agent.LoadProductions(domain_rule_source)
#     print reprint
#     reprint = agent.ExecuteCommandLine('print')
#     print reprint
    agent.ExecuteCommandLine('set-stop-phase -Ao')

    # get input link
    input_link_wme = agent.GetInputLink()

    # begin-session
    while True:   
        cmds = get_output(agent)
        if 'wait' in cmds:
#             kernel.SetAutoCommit(False)
            events = agent.CreateIdWME(input_link_wme, 'events')
            agent.CreateStringWME(events, 'begin-session', 'nil')
#             agent.Commit()
#             kernel.SetAutoCommit(True)
            break
    print 'should see welcome'
    cmds = get_output(agent)
#     kernel.SetAutoCommit(False)
    agent.DestroyWME(events)
#     agent.Commit()
#     kernel.SetAutoCommit(True)

    print 'should see init-help'
    cmds = get_output(agent)

#     reprint = agent.ExecuteCommandLine('print -d 4 s1')
#     print reprint
    
    while True:
        cmds = get_output(agent)
        if 'wait' in cmds:
#             print agent.ExecuteCommandLine('print -d 4 s1')
            input_link_wme = agent.GetInputLink()
#             kernel.SetAutoCommit(False)
            events = agent.CreateIdWME(input_link_wme, 'events')
            cu = agent.CreateIdWME(events, 'concept-update')
            agent.CreateStringWME(cu, 'name', 'route')
            hyp1 = agent.CreateIdWME(cu, 'top-hyp')
            agent.CreateStringWME(hyp1, 'value', '54c')
            agent.CreateFloatWME(hyp1, 'score', 0.7)
            hyp2 = agent.CreateIdWME(cu, 'second-hyp')
            agent.CreateStringWME(hyp2, 'value', '54')
            agent.CreateFloatWME(hyp2, 'score', 0.09)
            hyp3 = agent.CreateIdWME(cu, 'rest-hyp')
            agent.CreateStringWME(hyp3, 'value', '4c')
            agent.CreateFloatWME(hyp3, 'score', 0.01)

            cu = agent.CreateIdWME(events, 'concept-update')
            agent.CreateStringWME(cu, 'name', 'from')
            hyp1 = agent.CreateIdWME(cu, 'top-hyp')
            agent.CreateStringWME(hyp1, 'value', 'cmu')
            agent.CreateFloatWME(hyp1, 'score', 0.9)
            hyp2 = agent.CreateIdWME(cu, 'second-hyp')
            agent.CreateStringWME(hyp2, 'value', 'c')
            agent.CreateFloatWME(hyp2, 'score', 0.09)
            hyp3 = agent.CreateIdWME(cu, 'rest-hyp')
            agent.CreateStringWME(hyp3, 'value', 'm')
            agent.CreateFloatWME(hyp3, 'score', 0.01)

#             agent.Commit()
#             kernel.SetAutoCommit(True)
            break

#     reprint = agent.ExecuteCommandLine('print -d 4 s1')
#     print reprint
#     agent.ExecuteCommandLine('pwatch -e letsgo*propose*concept-update')
#     agent.ExecuteCommandLine('pwatch -e letsgo*apply*concept-update')
    
    print 'should see confirm from'
    cmds = get_output(agent)
#    cmds = get_output(agent, matches='letsgo*propose*concept-update')
#     reprint = agent.ExecuteCommandLine('print -d 6 s1')
#     print reprint
    agent.DestroyWME(events)
    agent.Commit()
    

#     print agent.ExecuteCommandLine('print -d 4 i2')
#     print agent.ExecuteCommandLine('print -d 4 s1')

    cmds = get_output(agent)
#    cmds = get_output(agent, matches='letsgo*propose*concept-update')
    reprint = agent.ExecuteCommandLine('print -d 6 s1')
    print reprint

#     print agent.ExecuteCommandLine('print -d 4 s1')
    
    kernel.DestroyAgent(agent)
    kernel.Shutdown()
    del kernel

test1()
