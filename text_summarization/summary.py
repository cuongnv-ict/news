# -*- encoding: utf-8 -*-
import unicodedata

__author__ = 'nobita'


from biterm_model import biterm
from sklearn.metrics.pairwise import cosine_distances
import numpy as np
from nlp_tools import spliter



class summary:
    def __init__(self, root_dir='.'):
        self.root_dir = root_dir
        self.DISTANCE_THRESHOLD = 0.5


    def get_ratio(self, btm, length, level=u'medium'):
        if level == u'medium':
            if length < btm.NUM_SEN_SHORT_TEXT:
                ratio = 0.6
            elif length > btm.NUM_SEN_LONG_TEXT:
                ratio = 0.35
            else: ratio = 0.45
        elif level == u'short':
            if length < btm.NUM_SEN_SHORT_TEXT:
                ratio = 0.45
            elif length > btm.NUM_SEN_LONG_TEXT:
                ratio = 0.25
            else: ratio = 0.3
        else:
            if length < btm.NUM_SEN_SHORT_TEXT:
                ratio = 0.75
            elif length > btm.NUM_SEN_LONG_TEXT:
                ratio = 0.45
            else: ratio = 0.6
        return ratio


    def get_des_and_remove_tags(self, content):
        sentences = content.split(u'\n')
        if len(sentences) < 3:
            return None, None
        des = sentences[1]
        if u'[ tags ]' in sentences[len(sentences) - 1]:
            body = u'\n'.join(sentences[2:len(sentences) - 1])
        else: body = u'\n'.join(sentences[2:])
        return des, body


    def run(self, content=u''):
        des, body = self.get_des_and_remove_tags(content)
        if des == None or body == None:
            return {u'error' : u'story is too short'}
        data = des + u'\n' + body
        data = unicodedata.normalize('NFKC', data.strip())
        if len(data) == 0:
            return {u'error' : u'story is too short'}

        btm = biterm(num_iters=30, root_dir=self.root_dir)
        docs = btm.run_gibbs_sampling(data, save_result=False)
        if len(docs) == 0:
            return {u'error': u'story is too short'}
        topic_docs = np.array([d.topic_proportion for d in docs])
        btm.theta = np.array([btm.theta])

        cosine_dis = cosine_distances(topic_docs, btm.theta)
        cosine_dis = map(lambda x: x[0], cosine_dis)

        summary_result = {}
        for level in [u'short', u'medium', u'long']:
            ratio = self.get_ratio(btm, len(docs), level=level)
            result = self.get_summary(cosine_dis, ratio)
            self.insert_description(des, result, btm.MINIMUM_LENGTH_SENTENCE)
            summ = [docs[i].content for i in result]
            summ = u'\r\n'.join(summ).replace(u'_', u' ')
            summary_result.update({level : summ})
        return summary_result


    def get_summary(self, cosine_dis, ratio):
        bounary = int(len(cosine_dis) * ratio)
        docs_sorted = list(np.argsort(cosine_dis)[:bounary])
        result = filter(lambda i: cosine_dis[i] <= self.DISTANCE_THRESHOLD,
                        docs_sorted)
        if len(result) == 0:
            result = docs_sorted
        # cosine_dis.sort()
        # print zip(docs_sorted[:bounary], cosine_dis[:bounary])
        result.sort()
        return result


    def insert_description(self, des, l, minimum):
        d = {i:True for i in l}
        des = spliter.split(des)
        des = filter(lambda x: len(x.split()) >= minimum, des)
        des_len = len(des)
        for i in xrange(des_len):
            try:
                _ = d[i]
                continue
            except:
                l.insert(i, i)



if __name__ == '__main__':
    print 'Type input:'
    data = u''
    while True:
        try:
            x = unicode(raw_input(), encoding='utf-8')
        except: x = unicode(raw_input())
        if x.lower() == u'q' or x.lower() == 'quit':
            break
        data += x
    s = summary()
    s.run(data)


