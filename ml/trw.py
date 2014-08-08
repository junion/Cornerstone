
from copy import deepcopy
import numpy as np
from pprint import pprint


class TRW(object):
    def __init__(self, nodes=[], node_vals={}, node_lpots={}, 
                 edges=[], edge_lpots={}, edge_rhos={}):
        np.seterr(all='raise')
        self.nodes = nodes
        self.node_vals = node_vals
        self.node_lpots = node_lpots
        self.edges = edges
        self.edge_lpots = edge_lpots
        self.edge_pots = deepcopy(edge_lpots)
        self.nbrs = {}
        self.node_rhos = {}            
        for node in self.nodes:
            self.nbrs[node] = [edge[1] for edge in self.edges if edge[0] == node] +\
            [edge[0] for edge in self.edges if edge[1] == node]
            self.node_rhos[node] = [self.edge_rhos[edge] for edge in self.edges if edge[0] == node] +\
            [self.edge_rhos[edge] for edge in self.edges if edge[1] == node]
        for edge in self.edges:
            node1, node2 = edge
            pots = self.edge_pots[edge]
            for val1 in self.node_vals[node1]:
                for val2 in self.node_vals[node2]:
                    pots[(val1, val2)] = np.power(np.exp(pots[(val1, val2)]), 1.0/self.edge_rhos[edge])
        self.damp = 0.5
        self.conv_thresh = 1e-6
        self.max_iter = 1000

    def get_marginals_and_partition(self):
        try:        
            # initialize marginal structures
            node_mrg = {}    
            for node in self.nodes:
                node_mrg[node] = {}
                for val in self.node_vals[node]:
                    node_mrg[node][val] = 0.0
            edge_mrg = {}            
            for edge in self.edges:
                edge_mrg[edge] = {}
                node1, node2 = edge
                for val1 in self.node_vals[node1]:
                    for val2 in self.node_vals[node2]:
                        edge_mrg[edge][(val1, val2)] = 0.0
            # initialize message
            n = {}
            for node in self.nodes:
                n[node] = {}
                for val in self.node_vals[node]: 
                    n[node][val] = 1.0
            m = {}
            for node in self.nodes:
                m[node] = {}
                for nbr in self.nbrs[node]:
                    m[node][nbr] = {}
                    for val in self.node_vals[nbr]:
                        m[node][nbr][val] = 1.0
            for reps in range(self.max_iter):
                # compute n[node] and m[from][to]
                for node in self.nodes:
                    npots = self.node_pots[node]
                    # compute n[node]
                    for val in self.node_vals[node]:
                        n[node][val] = 1.0 
                        for k, nbr in enumerate(self.nbrs[node]):
                            n[node][val] *= np.power(m[nbr][node][val], self.node_rhos[node][k]) # check its own potential
                    # compute m[from][to]
                    for nbr in self.nbrs[node]:
                        reversed = True if (node, nbr) in self.edges else False
                        sum = 0.0
                        for val1 in self.node_vals[nbr]:
                            m[node][nbr][val1] = 0.0
                            epots = self.edge_pots[(node, nbr)] if reversed else self.edge_pots[(nbr, node)]
                            for val2 in self.node_vals[node]:
                                index = (val2, val1) if reversed else (val1, val2)
                                m[node][nbr][val1] += epots[index] * npots[val2] * n[node][val2] / m[nbr][node][val2]
                            sum += m[node][nbr][val1]
                        # normalize the message
                        for val in self.node_vals[nbr]:
                            if sum == 0.0:
                                m[node][nbr][val] = 1.0 / len(self.node_vals[nbr])
                            else:                                                          
                                m[node][nbr][val] /= sum
                # compute node marginals
                prev_node_mrg = deepcopy(node_mrg)
                conv = 0.0
                for node in self.nodes:
                    npots = self.node_pots[node]
                    sum = 0.0
                    for val in self.node_vals[node]:
                        node_mrg[node][val] = n[node][val] * npots[val]
                        sum += node_mrg[node][val]
                    # normalize the marginal
                    for val in self.node_vals[node]:
                        if sum == 0.0:
                            node_mrg[node][val] = 1.0 / len(self.node_vals[node])
                        else:
                            node_mrg[node][val] /= sum
                        if prev_node_mrg != {}:
                            conv = max(conv, abs(prev_node_mrg[node][val] - node_mrg[node][val]))
                        else:
                            conv = 1e10
                # compute edge marginals
                for edge in self.edges:
                    epots = self.edge_pots[edge]
                    node1,node2 = edge
                    node1_pot = self.node_pots[node1]
                    node2_pot = self.node_pots[node2]
                    n_node1 = n[node1]
                    n_node2 = n[node2]
                    m_node1_node2 = m[node1][node2]
                    m_node2_node1 = m[node2][node1]
                    sum = 0.0
                    for val1 in self.node_vals[node1]:
                        for val2 in self.node_vals[node2]:
                            edge_mrg[edge][(val1,val2)] = epots[(val1,val2)] * node1_pot[val1] * node2_pot[val2] *\
                            n_node1[val1] * n_node2[val2] / m_node1_node2[val2] / m_node2_node1[val1]
                            sum += edge_mrg[edge][(val1,val2)]
                    # normalize the marginal
                    for val1 in self.node_vals[node1]:
                        for val2 in self.node_vals[node2]:
                            if sum == 0.0:
                                edge_mrg[edge][(val1, val2)] = 1.0 / (len(self.node_vals[node1]) * len(self.node_vals[node2]))
                            else:
                                edge_mrg[edge][(val1, val2)] /= sum
                if conv <= self.conv_thresh:
                    break
            # compute partition function
            node_theta_mrg_prdt = 0.0
            for node in self.nodes:
                nlpots = self.node_lpots[node]
                for val in self.node_vals[node]:
                    if node_mrg[node][val] > 0:
                        node_theta_mrg_prdt += nlpots[val] * node_mrg[node][val]
            edge_theta_mrg_prdt = 0.0
            for edge in self.edges:
                elpots = self.edge_lpots[edge] # note that we need original potential
                node1, node2 = edge
                for val1 in self.node_vals[node1]:
                    for val2 in self.node_vals[node2]:
                        if edge_mrg[edge][(val1, val2)] > 0:
                            edge_theta_mrg_prdt += elpots[(val1, val2)] * edge_mrg[edge][(val1, val2)]
            sum_node_h = 0.0
            for node in self.nodes:
                for val in self.node_vals[node]:
                    if node_mrg[node][val] > 0:
                        sum_node_h -= (1.0 - np.sum(self.node_rhos[node])) * node_mrg[node][val] * np.log(node_mrg[node][val])
            sum_edge_h = 0.0
            for edge in self.edges:
                node1, node2 = edge
                for val1 in self.node_vals[node1]:
                    for val2 in self.node_vals[node2]:
                        if edge_mrg[edge][(val1, val2)] > 0:
                            sum_edge_h -= self.edge_rhos[edge] * edge_mrg[edge][(val1, val2)] * np.log(edge_mrg[edge][(val1, val2)])
            log_partition = node_theta_mrg_prdt + edge_theta_mrg_prdt + sum_node_h + sum_edge_h
            node_mrg.update(edge_mrg)
            return node_mrg, log_partition, reps
        except FloatingPointError as e:
            print 'node_pot'
            pprint(npots)
            print 'n'
            pprint(n)
            print 'm'
            pprint(m)
            raise RuntimeError
        
    def get_log_likelihood(self, labels, zval=None):
        if zval == None:
            _, zval = self.get_marginals_and_partition()
        if np.isinf(zval):
            return np.finfo(np.float32).min
        unnorm_lpot = 0.0
        for node in self.nodes:
            if labels[node] == []:
                _labels = ['None']
            else:
                _labels = labels[node]
            unnorm_lpot_multi_label = 0.0
            for label in _labels:
                unnorm_lpot_multi_label += self.node_lpots[node][label]
            unnorm_lpot_multi_label /= (1.0 * len(_labels))
            unnorm_lpot += unnorm_lpot_multi_label
        for edge in self.edges:
            node1, node2 = edge
            if labels[node1] == []:
                labels1 = ['None']
            else:
                labels1 = labels[node1]
            if labels[node2] == []:
                labels2 = ['None']
            else:
                labels2 = labels[node2]
            unnorm_lpot_multi_label = 0.0
            for label1 in labels1:
                for label2 in labels2:
                    unnorm_lpot_multi_label += self.edge_lpots[edge][(label1,label2)]
            unnorm_lpot_multi_label /= (1.0 * len(labels1) * len(labels2))
            unnorm_lpot += unnorm_lpot_multi_label
        return unnorm_lpot - zval
