import sys,os,argparse,shutil,glob,json,pprint,copy

SLOT_GROUPS = ['route','from.desc','from.neighborhood','from.monument','to.desc','to.neighborhood','to.monument','date','time']
META_SLOT_GROUPS = SLOT_GROUPS + ['joint']
SLOT_TO_GROUP = {}
for slot in SLOT_GROUPS:
    if (slot in ['date','time']): 
        continue
    SLOT_TO_GROUP[slot] = slot
SLOT_TO_GROUP['time.ampm'] = 'time'
SLOT_TO_GROUP['time.minute'] = 'time'
SLOT_TO_GROUP['time.hour'] = 'time'
SLOT_TO_GROUP['time.arriveleave'] = 'time'
SLOT_TO_GROUP['time.rel'] = 'time'
SLOT_TO_GROUP['date.day'] = 'date'
SLOT_TO_GROUP['date.absmonth'] = 'date'
SLOT_TO_GROUP['date.absday'] = 'date'
SLOT_TO_GROUP['date.relweek'] = 'date'

def main(argv):
    #
    # CMD LINE ARGS
    # 
    install_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    utils_dirname = os.path.join(install_path,'lib')
    version_filename = os.path.join(install_path,'VERSION')
    f = open(version_filename)
    scorer_version = f.readline().strip()
    f.close()
    sys.path.append(utils_dirname)
    from dataset_walker import dataset_walker
    list_dir = os.path.join(install_path,'config')

    parser = argparse.ArgumentParser(description='Validate output from a belief tracker.')
    parser.add_argument('--dataset', dest='dataset', action='store', metavar='DATASET', required=True,
                        help='The dataset to analyze, for example train1 or test2 or train3a')
    parser.add_argument('--dataroot',dest='dataroot',action='store', metavar='PATH', required=True,
                        help='Will look for corpus in <destroot>/<dataset>/...')
    parser.add_argument('--trackfile',dest='scorefile',action='store',metavar='JSON_FILE',required=True,
                        help='File containing score JSON')
    args = parser.parse_args()

    sessions = dataset_walker(args.dataset,dataroot=args.dataroot,labels=False)    
    tracker_results = json.load(open(args.scorefile))
    
    validator = TrackerValidator(sessions,tracker_results)
    validator.Validate()
    print validator.Report()

class TrackerValidator(object):
    def __init__(self,sessions,tracker_results):
        self.sessions = sessions
        self.tracker_results = tracker_results
        self.parse_stack = []
        self.error_log = []
        self.session_counter = None
        from lib.DictDict import DictDict 
        self.DictDict = DictDict

    def Report(self):
        s = []
        for entry in self.error_log:
            stack_str = ''
            for item in entry['stack']:
                stack_str += '[%s]' % (item)
            s.append('%s\t%s' % (entry['msg'],stack_str))
        return '\n'.join(s)

    def _CheckDictKeys(self,dict_to_check,required,optional):
        if (isinstance(dict_to_check,dict)):
            for k in dict_to_check:
                if (k not in required and k not in optional):
                    self._LogError('key present which is neither optional nor required: %s' % (k))
            for k in required:
                if (k not in dict_to_check):
                    self._LogError('required key missing: %s' % (k))
        else:
            self._LogError('Should be a dict; instead found type %s (%s)' % (type(dict_to_check),dict_to_check))

    def _AddSlotValPairFromList(self,slots,all_slot_val_pairs):
        date = {}
        time = {}
        for slot,val in slots:
            if (slot.startswith('date')):
                date[slot] = val
            elif (slot.startswith('time')):
                time[slot] = val
            else:
                all_slot_val_pairs.Set({ slot: val }, True)
        if (len(date) > 0):
            all_slot_val_pairs.Set(date,True)
        if (len(time) > 0):
            all_slot_val_pairs.Set(time,True)

    def _LogError(self,err_msg):        
        self.error_log.append({
                'stack': copy.copy(self.parse_stack),
                'msg': err_msg,
                })
        return

    def Validate(self):
        for session_tracker,session in zip(self.tracker_results['sessions'],self.sessions):
            self.session_counter = 0 if self.session_counter == None else self.session_counter + 1
            session_id = session.log['session-id']
            self.parse_stack.append( session_id )
            self._CheckDictKeys(session_tracker,required=['session-id','turns'],optional=[])
            if ('session-id' not in session_tracker or 'turns' not in session_tracker):
                self._LogError('Skipping remaining checks for this session')
                self.parse_stack.pop(-1)
                continue
            if (session_id != session_tracker['session-id']):
                self._LogError('Session index %s: session-id of %s disagrees with dataset (%s); skipping remaining checks for this session' % (self.session_counter,session_id,session_tracker['session-id']))
                self.parse_stack.pop(-1)
                continue
            turn_count = 0
            for log_turn in session:
                turn_count += 1
            if (turn_count != len(session_tracker['turns'])):
                self._LogError('Different number of turns in tracker output (%s) and dataset (%s); skipping this session' % (len(session_tracker['turns']),turn_count))
            turn_index = 0
            self.parse_stack.append('turns')
            all_slot_val_pairs = self.DictDict()
            for (log_turn,label_turn),tracker_turn in zip(session,session_tracker['turns']):
                # gather recognized hyps from log_turn
                # include impl-conf, expl-conf, and user input
                for live_batch in ['live','batch']:
                    if (live_batch in log_turn['input']):
                        for i1,slu_nbest_entry in enumerate(log_turn['input'][live_batch]['slu-hyps']):
                            for i2,slu_hyp in enumerate(slu_nbest_entry['slu-hyp']):
                                slot_pairs = self._AddSlotValPairFromList(slu_hyp['slots'],all_slot_val_pairs)
                if ('dialog-act' in log_turn['output']):
                    for sys_act in log_turn['output']['dialog-acts']:
                        if (sys_act['act'] in ['expl-conf','impl-conf']):
                            # dont include confirmations of acts
                            if (len(sys_act['slots']) == 1 and sys_act['slots'][0][0] == 'act'):
                                continue
                            slot_pairs = self._AddSlotValPairFromList(slu_hyp['slots'],all_slot_val_pairs)

                # now check user input
                self.parse_stack.append( turn_index )
                turn_index += 1
                self._CheckDictKeys(tracker_turn,required=[],optional=META_SLOT_GROUPS)
                for slot_group in META_SLOT_GROUPS:
                    slot_group_score_total = 0.0
                    if (slot_group not in tracker_turn):
                        continue
                    self.parse_stack.append( slot_group )
                    self._CheckDictKeys(tracker_turn[slot_group],required=['hyps'],optional=[])
                    if ('hyps' not in tracker_turn[slot_group]):
                        self._LogError('Skipping remaining checks for this (meta) slot group')
                        self.parse_stack.pop(-1)
                        continue
                    score_total = 0.0
                    if (slot_group == 'joint'):
                        allowed_slot_groups = SLOT_GROUPS
                    else:
                        allowed_slot_groups = [ slot_group ]
                    for i,tracker_hyp in enumerate(tracker_turn[slot_group]['hyps']):
                        self.parse_stack.append(i)
                        self._CheckDictKeys(tracker_hyp,required=['slots','score'],optional=[])
                        if ('slots' not in tracker_hyp or 'score' not in tracker_hyp):
                            self._LogError('Skipping remaining checks for this slot hyp')
                            self.parse_stack.pop(-1)
                            continue
                        self.parse_stack.append('slots')
                        if (len(tracker_hyp['slots']) == 0):
                            self._LogError('Empty slots dict; this entry will be marked as incorrect')
                        partitioned_hyp = {}
                        for slot,val in tracker_hyp['slots'].items():
                            if (slot not in SLOT_TO_GROUP):
                                self._LogError('Dont recognize slot %s' % (slot)) 
                                continue
                            this_slot_group = SLOT_TO_GROUP[slot]
                            if (this_slot_group not in allowed_slot_groups):
                                self._LogError('Found slot %s in slot group %s; doesnt belong here' % (slot,slot_group))
                                continue
                            if (this_slot_group not in partitioned_hyp):
                                partitioned_hyp[this_slot_group] = {}
                            if (slot in partitioned_hyp[this_slot_group]):
                                self._LogError('Slot %s appears more than once in hyp; keeping only first' % (slot))
                                continue
                            partitioned_hyp[this_slot_group][slot] = val
                        for hyp_dict in partitioned_hyp.values():
                            if (not all_slot_val_pairs.HasKey( hyp_dict )):
                                self._LogError('This hypothesis hasnt been recognized before: %s' % (hyp_dict))
                        self.parse_stack.pop(-1)
                        self.parse_stack.append('score')
                        score = tracker_hyp['score']
                        if (score < 0.0):
                            self._LogError('Score %s is less than 0.0 -- will be changed to 0.0 when scored' % (score))
                            score = 0.0
                        if (score > 1.0):
                            self._LogError('Score %s is more than 1.0' % (score))
                        score_total += score
                        self.parse_stack.pop(-1)
                        self.parse_stack.pop(-1)
                    if (score_total > 1.0):
                        self._LogError('Score total is %s which is greater than 1.0 -- will be normalized to 0.0 when scored' % (score_total))
                    self.parse_stack.pop(-1)
                self.parse_stack.pop(-1)
            self.parse_stack.pop(-1)
            self.parse_stack.pop(-1)

if (__name__ == '__main__'):
    main(sys.argv)

    
