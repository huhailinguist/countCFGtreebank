#!/usr/bin/env python3
'''
process treebanks, get CFG counts
@author: Hai Hu

The input we take are trees that look like this:

( (IP-HLN (NP-PN-SBJ (NR 中) (NR 美)) (VP (PP-LOC (P 在) (NP-PN (NR 沪)))
    (VP (VV 签订) (NP-OBJ (NP (NP (ADJP (JJ 高)) (NP (NN 科技))) (NP (NN 合作))) (NP (NN 协议)))))) )
'''

import sys, re

class Node:
    """ terminal and non-terminal nodes """
    def __init__(self, tag, word=None):
        self.tag  = tag    # NN
        self.word = word   # apple
        self.children = []
        
    def __repr__(self):
        return self.tag
    
    def __str__(self):
        return self.__repr__()

class PCFG():
    def __init__(self, parseTrees=None, tagToCheck=None):
        self.parseTrees = parseTrees  # a list of parseTrees in penn treebank format
        self.grm_rule = {}  # {"S -> NP VP": 1, ...}
        self.lex_rule = {}  # {"NN -> apple": 1, ...}
        self.grm_lhss = {}  # {"S": {"NP VP":2, "NP VP NP":3}, "VP": {} ...}

        if self.parseTrees:
            self.getPCFG(self.parseTrees, tagToCheck)

    def addGrmRule(self, rule):
        self.grm_rule[rule] = self.grm_rule.get(rule, 0) + 1
        lhs = rule.split(' -> ')[0]
        rhs = rule.split(' -> ')[1]
        if lhs in self.grm_lhss:
            self.grm_lhss[lhs][rhs] = self.grm_lhss[lhs].get(rhs, 0) + 1
        else:
            self.grm_lhss[lhs] = {rhs: 1}

    def addLexRule(self, rule):
        self.lex_rule[rule] = self.lex_rule.get(rule, 0) + 1

    def getPCFG(self, parseTrees, tagToCheck=None, verbose=False, keepFuncTag=True):
        """
        extract a list of CFG rules from parseTrees
        if keepFuncTag: NP-PN-SBJ, otherwise NP, but output of corenlp does not have FuncTag """

        # change ( (FRAG(NR 新华社) to ( (FRAG (NR 新华社) Note the space before '('
        pat = re.compile('(\((?P<tag>[A-z|\-]*?)\()')

        # for testing:
        # t = '( (IP-HLN (NP-PN-SBJ (NR 中) (NR 美)) (VP (PP-LOC (P 在) (NP-PN (NR 沪))) (VP (VV 签订) (NP-OBJ (NP (NP (ADJP (JJ 高)) (NP (NN 科技))) (NP (NN 合作))) (NP (NN 协议)))))) )'

        for t in parseTrees:
            ###  pre-processing  ###
            t = t.strip()
            # if there are ( or ) in the sentence, corenlp doesn't change them to LOB, RCB,
            # so we need to do that: LOB=left opening bracket, RCB=right closing bracket
            t = t.replace('PU (', 'PU LOB').replace('PU )', 'PU RCB')
            # if no ROOT symbol, add ROOT
            if t.startswith('( ('):
                t = t.replace('( (', '(ROOT (')
            if t.startswith('(('):
                t = t.replace('((', '(ROOT (')
            m = pat.findall(t)
            if m:
                t = pat.sub(r'(\g<tag> (', t)

            # index of ( or )
            indBrc = [pos for pos, char in enumerate(t) if char == '(' or char == ')']

            stack = []
            counter_ntn = 0
            i = 0

            ###  real work  ###
            while i < len(indBrc):  # i is the index in indBrc[]
                if t[indBrc[i]] == '(':
                    # if current Brc is ( and next is )
                    # terminal node, lexical rules
                    if t[indBrc[i + 1]] == ')':
                        tagNword = t[ (indBrc[i] + 1): indBrc[i + 1] ].split(' ')  # ['NR', '中']
                        termNode = Node(tagNword[0], tagNword[1])
                        lex_rule = tagNword[0] + ' -> ' + tagNword[1]
                        self.addLexRule(lex_rule)

                        # add to the children of first node in stack
                        stack[-1].children.append(termNode)

                        i += 2  # skip the ')' in terminal node (NR 中)

                    # current Brc is (, next is also (
                    # a phrasal node, grammar rule
                    else:
                        tag = t[(indBrc[i] + 1): indBrc[i + 1]].rstrip()

                        if not keepFuncTag:  # change NP-PN-SBJ to just NP
                            if '-' in tag:
                                idx_hyphen = tag.find('-')
                                if idx_hyphen >= 2:
                                    tag = tag[:idx_hyphen]
                                else:
                                    print('tag is:', tag)
                                    exit()
                        nonTermNode = Node(tag)
                        
                        counter_ntn += 1
                        if counter_ntn == 1:  # root
                            pass
                        else:
                            # if not root, append to child of most recent node
                            stack[-1].children.append(nonTermNode)
                            
                        # add to stack
                        stack.append(nonTermNode)
                        i += 1

                # current node is )
                elif t[indBrc[i]] == ')':  # pop a node from the stack
                    lastNode = stack.pop(-1)
                    LHS = lastNode.tag
                    RHS = ' '.join([x.tag for x in lastNode.children])
                    grmrule = LHS + ' -> ' + RHS
                    self.addGrmRule(grmrule)
                    i += 1

            # make sure nothing is left in stack
            assert len(stack) == 0

        if verbose:
            print('\nlex_rule:')
            for k, v in sorted(self.lex_rule.items(), key=lambda x: x[1]):  # key is rule, value is count
                print('{:>10}\t{}'.format(v, k))

            print('\ngrm_rule:')
            for k, v in sorted(self.grm_rule.items(), key=lambda x: x[1]):
                print('{:>10}\t{}'.format(v, k))

            print('num of lex rules:', len(self.lex_rule))
            print('num of grm rules:', len(self.grm_rule))

        if tagToCheck is not None:
            print("pcfg.grm_lhss[{}]".format(tagToCheck))
            for k, v in sorted(self.grm_lhss[tagToCheck].items(), key=lambda x: x[1]):
                print('{:>10}\t{}'.format(v, k))
            print('\n# of rule types :', len(self.grm_lhss[tagToCheck]))
            print('# of rule counts:', sum(self.grm_lhss[tagToCheck].values()))

def main(args):
    trees = open(args[1]).readlines()
    if len(args) == 2:
        pcfg = PCFG(trees)
    else:
        pcfg = PCFG(trees, args[2])
            
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python tbProcess.py filename (tag)')
    else:
        main(sys.argv)
