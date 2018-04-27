# -*- encoding: utf-8 -*-

import os
from io import open
from document import document
from datasketch import MinHashLSH
import config, utils
from sklearn.externals import joblib
from threading import Thread
import schedule
import datetime, time
import unicodedata
from tokenizer.tokenizer import Tokenizer
import sys



class duplicate_docs:
    def __init__(self):
        self.docs_time = None
        self.docs = None
        self.lsh = None
        self.tokenizer = Tokenizer()


    def load(self, model):
        print('loading %s ...' % (model))
        if os.path.isfile(model):
            return joblib.load(model)
        else:
            return None


    def save(self, model, path):
        print('saving %s ...' % (path))
        joblib.dump(model, path)
        return


    def load_raw_data(self, dataset):
        stack = os.listdir(dataset)
        total_docs = 1; num_false_positive = 0; num_duplicate = 0
        print 'loading content in ' + dataset
        begin = time.time()
        while (len(stack) > 0):
            file_name = stack.pop()
            file_path = dataset + '/' + file_name
            if (os.path.isdir(file_path)):  # neu la thu muc thi day vao strong stack
                utils.push_data_to_stack(stack, file_path, file_name)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = unicodedata.normalize('NFKC', f.read().strip())
                    # data = self.tokenizer.predict(data)
                    data = self.tokenizer.predict(data)
                    doc = document(data)
                    did = self.insert(doc, check_duplication=True)
                    if did == 'False positive':
                        num_false_positive += 1
                    elif did == None:
                        num_duplicate += 1
                    print ('\r%d  --  %s' % (total_docs, did)),
                    sys.stdout.flush()
                    total_docs += 1
        end = time.time()
        print('')
        print('time = %s' % (str(datetime.timedelta(seconds=end-begin))))
        print('Total docs = %d' % (total_docs - 1))
        print('# Duplicate model predicted = %d' % (num_duplicate))
        print('# False positive = %d' % (num_false_positive))


    # insert a document object
    # output: key if document does not exist duplicate item
    # otherwise return alert duplication.
    def insert(self, doc, check_duplication=False):
        key = utils.id_generator()
        minhash = doc.get_minhash(doc.k_shingles,
                                  config.MINHASH_CONFIG['num_permutation'])
        if len(doc.k_shingles) == 0:
            return u'Does not insert this document to database.\nDocument\'s shingle = 0.\nDocument need to contain at least %d word' \
                   % (config.SHINGLE_CONFIG['k'])
        now = utils.get_date_now()
        if check_duplication:
            flag, key_duplicate = self.is_duplicate(doc.k_shingles, minhash)
            if not flag: # not duplicate
                if self.brute_force(doc):
                    return 'False positive'
                self.lsh.insert(key, minhash)
                self.docs.update({key : doc})
                try:
                    self.docs_time[now].append(key)
                except:
                    self.docs_time.update({now: [key]})
                return key
            else:
                utils.mkdir('duplicate')
                name = utils.id_generator()
                utils.mkdir('duplicate/' + name)
                with open('duplicate/' + name + '/0', 'w', encoding='utf-8') as f1, \
                        open('duplicate/' + name + '/1', 'w', encoding='utf-8') as f2:
                    f1.write(self.docs[key_duplicate].content.replace(u'_', u' '))
                    f2.write(doc.content.replace(u'_', u' '))
                return None
        else:
            self.lsh.insert(key, minhash)
            self.docs.update({key: doc})
            try:
                self.docs_time[now].append(key)
            except:
                self.docs_time.update({now: [key]})
            return key


    # check duplicate using brute force
    # return: True if duplication and otherwise return False
    def brute_force(self, doc):
        for d in self.docs.values():
            if self.get_actual_jaccard(doc.k_shingles, d.k_shingles) >= \
                    config.LSH_CONFIG['similarity_threshold']:
                utils.mkdir('false_positive')
                name = utils.id_generator()
                utils.mkdir('false_positive/' + name)
                with open('false_positive/' + name + '/0', 'w', encoding='utf-8') as f1, \
                    open('false_positive/' + name + '/1', 'w', encoding='utf-8') as f2:
                    f1.write(d.content.replace(u'_', u' '))
                    f2.write(doc.content.replace(u'_', u' '))
                return True
        return False


    # remove document by key
    def remove(self, key):
        try:
            del self.docs[key]
            self.lsh.remove(key)
            return u'Have deleted document has key is %s.' % (key)
        except Exception as e:
            # print e.message
            return u'The given key %s does not exist in database' % (key)

    # remove all docs
    def clear(self):
        docs_id = self.docs.keys()
        for id in docs_id:
            self.remove(id)
        times = self.docs_time.keys()
        for t in times:
            del self.docs_time[t]


    # check duplication
    # input: shingles and minhash of document
    def is_duplicate(self, shingles, minhash):
        result = self.lsh.query(minhash)
        if len(result) == 0:
            return False, None
        for key in result:
            jaccard = self.get_actual_jaccard(shingles, self.docs[key].k_shingles)
            if jaccard > config.LSH_CONFIG['similarity_threshold']:
                return True, key
        return False, None


    def get_actual_jaccard(self, shingles1, shingles2):
        union = float(len(shingles1.union(shingles2)))
        if union == 0.0:
            return 0.0
        intersection = float(len(shingles1.intersection(shingles2)))
        return intersection / union

    # remove docs is older than (x + 30) days
    def remove_old_docs_thread(self, days=7):
        print('create schedule do job at 00h00 every day ...')
        # print('days = %d' % (days))
        schedule.every().days.at('00:00').do(self.remove_old_doc, days)
        while True:
            schedule.run_pending()
            time.sleep(100)


    def remove_old_doc(self, days):
        for day in xrange(days + 30):
            previous_date = utils.get_previous_date(days)
            try:
                docs_id = self.docs_time[previous_date]
                for id in docs_id:
                    try:
                        self.remove(id)
                    except:
                        continue
                del self.docs_time[previous_date]
            except:
                continue


    def load_model(self):
        self.lsh = self.load('model/lsh.pkl')
        self.docs = self.load('model/docs.pkl')
        self.docs_time = self.load('model/docs_time.pkl')
        if self.lsh != None and self.docs != None and self.docs_time != None:
            return True
        return False


    def save_model(self):
        utils.mkdir('model')
        self.save(self.lsh, 'model/lsh.pkl')
        self.save(self.docs, 'model/docs.pkl')
        self.save(self.docs_time, 'model/docs_time.pkl')


    def run(self, dataset):
        if self.load_model():
            thread = Thread(target=self.remove_old_docs_thread, args=(config.TIME_TO_DELETE,))
            thread.start()
            return
        self.docs = {}
        self.docs_time = {}
        self.lsh = MinHashLSH(num_perm=config.LSH_CONFIG['num_permutation'],
                              params=(config.LSH_CONFIG['b'], config.LSH_CONFIG['r']),
                              storage_config=config.LSH_CONFIG['storage'],
                              prepickle=False)
        self.load_raw_data(dataset)
        # save model
        self.save_model()
        thread = Thread(target=self.remove_old_docs_thread, args=(config.TIME_TO_DELETE,))
        # thread.start()
        print('detect duplicate document service is running ...')


    def word_segment(self, data):
        return self.tokenizer.predict(data)




if __name__ == '__main__':
    dup = duplicate_docs()
    dup.run('dataset')
    dup.clear()
