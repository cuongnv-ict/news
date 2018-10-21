# -*- encoding: utf-8 -*-
__author__ = 'nobita'

from biterm_info import biterm_info
from nlp_tools import spliter
try:
    from pyvi.pyvi import ViPosTagger
except:
    from pyvi import ViPosTagger



class document:
    def __init__(self):
        self.length = 0
        self.word_freq = {}
        self.data = []
        self.btm_info = [] # list of biterm_info
        self.btm_freq = {}
        self.content = u''
        self.topic_proportion = None
        self.BTM_WINDOW_LENGTH = 0
        self.importance_pos = {'N':True, 'Np':True, 'Ny':True, 'V':True}


    def get_doc_info(self, doc, vocab):
        self.content = doc
        new_doc = self.remove_stop_postag(doc)
        words = new_doc.lower().split(u' ')
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


    def remove_stop_postag(self, content):
        content = map(lambda x: ViPosTagger.postagging(x),
                      spliter.split(content))
        clean_content = []
        for info in content:
            sen = []
            for i in xrange(len(info[0])):
                if self.is_exist(info[1][i]):
                    sen.append(info[0][i])
            clean_content.append(u' '.join(sen))
        return u'\n'.join(clean_content)


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


