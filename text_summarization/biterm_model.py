# -*- encoding: utf-8 -*-

__author__ = 'nobita'

import os
from random import randint, uniform
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from document import document
import operator
from io import open
import utils
from regex import regex
from nlp_tools import spliter


importance_pos = {'N':True, 'Np':True, 'Ny':True, 'V':True}

class biterm:
    def __init__(self, num_iters=100, root_dir='.'):
        self.K = 5 # number topic
        self.W = None # vocab size
        self.alpha = 0.01 # hyperparameters of p(z)
        self.beta = 0.01 # hyperparameters of p(w|z)
        self.n_iters = num_iters # number iterator of gibbs sampling
        self.theta = None # p(z)
        self.phi = None  # p(w|z)
        self.nb_z = None # the number of biterms assigned to the topic z
        self.nw_z = None # the number of times of the word w assigned to the topic z
        self.btm_info = []
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 1), max_df=0.6,
                                          min_df=1, max_features=200,
                                          stop_words=utils.load_data_to_list(os.path.join(root_dir, 'stopwords.txt')))
        self.re = regex()
        self.MINIMUM_LENGTH_SENTENCE = 5
        self.NUM_SEN_SHORT_TEXT = 15
        self.NUM_SEN_LONG_TEXT = 25


    def init_model(self):
        # print 'init model ...'
        self.theta = np.zeros((self.K))
        self.phi = np.zeros((self.K, self.W))
        self.nb_z = np.zeros((self.K), dtype=np.int)
        self.nw_z = np.zeros((self.K, self.W), dtype=np.int)
        k = self.K - 1
        for b in self.btm_info:
            z = randint(0, k)
            self.assign_biterm_topic(b, z)


    def preprocessing(self, data):
        data = self.re.detect_url.sub(u'url', data)
        data = self.re.detect_email.sub(u'email', data)
        data = self.re.detect_datetime.sub(u'datetime', data)
        data = self.re.detect_num.sub(u'number', data)
        # data = self.re.detect_non_vnese.sub(u'', data)
        data = self.re.detect_exception_chars.sub(u'', data)
        data = self.re.normalize_space.sub(u' ', data)
        return data.strip()


    # tranform data to biterm format:
    # wid wid wid wid wid ...
    def tranform(self, raw_data):
        raw_sentences, clean_sentences = self.get_sentences(raw_data)
        self.set_num_topic(len(clean_sentences))
        if self.vectorizer.max_df * len(clean_sentences) < self.vectorizer.min_df:
            self.vectorizer.max_df = 1.0
        # print len(clean_sentences)
        try:
            self.vectorizer.fit(clean_sentences)
        except:
            try:
                self.vectorizer.max_df = 1.0
                self.vectorizer.fit(clean_sentences)
            except:
                try:
                    self.vectorizer.fit(raw_sentences)
                except: return []
        self.W = len(self.vectorizer.vocabulary_)
        # print ('Vocab length = %d' % (self.W))
        docs = []
        for sen in raw_sentences:
            doc = document()
            doc.get_doc_info(sen, self.vectorizer.vocabulary_)
            docs.append(doc)
        return docs


    def set_num_topic(self, num_sen):
        if num_sen < self.NUM_SEN_SHORT_TEXT:
            self.K = 5
            self.vectorizer.max_features = 150
        elif num_sen >= self.NUM_SEN_LONG_TEXT:
            self.K = 15
            self.vectorizer.max_features = 300
        else:
            self.K = 10
            self.vectorizer.max_features = 200


    def get_sentences(self, data):
        raw_sentences = []; clean_sentences = []
        sen = spliter.split(data)
        raw_sentences.extend(sen)
        clean_sentences.extend(map(self.preprocessing, sen))
        raw_sentences_final = []
        clean_sentences_final = []
        for i in xrange(len(raw_sentences)):
            if len(raw_sentences[i].split()) < self.MINIMUM_LENGTH_SENTENCE or \
                len(clean_sentences[i].split()) < self.MINIMUM_LENGTH_SENTENCE:
                continue
            raw_sentences_final.append(raw_sentences[i])
            clean_sentences_final.append(clean_sentences[i])
        return raw_sentences_final, clean_sentences_final


    def restore_info(self, sen, num, acronyms):
        i_num = 0; i_acronym = 0
        for k, s in enumerate(sen):
            s = list(s)
            for j, c in enumerate(s):
                if c == u'1':
                    s[j] = num[i_num]
                    i_num += 1
                elif c == u'2':
                    s[j] = acronyms[i_acronym]
                    i_acronym += 1
            sen[k] = u''.join(s)
        return sen


    def load_data(self, corpus):
        # print 'loading data ...'
        docs = self.tranform(corpus)
        for doc in docs:
            self.btm_info.extend(doc.btm_info)
        return docs


    def assign_biterm_topic(self, btm, k):
        self.nb_z[k] += 1
        self.nw_z[k][btm.w_i] += 1
        self.nw_z[k][btm.w_j] += 1
        btm.set_topic_assign(k)


    def reset_biterm_topic(self, btm):
        self.nb_z[btm.z] -= 1
        self.nw_z[btm.z][btm.w_i] -= 1
        self.nw_z[btm.z][btm.w_j] -= 1
        btm.reset_topic_assign()


    def update_biterm(self, btm):
        self.reset_biterm_topic(btm)
        k = self.compute_pz_b(btm)
        self.assign_biterm_topic(btm, k)


    def compute_pz_b(self, btm):
        w_i = btm.w_i; w_j = btm.w_j
        pz = np.zeros((self.K))
        for k in xrange(self.K):
            denominator = float(2 * self.nb_z[k] + self.W * self.beta)
            pw_i_k = float(self.nw_z[k][w_i] + self.beta) / denominator
            pw_j_k = float(self.nw_z[k][w_j] + self.beta) / (denominator + 1)
            pz[k] = float(self.nb_z[k] + self.alpha) * pw_i_k * pw_j_k
        # normalize self.pz
        total = pz.sum()
        pz = map(lambda x: float(x / total), pz)
        return self.multinomial_sample(pz)


    def multinomial_sample(self, pz):
        for k in xrange(1, len(pz)):
            pz[k] += pz[k - 1]
        factor = uniform(0.0, 1.0)
        threshold = pz[-1] * factor
        k = 0
        for k in xrange(len(pz)):
            if pz[k] >= threshold:
                break
        if k == len(pz):
            return k-1
        return k


    # get theta and phi
    def get_parameters(self):
        # print 'get parameters theta and phi ...'
        self.get_theta()
        self.get_phi()


    def get_phi(self):
        denominator = np.zeros((self.K))
        for k in xrange(self.K):
            denominator[k] = np.sum(self.nw_z[k], dtype=np.int)
            if denominator[k] == 0:
                denominator[k] = 1e7
            for w in xrange(self.W):
                self.phi[k][w] = float(self.nw_z[k][w] + self.beta) / denominator[k]


    def get_theta(self):
        denominator = float(len(self.btm_info) + self.K * self.alpha)
        if denominator == 0:
            denominator = 1e7
        for k in xrange(self.K):
            self.theta[k] = float(self.nb_z[k] + self.alpha) / denominator


    # save results to file
    def save_result(self):
        print 'save result to file ...'
        utils.mkdir('model')
        self.save_vocab('model/vocab.dat')
        # save theta and phi
        np.savetxt('model/theta_final.dat', self.theta)
        np.savetxt('model/phi_final.dat', self.phi)


    def save_vocab(self, file_name):
        vocab = sorted(self.vectorizer.vocabulary_.items(), key=operator.itemgetter(1))
        with open(file_name, 'w', encoding='utf-8') as f:
            words = [w[0] for w in vocab]
            f.write(u'\n'.join(words))


    def run_gibbs_sampling(self, data_train, save_result=False):
        # print 'run gibbs sampling ...'
        docs = self.load_data(data_train)
        if len(docs) == 0:
            return []
        self.init_model()
        # run gibbs sampling epoch
        # print 'run gibbs sampling\'s iterations ...'
        # print('number of iterations = %d' % self.n_iters)
        for it in xrange(self.n_iters):
            # print '\riter = %d' % it,
            for btm in self.btm_info:
                self.update_biterm(btm)
        self.get_parameters()
        if save_result:
            self.save_result()
        # print 'training completed !!!'
        # print 'infer topic proportion for each sentence ...'
        for doc in docs:
            self.infer_topic_document(doc)
        return docs


    # infer topic proportion for docs in traing
    def infer_topic_document(self, doc, method='sum_b'):
        doc.topic_proportion = np.zeros(self.K)
        if method == 'sum_b' and len(doc.data) > 1:
            # print('use sum_b method to infer topic proportion of new doc')
            self.infer_sum_b(doc)
        elif method == 'sum_w' or len(doc.data) == 1:
            # print('use sum_w method to infer topic proportion of new doc')
            self.infer_sum_w(doc)
        else:
            pass
            # print('Warning: don\'t know this method %s' % method)


    def infer_sum_b(self, doc):
        norm = np.zeros(len(doc.btm_info))
        i = 0
        for btm in doc.btm_freq.keys():
            btm = map(int, btm.split('_'))
            for k in xrange(self.K):
                norm[i] += self.theta[k] * self.phi[k][btm[0]] * self.phi[k][btm[1]]
            norm[i] *= len(doc.btm_info)
            i += 1
        for k in xrange(self.K):
            j = 0
            for btm, freq in doc.btm_freq.items():
                btm = map(int, btm.split('_'))
                doc.topic_proportion[k] += freq * self.theta[k] * self.phi[k][btm[0]]\
                                           * self.phi[k][btm[1]] / norm[j]
                j += 1


    def infer_sum_w(self, doc):
        norm = np.zeros(len(doc.word_freq))
        i = 0
        for w in doc.word_freq.keys():
            for k in xrange(self.K):
                norm[i] += self.theta[k] * self.phi[k][w]
            norm[i] *= len(doc.data)
            i += 1
        for k in xrange(self.K):
            j = 0
            for w, freq in doc.word_freq.items():
                doc.topic_proportion[k] += freq * self.theta[k] \
                                           * self.phi[k][w] / norm[j]
                j += 1