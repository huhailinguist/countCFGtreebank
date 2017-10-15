'''
process treebanks, get CFG counts
@author: Hai Hu

The input we take are trees that look like this:

( (IP-HLN (NP-PN-SBJ (NR 中) (NR 美)) (VP (PP-LOC (P 在) (NP-PN (NR 沪)))
    (VP (VV 签订) (NP-OBJ (NP (NP (ADJP (JJ 高)) (NP (NN 科技))) (NP (NN 合作))) (NP (NN 协议)))))) )
'''

import sys, re

class Node:
    '''
    A node has
    1) tag, e.g. NP
    2) word, e.g. Apple
    3) children = a list of nodes
    '''
    def __init__(self, tag, word=None):
        self.tag = tag
        self.word = word
        self.children = []


class Tree:
    '''
    A tree has
    1) n = number of nodes
    2) m = number of layers
    3) root = root node
    '''
    def __init__(self, root=None):
        self.root = root
        self.n = 0
        self.m = 0
    def traverse(self):
        pass

class PCFG():
    def __init__(self):
        self.pcfg = {}
        self.grm_rule = {}
        self.lex_rule = {}
        self.grm_lhss = {} # left hand side symbols for grammar rules
        # grm_lhss is a dict of dicts:
        # {S: {'NP VP':2, 'NP VP NP':3}, VP ...}

    def addGrmRule(self, rule):
        self.grm_rule[rule] = self.grm_rule.get(rule, 0)+1
        lhs = rule.split(' -> ')[0]
        rhs = rule.split(' -> ')[1]
        if lhs in self.grm_lhss:
            self.grm_lhss[lhs][rhs] = self.grm_lhss[lhs].get(rhs, 0) + 1
        else:
            self.grm_lhss[lhs] = {rhs : 1}
    def addLexRule(self, rule):
        self.lex_rule[rule] = self.lex_rule.get(rule, 0)+1

def getPCFG(fn, funcTag=False):
    # if funcTag: we have NP-PN-SBJ, otherwise we have NP
    trees = open(fn, encoding='utf8').readlines()
    trees = [x.rstrip() for x in trees]

    grm_rule = {}
    lex_rule = {}

    pcfg = PCFG()

    # for testing:
    # t = '( (IP-HLN (NP-PN-SBJ (NR 中) (NR 美)) (VP (PP-LOC (P 在) (NP-PN (NR 沪))) (VP (VV 签订) (NP-OBJ (NP (NP (ADJP (JJ 高)) (NP (NN 科技))) (NP (NN 合作))) (NP (NN 协议)))))) )'

    for t in trees:
        # -------------- #
        # pre-processing
        # -------------- #
        # if no ROOT symbol, add ROOT
        if t.startswith('( ('): # TODO what about other treebanks: or t.startswith('((') or t.startswith('(  ('):
            # print('No ROOT symbol found! Added "ROOT" as ROOT symbol.')
            t = t.replace('( (', '(ROOT (')

        if t.startswith('(('): #
            # print('No ROOT symbol found! Added "ROOT" as ROOT symbol.')
            t = t.replace('((', '(ROOT (')

        # change ( (FRAG(NR 新华社) to ( (FRAG (NR 新华社) Note the space before '('
        pat = re.compile('(\((?P<tag>[A-z|\-]*?)\()')
        m = pat.findall(t)
        if m:
            # print('\nfound (TAG(TAG! lacking a space!')
            # print([x[0] for x in m])
            # print('BEFORE:', t)
            t = pat.sub(r'(\g<tag> (', t)
            # print('AFTER :', t)

        # index of ( or )
        indBrc = [pos for pos, char in enumerate(t) if char == '(' or char == ')']
        # print(indBrc)

        counter_ntn = 0 # non-terminal node, which includes phrasal nodes AND pos tags!
        stack = []
        tree = Tree()
        i = 0

        while i < len(indBrc): # i is the index in indBrc[]
            if t[indBrc[i]] == '(': # and t[indBrc[indOfBrc+1]] == '(':
                if t[ indBrc[i+1] ] == ')':
                    # ---------------------------- #
                    # terminal node, lexical rules
                    # ---------------------------- #
                    counter_ntn += 1

                    tmp = t[(indBrc[i] + 1) : indBrc[i + 1]] # NR 中
                    tmp = tmp.split(' ')
                    node_tmp = Node(tmp[0], tmp[1]) # NR, 中
                    # print('terminal node:', tmp, 'No.{}'.format(counter_ntn))
                    rule = tmp[0] + ' -> ' + tmp[1]
                    # ----------------------------------------
                    lex_rule[rule] = lex_rule.get(rule, 0) + 1
                    pcfg.addLexRule(rule)
                    # ----------------------------------------

                    # TODO will this happen? probably not
                    if counter_ntn == 1: # root
                        tree.root = node_tmp

                    # add to the children of first node in stack
                    stack[-1].children.append(node_tmp)

                    i += 2 # skip the ')' in terminal node (NR 中)
                    continue # this is used to skip: if t[indBrc[i]] == ')': ?? Maybe not

                else:
                    # ---------------------------- #
                    # a phrasal node, grammar rule
                    # ---------------------------- #
                    counter_ntn += 1
                    tag = t[ (indBrc[i] + 1) : indBrc[i+1] ]
                    tag = tag.rstrip() # get rid of the \s in NP\s

                    if not funcTag: # change NP-PN-SBJ to just NP
                        if '-' in tag:
                            idx_hyphen = tag.find('-')
                            if idx_hyphen >= 2:
                                tag = tag[:idx_hyphen]
                            else:
                                print('tag is:', tag)
                                exit('something wrong when removing functional tags')
                    node_tmp = Node(tag)
                    # print('phrasal node:', tag, 'No.{}'.format(counter_ntn))

                    if counter_ntn == 1: # root
                        tree.root = node_tmp
                    else:
                        # if not root, append to child
                        stack[-1].children.append(node_tmp)

                    # add to stack
                    stack.append(node_tmp)

            if t[indBrc[i]] == ')': # pop a node from the stack
                lastNode = stack.pop(-1)
                LHS = lastNode.tag
                RHS = ' '.join([x.tag for x in lastNode.children])
                rule = LHS + ' -> ' + RHS
                if rule == 'IP -> -NONE-':
                    print(t)
                # print(rule)
                # ----------------------------------------
                grm_rule[rule] = grm_rule.get(rule, 0) + 1
                pcfg.addGrmRule(rule)
                # ----------------------------------------

            i+=1

        # make sure nothing is left in stack
        assert len(stack) == 0

    print()


    print('\nlex_rule:')
    for k, v in lex_rule.items(): # key is rule, value is count
        print('{:>10}\t{}'.format(v, k))
    
    print('\ngrm_rule:')
    for k, v in grm_rule.items():
        print('{:>10}\t{}'.format(v, k))

    print()
    print('num of lex rules:', len(lex_rule))
    print('num of grm rules:', len(grm_rule))

    # print("pcfg.grm_lhss['IP']")
    # for k, v in pcfg.grm_lhss['IP'].items():
    #     print('{:>10}\t{}'.format(v, k))
    # print('\n'.join(pcfg.grm_lhss.keys()))
    # print(len(pcfg.grm_lhss['IP']))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python tbProcess.py filename')
        # getPCFG('brc_split2_test', False)
        # getPCFG('oneSent', False)
    else:
        getPCFG(sys.argv[1], False)


