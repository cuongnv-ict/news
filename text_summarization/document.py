# -*- encoding: utf-8 -*-
__author__ = 'nobita'

from biterm_info import biterm_info



class document:
    def __init__(self):
        self.length = 0
        self.word_freq = {}
        self.data = []
        self.btm_info = [] # list of biterm_info
        self.btm_freq = {}
        self.content = u''
        self.topic_proportion = None
        self.BTM_WINDOW_LENGTH = 2


    def get_doc_info(self, doc, vocab):
        self.content = doc
        # new_doc = self.remove_stop_postag(doc)
        # words = new_doc.lower().split(u' ')
        words = doc.lower().split()
        for w in words:
            try:
                wid = vocab[w]
                try:
                    self.word_freq[wid] += 1
                except: self.word_freq[wid] = 1
                self.data.append(wid)
            except: continue
        self.length = len(self.data)
        self.gen_biterm()


    def is_exist(self, postag):
        try:
            _ = self.importance_pos[postag]
            return True
        except:
            return False


    def gen_biterm(self):
        if len(self.data) < 2: return
        for i in xrange(len(self.data) - 1):
            w1 = self.data[i]
            for j in xrange(i+1, min(i + self.BTM_WINDOW_LENGTH, len(self.data))):
                w2 = self.data[j]
                btm = str(w1) + '_' + str(w2)
                try:
                    self.btm_freq[btm] += 1
                except:
                    self.btm_freq.update({btm:1})
                btm_info = biterm_info(w1, w2)
                self.btm_info.append(btm_info)


