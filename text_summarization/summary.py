# -*- encoding: utf-8 -*-
import unicodedata

__author__ = 'nobita'

from os import path
from biterm_model import biterm
from sklearn.metrics.pairwise import cosine_distances
import numpy as np
from nlp_tools import spliter
import utils
from duplicate_documents.minhash_lsh import duplicate_docs



class summary:
    def __init__(self, root_dir='.'):
        self.root_dir = root_dir
        self.DISTANCE_THRESHOLD = 0.35
        self.DISTANCE_THRESHOLD_2 = 0.5
        self.DISTANCE_THRESHOLD_3 = 0.75
        self.DISTANCE_THRESHOLD_4 = 0.9
        self.DOCUMENT_TOO_LONG = 50
        self.NUM_SENTENCES_SHORT = 8
        self.MINIMUM_LENGTH_SENTENCE = 8 # sentences in summary have to length greate than equal MINIMUM_LENGTH_SENTENCE
        self.skip_title = utils.load_data_to_list(path.join(root_dir, 'skip_title.txt'))
        self.skip_content = utils.load_data_to_list(path.join(root_dir, 'skip_content.txt'))


    def get_ratio(self, btm, length, level=u'medium'):
        if level == u'medium':
            if length < btm.NUM_SEN_SHORT_TEXT:
                ratio = 0.75
                # ratio = 0.525
            elif length > btm.NUM_SEN_LONG_TEXT:
                # ratio = 0.35
                ratio = 0.5
            else:
                # ratio = 0.45
                ratio = 0.6
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


    def is_skip(self, title, content):
        try:
            new_title = title.replace(u'_', u' ').lower()
            new_content = content.replace(u'_', u' ').lower()

            # check title has form: number + clause
            # example: 7 sao Hoa ngữ là mẹ kế, cha dượng
            words = new_title.split()[0]
            try:
                _ = int(words[0])
                return True
            except:
                # check title has form: top + number + clause
                # example: Top 5 dấu ấn CĐV ấn tượng nhất World Cup 2018 hiện tại
                if words[0] == u'top':
                    try:
                        _ = int(words[1])
                        return True
                    except: pass

            for skip in self.skip_title:
                if new_title.find(skip) != -1:
                    return True

            for skip in self.skip_content:
                if new_content.find(skip) != -1:
                    return True

            return False
        except:
            return True


    def get_default_summary(self, num_sens, des, body):
        new_des = des.replace(u'_', u' ')
        new_body = body.replace(u'_', u' ')
        if num_sens > self.NUM_SENTENCES_SHORT:
            return {u'short': new_des,
                    u'medium': new_des,
                    u'long': new_des}
        else:
            return {u'short': u'\n'.join([new_des, new_body]),
                    u'medium': u'\n'.join([new_des, new_body]),
                    u'long': u'\n'.join([new_des, new_body])}


    def run(self, title=u'', des=u'', body=u''):
        num_sens = len(spliter.split(u'\n'.join([des, body])))
        if self.is_skip(title, u'\n'.join([des, body])):
            print(u'Not summary doc: %s' % (title))
            if des != u'':
                return self.get_default_summary(num_sens, des, body)
            else:
                return {u'short' : u'Not support kind of this document',
                        u'medium' : u'Not support kind of this document',
                        u'long' : u'Not support kind of this document'}

        if des == u'':
            return {u'short': u'Not support kind of this document',
                    u'medium': u'Not support kind of this document',
                    u'long': u'Not support kind of this document'}
        elif body == u'':
            return self.get_default_summary(num_sens, des, body)

        data = des + u'\n' + body
        data = unicodedata.normalize('NFKC', data.strip())

        if len(data) == 0:
            return {u'short': u'Not support kind of this document',
                    u'medium': u'Not support kind of this document',
                    u'long': u'Not support kind of this document'}

        btm = biterm(num_iters=100, root_dir=self.root_dir)
        docs = btm.run_gibbs_sampling(data, save_result=False)

        if len(docs) == 0 or len(docs) > self.DOCUMENT_TOO_LONG:
            if des != u'':
                return self.get_default_summary(num_sens, des, body)
            else:
                return {u'short': u'Not support kind of this document',
                        u'medium': u'Not support kind of this document',
                        u'long': u'Not support kind of this document'}

        topic_docs = np.array([d.topic_proportion for d in docs])
        btm.theta = np.array([btm.theta])

        # cosine_distance = 1 - cosine_similarity
        cosine_dis = cosine_distances(topic_docs, btm.theta)
        cosine_dis = map(lambda x: x[0], cosine_dis)

        summary_result = {}
        for level in [u'short', u'medium', u'long']:
            ratio = self.get_ratio(btm, len(docs), level=level)

            for l in xrange(4):
                result = self.get_summary(cosine_dis, ratio, level=l+1)
                if len(result) > 0:
                    break

            if len(result) == 0:
                return self.get_default_summary(num_sens, des, body)

            self.insert_description(des, result, btm.MINIMUM_LENGTH_SENTENCE)

            summ = [docs[i].content for i in result if docs[i].length >= self.MINIMUM_LENGTH_SENTENCE]

            lsh = duplicate_docs()
            summ = lsh.run_ex(summ)
            lsh.clear()

            summ = u'\r\n'.join(summ).replace(u'_', u' ').\
                replace(u'\"', u'').replace(u'”', u'').replace(u'“', u'')

            summary_result.update({level : summ})

        return summary_result


    def get_summary(self, cosine_dis, ratio, level=1):
        if level == 1:
            distance = self.DISTANCE_THRESHOLD
        elif level == 2:
            distance = self.DISTANCE_THRESHOLD_2
        elif level == 3:
            distance = self.DISTANCE_THRESHOLD_3
        else:
            distance = self.DISTANCE_THRESHOLD_4
        bounary = int(round(len(cosine_dis) * ratio))
        docs_sorted = list(np.argsort(cosine_dis)[:bounary])
        result = filter(lambda i: cosine_dis[i] <= distance,
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


