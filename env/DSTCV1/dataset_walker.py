
import os, json, re, sys


class dataset_walker(object):
    def __init__(self, dataset, dataroot, labels=False):
        self.dataset = dataset
        self.install_root = os.path.dirname(os.path.abspath(__file__))
        self.dataset_session_list = os.path.join(self.install_root, 'dataset', self.dataset+'.sessions')
        self.labels = labels
        if (dataroot == None):
            install_parent = os.path.dirname(self.install_root)
            self.dataroot = os.path.join(install_parent, 'data')
        else:
            self.dataroot = os.path.join(os.path.abspath(dataroot))

        # load dataset (list of calls)
        self.session_list = []
        f = open(self.dataset_session_list)
        for line in f:
            line = line.strip()
            #line = re.sub('/',r'\\',line)
            #line = re.sub(r'\\+$','',line)
            if (line in self.session_list):
                raise RuntimeError,'Call appears twice: %s' % (line)
            self.session_list.append(line)
        f.close()
        
    def __iter__(self):
        for session_id in self.session_list:
            session_id_list = session_id.split('/')
            session_dirname = os.path.join(self.dataroot, *session_id_list)
            applog_filename = os.path.join(session_dirname, 'dstc.log.json')
            if (self.labels):
                labels_filename = os.path.join(session_dirname, 'dstc.labels.json')
                if (not os.path.exists(labels_filename)):
                    raise RuntimeError, 'Cant score : cant open labels file %s' % (labels_filename)
            else:
                labels_filename = None
            call = Call(applog_filename,labels_filename,self.dataset)
            yield call


class Call(object):
    def __init__(self, applog_filename, labels_filename, dataset):
        self.applog_filename = applog_filename
        self.labels_filename = labels_filename
        self.dataset = dataset
#        print >>sys.stderr,applog_filename
        print applog_filename
        f = open(applog_filename)
        self.log = json.load(f)
        f.close()
        if (labels_filename != None):
            f = open(labels_filename)
            self.labels = json.load(f)
            f.close()
        else:
            self.labels = None

    def __iter__(self):
        if (self.labels_filename != None):
            for (log, labels) in zip(self.log['turns'], self.labels['turns']):
                yield (log, labels)
        else: 
            for log in self.log['turns']:
                yield (log, None)
        
