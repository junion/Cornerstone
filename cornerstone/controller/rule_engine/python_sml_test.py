
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
 
    # begin-session   
    print agent.RunSelfTilOutput('run')
    events = agent.CreateIdWME(input_link_wme, 'events')
    begin = agent.CreateStringWME(events, 'begin-session', 'nil')
    print agent.RunSelfTilOutput('run')
    
    kernel.DestroyAgent(agent)
    kernel.Shutdown()
    del kernel


