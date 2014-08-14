import sys,os,argparse,shutil,glob,json

META_SLOTS = ['route','from.desc','from.monument','from.neighborhood','to.desc','to.monument','to.neighborhood','date','time','joint','all']

def main(argv):
    #
    # CMD LINE ARGS
    # 
#     install_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#     utils_dirname = os.path.join(install_path,'lib')
#     sys.path.append(utils_dirname)
    from dataset_walker import dataset_walker
#     list_dir = os.path.join(install_path,'config')

    parser = argparse.ArgumentParser(description='Formats a scorefile into a report and prints to stdout.')
    parser.add_argument('--scorefile',dest='csv',action='store',required=True,metavar='CSV_FILE',
                        help='File to read with CSV scoring data')
    parser.add_argument('--reportfile',dest='report',action='store',required=True,metavar='TXT_FILE',
                        help='File to write with a TXT report')
    args = parser.parse_args()

    csvfile = open(args.csv)

    scoredata = {}
    basic_stats = {}
    for line in csvfile:
        (meta_slot,schedule,print_name,N,r) = line.strip().split(',')
        if (meta_slot == 'basic'): 
            basic_stats[print_name] = r
            continue
        if (schedule not in scoredata): scoredata[schedule] = {}
        if (meta_slot not in scoredata[schedule]): scoredata[schedule][meta_slot] = {}
        if (print_name not in scoredata[schedule][meta_slot]): scoredata[schedule][meta_slot][print_name] = {}
        scoredata[schedule][meta_slot][print_name]['N'] = int(N)
        scoredata[schedule][meta_slot][print_name]['r'] = None if (r=='None') else float(r)
    csvfile.close()

    reportfile = open(args.report,'w')
    for schedule in scoredata:
        print >>reportfile,'------------------------------------------------------------------------------------------'
        print >>reportfile,'                                    %s' % (schedule)
        print >>reportfile,'------------------------------------------------------------------------------------------'
        # meta_slots = sorted(scoredata[schedule])        
        print >>reportfile,'%13s %s' % ('',' '.join([ '%6s' % meta_slot[:6] for meta_slot in META_SLOTS]))
        print_names = []
        N = {}        
        for meta_slot in scoredata[schedule]:
            for print_name in scoredata[schedule][meta_slot]:
                if print_name not in print_names: 
                    print_names.append(print_name)
                if (meta_slot not in N):
                    N[meta_slot] = scoredata[schedule][meta_slot][print_name]['N']
                elif (N[meta_slot] != scoredata[schedule][meta_slot][print_name]['N']):
                    print >>reportfile,'WARNING: N differs in %s, %s' % (schedule,meta_slot)
        
        N_print = {}
        for meta_slot in META_SLOTS:
            N_print[meta_slot] = '%6d' % N[meta_slot] if meta_slot in N else '%6s' % 'na'
        print >>reportfile,'%13s %s' % ('N',' '.join( [ N_print[meta_slot] for meta_slot in META_SLOTS ]))
        for print_name in sorted(print_names):
            stats = []
            for meta_slot in META_SLOTS:
                if (meta_slot not in scoredata[schedule] or 
                    print_name not in scoredata[schedule][meta_slot] or
                    scoredata[schedule][meta_slot][print_name]['r'] == None):
                    stat = '%6s' % ('-')
                else:
                    stat = '%0.4f' % (scoredata[schedule][meta_slot][print_name]['r'])
                stats.append(stat)
            print >>reportfile,'%13s %s' % (print_name,' '.join(stats))
        print >>reportfile,''
    print >>reportfile,'------------------------------------------------------------------------------------------'
    print >>reportfile,'                                    basic stats'
    print >>reportfile,'------------------------------------------------------------------------------------------'
    for k in sorted(basic_stats.keys()):
        v = basic_stats[k]
        print >>reportfile,'%20s : %s' % (k,v)
    print >>reportfile,''
    reportfile.close()
    
    for schedule in scoredata:
        print '------------------------------------------------------------------------------------------'
        print '                                    %s' % (schedule)
        print '------------------------------------------------------------------------------------------'
        # meta_slots = sorted(scoredata[schedule])        
        print '%13s %s' % ('',' '.join([ '%6s' % meta_slot[:6] for meta_slot in META_SLOTS]))
        print_names = []
        N = {}        
        for meta_slot in scoredata[schedule]:
            for print_name in scoredata[schedule][meta_slot]:
                if print_name not in print_names: 
                    print_names.append(print_name)
                if (meta_slot not in N):
                    N[meta_slot] = scoredata[schedule][meta_slot][print_name]['N']
                elif (N[meta_slot] != scoredata[schedule][meta_slot][print_name]['N']):
                    print 'WARNING: N differs in %s, %s' % (schedule,meta_slot)
        
        N_print = {}
        for meta_slot in META_SLOTS:
            N_print[meta_slot] = '%6d' % N[meta_slot] if meta_slot in N else '%6s' % 'na'
        print '%13s %s' % ('N',' '.join( [ N_print[meta_slot] for meta_slot in META_SLOTS ]))
        for print_name in sorted(print_names):
            stats = []
            for meta_slot in META_SLOTS:
                if (meta_slot not in scoredata[schedule] or 
                    print_name not in scoredata[schedule][meta_slot] or
                    scoredata[schedule][meta_slot][print_name]['r'] == None):
                    stat = '%6s' % ('-')
                else:
                    stat = '%0.4f' % (scoredata[schedule][meta_slot][print_name]['r'])
                stats.append(stat)
            print '%13s %s' % (print_name,' '.join(stats))
        print ''
    print '------------------------------------------------------------------------------------------'
    print '                                    basic stats'
    print '------------------------------------------------------------------------------------------'
    for k in sorted(basic_stats.keys()):
        v = basic_stats[k]
        print '%20s : %s' % (k,v)
    print ''

if (__name__ == '__main__'):
    main(sys.argv)

