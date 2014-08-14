import sys,os,argparse,shutil,glob,json,pprint

SLOT_GROUPS = ['route','from.desc','from.neighborhood','from.monument','to.desc','to.neighborhood','to.monument','date','time']
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
SCHEDULES = ['schedule1','schedule2','schedule3']

def main(argv):
    #
    # CMD LINE ARGS
    # 
#     install_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#     utils_dirname = os.path.join(install_path,'lib')
#     version_filename = os.path.join(install_path,'VERSION')
#     f = open(version_filename)
#     scorer_version = f.readline().strip()
#     f.close()
#     sys.path.append(utils_dirname)
    from dataset_walker import dataset_walker
#     list_dir = os.path.join(install_path,'config')

    parser = argparse.ArgumentParser(description='Evaluate output from a belief tracker.')
    parser.add_argument('--dataset', dest='dataset', action='store', metavar='DATASET', required=True,
                        help='The dataset to analyze, for example train1 or test2 or train3a')
    parser.add_argument('--dataroot',dest='dataroot',action='store', metavar='PATH', required=True,
                        help='Will look for corpus in <destroot>/<dataset>/...')
    parser.add_argument('--trackfile',dest='scorefile',action='store',metavar='JSON_FILE',required=True,
                        help='File containing score JSON')
    parser.add_argument('--scorefile',dest='csv',action='store',metavar='CSV_FILE',required=True,
                        help='File to write with CSV scoring data')
    parser.add_argument('--markfile',dest='markfile',action='store',metavar='JSON_FILE',
                        help='Optional: re-write scorefile with scoring mark-up (for debugging and checking scoring process)')
    parser.add_argument('--csvdetail',dest='csvdetail',action='store',metavar='CSV_FILE',
                        help='Optional: output a CSV file showing how each turn was scored (for error analysis)')
    parser.add_argument('--rocbins',dest='rocbins',action='store',metavar='INT',default=1000,type=int,
                        help='ROC bins to use (default 10000).  Lower numbers make the script run faster, but produce less accurate ROC results.')
    parser.add_argument('--rocdump',dest='rocdump',action='store',metavar='FILE_STEM',
                        help='If present, use this file stem to write out ROC plot data: filestem.<schedule>.<slot>.<type>.csv, where type is either roc (which contains the ROC curve coordinates) or scores (which contains the raw scores used to compute the ROC curves).')
    args = parser.parse_args()

    sessions = dataset_walker(args.dataset,dataroot=args.dataroot,labels=True)    
    tracker_results = json.load(open(args.scorefile))

    csvfile = open(args.csv,'w')
    if (args.csvdetail):
        detail = []
        detail.append( ['session-id','turn-index','slot-group','label','instantiated-label','oracle-label',
                        'schedule1','schedule2','schedule3','top-hyp'] )
    
    stats = {}
    for meta_slot in SLOT_GROUPS + ['joint','all']:
        stats[meta_slot] = {}
        for schedule in SCHEDULES:
            stats[meta_slot][schedule] = {
                'accuracy': Stat_Accuracy(),
                'mrr':      Stat_MRR(),
                'roc':      Stat_ROC(bins=args.rocbins),
                'l2':       Stat_L2(),
                'avgp':     Stat_AverageProb(),
                'nonempty': Stat_NonEmpty(),
                'hypcount': Stat_HypCount(),
                }

    # mark each label hyp as being correct or not
    # also indicate whether each utt is on each kind of "schedule"
    turn_counter = 0
    session_counter = 0
    for session_tracker,session in zip(tracker_results['sessions'],sessions):
        session_counter += 1
        session_id = session.log['session-id']
        offlist_flag = {}
        for meta_slot in SLOT_GROUPS + ['joint']:
            offlist_flag[meta_slot] = True
        labels = {}
        for grounded_slot in SLOT_GROUPS:
            labels[grounded_slot] = {}
        turn_index = 0
        for (log_turn,label_turn),tracker_turn in zip(session,session_tracker['turns']):
            turn_index += 1
            turn_counter += 1
            # check if this was a start-over
            if (log_turn['restart'] == True):
                for grounded_slot in SLOT_GROUPS:
                    labels[grounded_slot] = {}
                for meta_slot in SLOT_GROUPS + ['joint']:
                    offlist_flag[meta_slot] = True

            # accumulate labels
            for slu_label_entry in label_turn['slu-labels']:
                try:
                    slot_group,pairset_key = _MakePairsetKey(slu_label_entry['slots'])
                except ScoreError as e:
                    raise RuntimeError,'Problem with label file: %s' % (e.msg)
                if (pairset_key not in labels[slot_group]):
                    labels[slot_group][pairset_key] = slu_label_entry['label']
                elif (labels[slot_group][pairset_key] == False and slu_label_entry['label'] == True):
                    # the old label was False but the new label is True
                    # change label to True
                    labels[slot_group][pairset_key] = True

            for meta_slot in SLOT_GROUPS + ['joint']:                
                # check if tracker guessed anything at all for this slot 
                if (meta_slot not in tracker_turn):
                    tracker_turn[meta_slot] = {}
                    tracker_turn[meta_slot]['hyps'] = []
                tracker_turn_slot = tracker_turn[meta_slot]

                # sort traker_hyps (in case they weren't sorted already)
                tracker_turn_slot['hyps'].sort(key=lambda x:x['score'],reverse=True)

                #print >>sys.stderr,'Working on session %s, turn %s, slot %s' % (
                #    session.log['session-id'],
                #    log_turn['turn-index'],
                #    meta_slot)

                # check which schedules this turn is on
                if (meta_slot != 'joint'):
                    tracker_turn_slot['schedules'] = GetTurnSchedulesGroundedSlot(log_turn,meta_slot,args.dataset)
                else:
                    tracker_turn_slot['schedules'] = GetTurnSchedulesJoint(tracker_turn)

                # check whether ANY correct value has been observed yet (offlist_flag)
                if (offlist_flag[meta_slot] == True):
                    if (meta_slot != 'joint'):
                        offlist_flag[meta_slot] = AreAllItemsIncorrectGroundedSlot(labels[meta_slot])
                    else:
                        offlist_flag[meta_slot] = AreAllItemsIncorrectJoint(tracker_turn)
                tracker_turn_slot['offlist_flag'] = offlist_flag[meta_slot]

                # compute offlist score
                offlist_score = 1.0
                total = 0.0
                for i,tracker_hyp in enumerate(tracker_turn_slot['hyps']):
                    if (tracker_hyp['score'] < 0.0):
                        print >>sys.stderr,'WARNING: Score is less than 0.0 (%s); changing to 0.0 (session %s, turn %s, slot %s, hyp %s)' % (
                            tracker_hyp['score'],
                            session.log['session-id'],
                            log_turn['turn-index'],
                            meta_slot,
                            i)
                        tracker_hyp['score'] = 0.0
                    offlist_score -= tracker_hyp['score']
                    total += tracker_hyp['score']
                if (offlist_score < 0.0):
                    print >>sys.stderr,'WARNING: Scores sum to more than 1.0 (%s); normalizing and setting offlist_score to 0.0 (session %s, turn %s, slot %s)' % (
                        1.0 - offlist_score,
                        session.log['session-id'],
                        log_turn['turn-index'],
                        meta_slot)
                    offlist_score = 0.0
                    for tracker_hyp in tracker_turn_slot['hyps']:
                        tracker_hyp['score'] = tracker_hyp['score'] / total
                tracker_turn_slot['offlist_score'] = offlist_score

                # assign correctness values to labels 
                for i,tracker_hyp in enumerate(tracker_turn_slot['hyps']):
                    try:
                        tracker_hyp['label'] = AssignLabelToTrackerHyp(tracker_hyp['slots'],labels,meta_slot,tracker_turn)
                    except ScoreError as e:
                        print sys.stderr,'WARNING: %s (session %s, turn %s, slot %s, hyp %s); assigning incorrect' % (e.msg,
                                                                                                           session.log['session-id'],
                                                                                                           log_turn['turn-index'],
                                                                                                           meta_slot,
                                                                                                           i)
                        tracker_hyp['label'] = False

                # for convenience, compute a list of True/False values that describe correctness
                tracker_turn_slot['all-hyps'] = []
                tracker_turn_slot['all-hyps'].append( {
                        'hyp': None, 
                        'label': tracker_turn_slot['offlist_flag'],
                        'score': tracker_turn_slot['offlist_score'],
                })
                for hyp_index,tracker_hyp in enumerate(tracker_turn_slot['hyps']):
                    tracker_turn_slot['all-hyps'].append( {
                            'hyp': tracker_hyp,
                            'label': tracker_hyp['label'],
                            'score': tracker_hyp['score'],
                            })
                tracker_turn_slot['all-hyps'].sort(key=lambda x: x['score'],reverse=True)

                # compute stats according to each schedule
                for schedule in SCHEDULES:
                    if ( tracker_turn_slot['schedules'][schedule] ):
                        for stat_type in stats[meta_slot][schedule]:
                            stats[meta_slot][schedule][stat_type].AddTurn(tracker_turn_slot,log_turn)                
                            if (meta_slot in SLOT_GROUPS):
                                stats['all'][schedule][stat_type].AddTurn(tracker_turn_slot,log_turn)

                # save details
                # ['session-id','turn-index','slot-group','label','schedule1','schedule2','schedule3','top-hyp'] 
                if (args.csvdetail):
                    if (tracker_turn_slot['all-hyps'][0]['hyp'] == None):
                        top_hyp = None
                    else:
                        top_hyp_array = []
                        for k in sorted(tracker_turn_slot['all-hyps'][0]['hyp']['slots'].keys()):
                            top_hyp_array.append( [k,tracker_turn_slot['all-hyps'][0]['hyp']['slots'][k]] )
                        top_hyp = ';'.join( [ '='.join([k,str(v)]) for k,v in top_hyp_array] )
                    # is top instantiated hyp correct?
                    for tracker_hyp in tracker_turn_slot['all-hyps']:
                        if (tracker_hyp['hyp'] != None):
                            instantiated_label = tracker_hyp['label']
                            break
                    else:
                        instantiated_label = None

                    for tracker_hyp in tracker_turn_slot['all-hyps']:
                        if (tracker_hyp['hyp'] == None):
                            continue
                        if (tracker_hyp['label'] == True):
                            oracle_label = True
                            break
                    else:
                        oracle_label = False

                    detail.append([
                            session_id,
                            log_turn['turn-index'],
                            meta_slot,
                            tracker_turn_slot['all-hyps'][0]['label'],
                            instantiated_label,
                            oracle_label,
                            tracker_turn_slot['schedules']['schedule1'],
                            tracker_turn_slot['schedules']['schedule2'],
                            tracker_turn_slot['schedules']['schedule3'],
                            top_hyp,
                            ])
                        
            # handle last turn and restart turns for schedule3
            if (len(session.log['turns']) == turn_index or             # this is the last turn
                session.log['turns'][turn_index]['restart'] == True):  # next turn is a restart
                any_slot_found = False
                for grounded_slot in SLOT_GROUPS:
                    if (len(labels[grounded_slot]) > 0):
                        any_slot_found = True
                        tracker_turn_slot = tracker_turn[grounded_slot]
                        tracker_turn_slot['schedules']['schedule3'] = True
                        for stat_type in stats[grounded_slot]['schedule3']:
                            stats[grounded_slot]['schedule3'][stat_type].AddTurn(tracker_turn_slot,log_turn)
                            stats['all']['schedule3'][stat_type].AddTurn(tracker_turn_slot,log_turn)
                if (any_slot_found):
                    tracker_turn_slot = tracker_turn['joint']
                    tracker_turn_slot['schedules']['schedule3'] = True
                    for stat_type in stats['joint']['schedule3']:
                        stats['joint']['schedule3'][stat_type].AddTurn(tracker_turn_slot,log_turn)

    # compute stats according to each schedule
    for meta_slot in sorted(SLOT_GROUPS) + ['joint','all']:
        for schedule in sorted(SCHEDULES):
            if (args.rocdump):
                rocfile = args.rocdump + '.' + schedule + '.' + meta_slot + '.roc.csv'
                stats[meta_slot][schedule]['roc'].DumpROCToFile(rocfile)
                rawfile = args.rocdump + '.' + schedule + '.' + meta_slot + '.scores.csv'
                stats[meta_slot][schedule]['roc'].DumpScoresToFile(rawfile)
            for stat_type in sorted(stats[meta_slot][schedule]):
                R = stats[meta_slot][schedule][stat_type].Result()
                N = stats[meta_slot][schedule][stat_type].N
                for name,r in sorted(R,key=lambda x:x[0]):
                    if (name == ''):
                        print_name = stat_type
                    else:
                        print_name = '%s.%s' % (stat_type,name)
                    print >>csvfile,'%s,%s,%s,%s,%s' % (meta_slot,schedule,print_name,N,r)

    print >>csvfile,'basic,,total_wall_time,,%s' % (tracker_results['wall-time'])
    print >>csvfile,'basic,,sessions,,%s' % (session_counter)
    print >>csvfile,'basic,,turns,,%s' % (turn_counter)
    print >>csvfile,'basic,,wall_time_per_turn,,%s' % (tracker_results['wall-time'] / turn_counter)
    print >>csvfile,'basic,,dataset,,%s' % (tracker_results['dataset'] )
#     print >>csvfile,'basic,,scorer_version,,%s' % (scorer_version )
    
    csvfile.close()

    # optional: save label file
    if (args.markfile):
        f = open(args.markfile,'w')
        json.dump(tracker_results,f,indent=2)
        f.close()

    # optional: save csvdetail file
    if (args.csvdetail):
        f = open(args.csvdetail,'w')
        for row in detail:
            print >>f,','.join( [str(x) for x in row] )
        f.close()

class Stat_NonEmpty(object):
    def __init__(self):
        self.N = 0
        self.non_empty = 0

    def AddTurn(self,tracker_turn_slot,log_turn):
        self.N += 1
        if (len(tracker_turn_slot['all-hyps'])>1):
            self.non_empty += 1

    def Result(self):
        if (self.N == 0):
            r = None
        else:
            r = 1.0 * self.non_empty / self.N
        return [['',r]]

class Stat_HypCount(object):
    def __init__(self):
        self.N = 0
        self.hyp_count = 0

    def AddTurn(self,tracker_turn_slot,log_turn):
        self.N += 1
        self.hyp_count += len(tracker_turn_slot['all-hyps'])-1

    def Result(self):
        if (self.N == 0):
            r = None
        else:
            r = 1.0 * self.hyp_count / self.N
        return [['',r]]

class Stat_Accuracy(object):
    def __init__(self):
        self.N = 0
        self.correct = 0

    def AddTurn(self,tracker_turn_slot,log_turn):
        self.N += 1
        if (tracker_turn_slot['all-hyps'][0]['label'] == True):
            self.correct += 1

    def Result(self):
        if (self.N == 0):
            r = None
        else:
            r = 1.0 * self.correct / self.N
        return [['',r]]

class Stat_L2(object):
    def __init__(self):
        self.N = 0
        self.sum_of_L2_diffs = 0.0

    def AddTurn(self,tracker_turn_slot,log_turn):
        self.N += 1
        correct_total = 0.0
        for n,entry in enumerate(tracker_turn_slot['all-hyps']):
            if (entry['label'] == True):                
                correct_total += entry['score']
        incorrect_total = 1.0 - correct_total 
        self.sum_of_L2_diffs += ((1.0 - correct_total)**2 + incorrect_total ** 2) ** 0.5

    def Result(self):
        if (self.N == 0):
            r = None
        else:
            r = 1.0 * self.sum_of_L2_diffs / self.N
        return [['',r]]           

class Stat_AverageProb(object):
    def __init__(self):
        self.N = 0
        self.sum_of_probs = 0.0

    def AddTurn(self,tracker_turn_slot,log_turn):
        self.N += 1
        for n,entry in enumerate(tracker_turn_slot['all-hyps']):
            if (entry['label'] == True):                
                p = entry['score']
                break
        else:
            p = 0.0
        self.sum_of_probs += p

    def Result(self):
        if (self.N == 0):
            r = None
        else:
            r = 1.0 * self.sum_of_probs / self.N
        return [['',r]]           

class Stat_ROC(object):
    def __init__(self,bins=10000):
        self.data = []
        self.bins = bins
        self.current = False
        self.N = len(self.data)

    def AddTurn(self,tracker_turn_slot,log_turn):
        label = tracker_turn_slot['all-hyps'][0]['label']
        score = tracker_turn_slot['all-hyps'][0]['score']
        self.data.append( [label,score] )
        self.current = False
        self.N = len(self.data)

    def _CountBins(self):
        self._data = []
        self._rawdata = []
        if (len(self.data) < 2): 
            return
        self.data.sort(key=lambda x:x[1])
        items = len(self.data)
        min_score = min(self.data,key=lambda x:x[1])[1]
        max_score = max(self.data,key=lambda x:x[1])[1]
        incr = 1.0 * (max_score - min_score) / (self.bins-1)
        thresholds = [min_score + (x*incr) for x in range(self.bins)]
        for threshold_index,threshold in enumerate(thresholds):
            count_TA = 0
            count_FA = 0
            count_TR = 0
            count_FR = 0
            for label,score in self.data:
                if (threshold_index == (self.bins-1) or score < threshold): 
                    # reject
                    if (label == True):
                        count_FR += 1
                    elif (label == False):
                        count_TR += 1
                    else:
                        raise RuntimeError,'Label is not true or false: %s' % (label)
                else:
                    # accept
                    if (label == True):
                        count_TA += 1
                    elif (label == False):
                        count_FA += 1
                    else:
                        raise RuntimeError,'Label is not true or false: %s' % (label)
            self._data.append([
                        threshold,
                        1.0 * count_TA / items,
                        1.0 * count_FA / items,
                        1.0 * count_TR / items,
                        1.0 * count_FR / items,
                        1.0 * count_TA / (count_TA + count_FR) if (count_TA + count_FR)>0 else None,
                        1.0 * count_FA / (count_FA + count_TR) if (count_FA + count_TR)>0 else None,
                        ])
            self._rawdata.append([
                    threshold,
                    count_TA,
                    count_FA,
                    count_TR,
                    count_FR,
                    ])

    def Result(self):
        r = [
             ['v1_eer', self.EER() ],
             ['v1_ca05', self.CA_at_FA(0.05) ],
             ['v1_ca10', self.CA_at_FA(0.10) ],
             ['v1_ca20', self.CA_at_FA(0.20) ],
             ['v2_eer', self.EER(version=2) ],
             ['v2_ca05', self.CA_at_FA(0.05,version=2) ],
             ['v2_ca10', self.CA_at_FA(0.10,version=2) ],
             ['v2_ca20', self.CA_at_FA(0.20,version=2) ],
#             ['v2_ca15', self.CA_at_FA(0.15,version=2) ],
#             ['v2_ca20', self.CA_at_FA(0.20,version=2) ],
#             ['v2_ca25', self.CA_at_FA(0.25,version=2) ],
#             ['v2_ca30', self.CA_at_FA(0.30,version=2) ],
            ]
        return r

    def _CheckCurrent(self):
        if (self.current == False):
            self._CountBins()
            self.current = True

    def CA_at_FA(self,fa_thresh,version=1):
        assert (version in [1,2]),'Dont know version %s' % (version)
        self._CheckCurrent()
        if (self.N < 2):
            return None
        if (version == 1):
            for (t,ta,fa,tr,fr,tpr,fpr) in self._data:            
                if (fa <= fa_thresh):
                    return ta
            raise RuntimeError,'Could not find a place where FA <= FA_THRESH'
        else:
            for (t,ta,fa,tr,fr,tpr,fpr) in self._data:
                if (fpr != None and fpr <= fa_thresh):
                    return tpr
            return None

    def EER(self,version=1):
        self._CheckCurrent()
        if (self.N < 2):
            return None
        if (version == 1):
            for (t,ta,fa,tr,fr,tpr,fpr) in self._data:
                if (fr >= fa):
                    return fr + fa
            raise RuntimeError,'Could not find a place where FR >= FA'
        else:
            for (t,ta,fa,tr,fr,tpr,fpr) in self._data:
                if (fpr != None and tpr != None and fpr <= 1-tpr):
                    return fpr
            return None

    def DumpROCToFile(self,filename):
        self._CheckCurrent()
        f = open(filename,'w')
        print >>f,'threshold,TA,FA,TR,FR,TPR,FPR,count_threshold,count_TA,count_FA,count_TR,count_FR'
        for row,row_raw in zip(self._data,self._rawdata):
            print >>f,','.join( [str(x) for x in row+row_raw])
        f.close()

    def DumpScoresToFile(self,filename):
        self._CheckCurrent()
        f = open(filename,'w')
        print >>f,'label,score'
        for label,score in self.data:
            print >>f,'%s,%s' % (label,score)
        f.close()

class Stat_MRR(object):
    def __init__(self):
        self.N = 0
        self.sum_of_recip_ranks = 0.0

    def AddTurn(self,tracker_turn_slot,log_turn):
        self.N += 1
        for n,entry in enumerate(tracker_turn_slot['all-hyps']):
            if (entry['label'] == True):                
                recip_rank = 1.0 / (n+1)
                break
        else:
            recip_rank = 0.0
        self.sum_of_recip_ranks += recip_rank

    def Result(self):
        if (self.N == 0):
            r = None
        else:
            r = 1.0 * self.sum_of_recip_ranks / self.N
        return [['',r]]

def AreAllItemsIncorrectJoint(tracker_turn):
    for grounded_slot in SLOT_GROUPS:
        if (tracker_turn[grounded_slot]['offlist_flag'] == False):
            return False
    return True
            
def AreAllItemsIncorrectGroundedSlot(label_entry):
    for label_val in label_entry.values():
        if (label_val == True):
            # found an instance of a correct slot value for the taget_slot
            return False
    return True

def GetTurnSchedulesJoint(tracker_turn):
    for grounded_slot in SLOT_GROUPS:
        if (tracker_turn[grounded_slot]['schedules']['schedule2'] == True):
            schedule2 = True
            break
        else:
            schedule2 = False
    return {
        'schedule1': True,
        'schedule2': schedule2,
        'schedule3': False,
        }
            

def GetTurnSchedulesGroundedSlot(log_turn,target_slot,dataset):
    '''
    schedule 1: always true
    schedule 2: true when slot is present in an SLU hyp or in system action; else false
                for joint, schedule 2 is true when ANY slot is present in an SLU hyp or in a system action
    schedule 3: true for very last turn; false otherwise
    [schedule 3 is set outside this fn]
    '''
    attset = True if (dataset.startswith('train3') or dataset.startswith('test3')) else False

    # in train3 release 1.3, a new act want-next-bus was introduced; this removes the need
    # for this test below (although leaving it in causes no harm
    #if (target_slot == 'time' and attset):
    #    # ATT systems ask "do you want times for the next few buses?"
    #    # For 'time' these arent scored; only responses to the question about time is scored
    #    # Look for AskTime or ConfirmTime dialog states
    #    for dialog_state_entry in log_turn['system-specific']['dialog_states']:
    #        if (dialog_state_entry['state'] in ['AskTime','ConfirmTime']):
    #            break
    #    else:
    #        return {
    #            'schedule1': True,
    #            'schedule2': False,
    #            'schedule3': False,
    #            }

    if (target_slot in ['from.neighborhood','to.neighborhood'] and attset):
        # ATT systems produce X.neighborhood in questions but only recognize X.desc
        return {
            'schedule1': True,
            'schedule2': False,
            'schedule3': False,
            }
    schedule2 = _GetSchedule2Val(log_turn,target_slot)
    if (target_slot == 'from.desc' and attset):
        schedule2alt = _GetSchedule2Val(log_turn,'from.neighborhood')
    elif (target_slot == 'to.desc' and attset):
        schedule2alt = _GetSchedule2Val(log_turn,'to.neighborhood')
    else:
        schedule2alt = False
    schedules = {
        'schedule1': True,
        'schedule2': schedule2 or schedule2alt,
        'schedule3': False,
        }
    return schedules

def _GetSchedule2Val(log_turn,target_slot):
    for bl in ['batch','live']:
        if (bl not in log_turn['input']):
            continue
        for slu_hyp in log_turn['input'][bl]['slu-hyps']:
            for act_hyp in slu_hyp['slu-hyp']:
                for slot,val in act_hyp['slots']:
                    if (slot.startswith(target_slot)):
                        return True
    if ('dialog-acts' in log_turn['output']):
        for sys_act in log_turn['output']['dialog-acts']:
            for slot,val in sys_act['slots']:
                if (slot.startswith(target_slot)):
                    return True
    return False

# def AssignLabelToTrackerHyp(tracker_hyp,turn_index,meta_slot,hyp_index,session_id,session_labels,session,last_start_over,tracker_turn):
def AssignLabelToTrackerHyp(tracker_hyp,labels,meta_slot,tracker_turn):
    if (meta_slot == 'joint'):
        # check not all are empty
        if (len(tracker_hyp) == 0):
            raise ScoreError,'A joint hyp cant be empty'
        # group joint hyps into slot groups
        slot_groups = {}
        for grounded_slot in SLOT_GROUPS:
            slot_groups[grounded_slot] = {}
            for tracker_slot,tracker_val in tracker_hyp.items():
                if (tracker_slot.startswith(grounded_slot)):
                    slot_groups[grounded_slot][tracker_slot] = tracker_val
        # score the groups
        for grounded_slot in SLOT_GROUPS:
            if (len(slot_groups[grounded_slot]) == 0):
                # tracker guessed offlist for this slot
                slot_correctness = tracker_turn[grounded_slot]['offlist_flag']
            else:
                slot_correctness = _AssignLabelToTrackerHyp(slot_groups[grounded_slot],labels,grounded_slot)
            if (slot_correctness == False):
                hyp_correctness = False
                break
        else:
            hyp_correctness = True
        return hyp_correctness
    else:
        grounded_slot = meta_slot
        return _AssignLabelToTrackerHyp(tracker_hyp,labels,grounded_slot)

def _AssignLabelToTrackerHyp(tracker_hyp,labels,grounded_slot):
    slot_group,pairset_key = _MakePairsetKey(tracker_hyp)
    if (slot_group == None):
        raise ScoreError,'Cant determine slot group'
    if (slot_group != grounded_slot):
        raise ScoreError,'Found slot that belongs to %s; expected %s' % (slot_group,grounded_slot)
    if (pairset_key not in labels[slot_group]):
        raise ScoreError,'Cant find hypothesis in slot group %s: %s' % (slot_group,pairset_key)
    return labels[slot_group][pairset_key]

class ScoreError(Exception):
    def __init__(self,msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

def _MakePairsetKey(slots):
    if (len(slots) == 0):
        raise ScoreError,'slots dict is empty'
    slot_group = None
    slot_items = []
    for slot in sorted(slots.keys()):
        val = slots[slot]
        if (slot not in SLOT_TO_GROUP):
            raise ScoreError,'dont recognize slot name: %s' % (slot)
        group = SLOT_TO_GROUP[slot]
        if (slot_group == None):
            slot_group = group
        elif (slot_group != group):
            raise ScoreError,'multiple slot groups in one hyp: %s and %s' % (slot_group,group)
        slot_items.append( slot + '=' + str(val) )
    if (len(slots) > 1 and slot_group not in ['date','time']):
        raise ScoreError,'more than one slot-value pair in hyp; this slot group (%s) can only have one' % (slot_group)
    return slot_group,'+'.join(slot_items)

if (__name__ == '__main__'):
    main(sys.argv)

