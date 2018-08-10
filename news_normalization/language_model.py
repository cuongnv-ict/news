# -*- encoding: utf-8 -*-
import unicodedata

import utils
import os, re, sys
import regex
from io import open
import math
from nlp_tools import tokenizer




class language_model:
    def __init__(self, root_dir='.'):
        self.re = regex.regex()
        self.count_bigram = None
        self.count_unigram = None
        self.total_count_tokens = 0
        self.MIN_PROB = math.log(1e-50)
        self.root_dir = root_dir
        self.dataset = os.path.join(self.root_dir, 'markov_dataset')
        language_model.run(self)


    def pre_processing(self, data, predict_mode=False):
        if predict_mode:
            return self.re.run_regex_predict(data)
        else:
            data = data.lower()
            return self.re.run_regex_training(data)


    def build_vocab(self, dataset):
        count_bigram = utils.load(os.path.join(self.root_dir, 'model/count_bigram.dat'))
        count_unigram = utils.load(os.path.join(self.root_dir, 'model/count_unigram.dat'))
        total_count = utils.load(os.path.join(self.root_dir, 'model/total_count_tokens.dat'))
        if count_bigram != None and count_unigram != None and total_count != None:
            return count_bigram, count_unigram, total_count

        stack = os.listdir(dataset)
        count_bigram = {}
        count_unigram = {}
        total_count = 0
        ndocs = 0
        print 'loading data in ' + dataset
        while (len(stack) > 0):
            file_name = stack.pop()
            file_path = dataset + '/' + file_name
            if (os.path.isdir(file_path)):  # neu la thu muc thi day vao strong stack
                utils.push_data_to_stack(stack, file_path, file_name)
            else:
                ndocs += 1
                print ('\r%d - %s' % (ndocs, file_path)),
                sys.stdout.flush()
                try:
                    fp = open(file_path, 'r', encoding='utf-8')
                    sens = [sen for sen in fp]
                except:
                    fp = open(file_path, 'r', encoding='utf-16')
                    sens = [sen for sen in fp]
                for sen in sens:
                    sen = unicodedata.normalize('NFKC', sen.strip())
                    sen_nor = self.pre_processing(tokenizer.predict(sen).lower(), predict_mode=False)
                    sen_nor = sen_nor.split()
                    total_count += len(sen_nor)
                    previous_word = u''
                    for w in sen_nor:
                        self.update_count_unigram(w, count_unigram)
                        if previous_word != u'':
                            self.update_count_bigram(w, previous_word, count_bigram)
                        previous_word = w
                fp.close()
        print(u'')
        # save model
        utils.save(count_bigram, os.path.join(self.root_dir, 'model/count_bigram.dat'))
        utils.save(count_unigram, os.path.join(self.root_dir, 'model/count_unigram.dat'))
        utils.save(total_count, os.path.join(self.root_dir, 'model/total_count_tokens.dat'))
        return count_bigram, count_unigram, total_count


    def update_count_bigram(self, current_token, previous_token, count_token):
        try:
            count_token[current_token[0]][current_token][previous_token] += 1
        except:
            try:
                count_token[current_token[0]][current_token].update({previous_token : 1})
            except:
                try:
                    count_token[current_token[0]].update({current_token : {previous_token : 1}})
                except:
                    if previous_token == u'':
                        count_token.update({current_token[0] : {current_token : {}}})
                    else:
                        count_token.update({current_token[0] : {current_token : {previous_token : 1}}})


    def update_count_unigram(self, token, count_token_ex):
        try:
            count_token_ex[token[0]][token] += 1
        except:
            try:
                count_token_ex[token[0]].update({token : 1})
            except:
                count_token_ex.update({token[0] : {token : 1}})


    @staticmethod
    def run(self):
        print 'language model is running...'
        self.count_bigram, self.count_unigram, \
        self.total_count_tokens = self.build_vocab(self.dataset)


    def get_markov_chain_score(self, context):
        words = context.split()
        previous_word = words[0]
        prob = 0.0
        '''
        p(w1w2w3w4) = p(w1).p(w2|w1).p(p3|w2).p(w4|w3)
        p(w2|w1) = count(w2|w1) / count(w1)
        where w1 and w4 are constant so p(w1) is constant
        '''
        try:
            c = previous_word[0]
            prob = math.log(float(self.count_unigram[c][previous_word]) /
                            float(self.total_count_tokens))
        except:
            prob += self.MIN_PROB
        for i in xrange(1, len(words)):
            current_word = words[i]
            try:
                c = current_word[0]
                stastistic = self.count_bigram[c][current_word][previous_word]
                cc = previous_word[0]
                total = self.count_unigram[cc][previous_word]
                prob += math.log(float(stastistic) / float(total))
            except:
                prob += self.MIN_PROB
            previous_word = current_word
        return prob


    def restore_info(self, q, number, url, email, datetime, mark, mark2):
        q = self.restore_info_ex(q, mark2, u'6')
        q = self.restore_info_ex(q, mark, u'5')
        q = self.restore_info_ex(q, datetime, u'4')
        q = self.restore_info_ex(q, email, u'3')
        q = self.restore_info_ex(q, url, u'2')
        q = self.restore_info_ex(q, number, u'1')
        return q


    def restore_info_ex(self, q, data, mask):
        q = q.replace(u'%', u'%%')
        q = re.sub(mask, u'%s', q)
        data = tuple(data)
        try:
            q = q % data  # use format string to get best performance
        except:
            pass
        q = q.replace(u'%%', u'%')
        return q




if __name__ == '__main__':
    lm = language_model()
    pass
